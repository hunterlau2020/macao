"""Live Multi-Agent CLI Dispatcher and Review Extractor (Phase 3 / PRD §12.5 & §12.6)."""

import os
import re
import time
import shutil
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from macao.core.types import AgentState, OpinionStatus, Vote
from macao.core.schema import validate_review_manifest
from macao.adapter.base import AgentAdapter
from macao.adapter.claude import ClaudeCodeAdapter
from macao.adapter.codex import CodexAdapter
from macao.adapter.opencode import OpenCodeAdapter
from macao.adapter.antigravity import AntigravityAdapter
from macao.adapter.cursor import CursorAgentAdapter
from macao.adapter.kimi import KimiAdapter
from macao.adapter.mock import MockAgentAdapter
from macao.utils.git_utils import GitManager
from macao.utils.ansi import strip_ansi


CLI_ADAPTER_REGISTRY = {
    "claude-code": ClaudeCodeAdapter,
    "claude": ClaudeCodeAdapter,
    "codex": CodexAdapter,
    "opencode": OpenCodeAdapter,
    "agy": AntigravityAdapter,
    "antigravity": AntigravityAdapter,
    "agent": CursorAgentAdapter,
    "cursor": CursorAgentAdapter,
    "kimi": KimiAdapter,
    "mock-cli": MockAgentAdapter,
}


class ReviewExtractor:
    """Extracts, cleans, and validates review YAML from LLM CLI terminal output (PRD §12.5)."""

    YAML_BLOCK_PATTERN = re.compile(r"```(?:yaml|yml)?\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)

    @classmethod
    def extract_and_validate(cls, raw_terminal_output: str, agent_id: str, checkpoint_ref: str, review_round: int) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Level 1: Regex extraction and Draft-07 schema validation (Fail-closed).
        Returns (is_valid, parsed_dict, error_message).
        """
        clean_text = strip_ansi(raw_terminal_output)

        # 1. Try to find fenced code blocks first
        candidates = []
        matches = cls.YAML_BLOCK_PATTERN.findall(clean_text)
        for m in matches:
            candidates.append(m.strip())

        # 2. Also try whole text or YAML-like slice if no code block was used
        if not candidates:
            candidates.append(clean_text.strip())

        for cand in candidates:
            try:
                parsed = yaml.safe_load(cand)
                if not isinstance(parsed, dict) or not parsed:
                    continue

                opinion = parsed.get("opinion")
                top_vote = parsed.get("vote")

                # Fail-closed: Must contain explicit vote or opinion with status/vote
                if not isinstance(opinion, dict) and not top_vote:
                    continue

                if not isinstance(opinion, dict):
                    opinion = {}
                    parsed["opinion"] = opinion

                status = opinion.get("status")
                vote = top_vote or opinion.get("vote")

                if not status and not vote:
                    # Neither status nor vote is present: Reject (do not fabricate approval)
                    continue

                # Harmonize explicit status and vote
                if status == "APPROVED":
                    vote = "YES_APPROVE"
                elif status in ("CHANGES_REQUESTED", "REJECTED"):
                    vote = "NO_APPROVE"
                elif vote == "YES_APPROVE":
                    status = "APPROVED"
                elif vote in ("NO_APPROVE", "ABSTAIN"):
                    status = "CHANGES_REQUESTED"
                else:
                    # Unknown status/vote values
                    continue

                # Strict Context Binding: If YAML already contains metadata, it MUST match the dispatch context
                rev_info = parsed.get("reviewer")
                if isinstance(rev_info, dict) and rev_info.get("id") and rev_info.get("id") != agent_id:
                    continue
                if parsed.get("checkpoint_ref") and parsed.get("checkpoint_ref") != checkpoint_ref:
                    continue
                if parsed.get("review_round") is not None and parsed.get("review_round") != review_round:
                    continue

                # Bind validated context and schema requirements
                parsed["version"] = parsed.get("version") or "1.0"
                parsed["review_round"] = review_round
                parsed["checkpoint_ref"] = checkpoint_ref
                parsed["reviewer"] = {"id": agent_id, "cli": agent_id}
                parsed["vote"] = vote
                opinion["status"] = status
                opinion.setdefault("feedback", {"summary": "Review extracted from CLI session"})

                is_valid, err = validate_review_manifest(parsed)
                if is_valid:
                    return True, parsed, None

            except Exception:
                continue

        return False, None, "Failed to extract schema-valid YAML review manifest with explicit vote/status from terminal logs"


class LiveAgentDispatcher:
    """Manages real CLI PTY execution in isolated Git Worktrees."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.git = GitManager(str(self.project_root))
        self.active_sessions: Dict[str, Any] = {}

    def get_adapter_for_reviewer(self, reviewer_cfg: Dict[str, Any]) -> AgentAdapter:
        cli_type = reviewer_cfg.get("cli", "").lower()
        adapter_cls = CLI_ADAPTER_REGISTRY.get(cli_type)
        if not adapter_cls:
            raise ValueError(f"Unsupported or unconfigured reviewer CLI '{cli_type}'. Allowed: {list(CLI_ADAPTER_REGISTRY.keys())}")
        agent_id = reviewer_cfg.get("id", cli_type)
        return adapter_cls(agent_id=agent_id, config=reviewer_cfg)

    def dispatch_review_in_worktree(
        self,
        reviewer_cfg: Dict[str, Any],
        task_id: str,
        checkpoint_ref: str,
        review_round: int,
        diff_context: str = "",
        timeout_sec: float = 300.0
    ) -> Dict[str, Any]:
        """
        1. Creates isolated Git Worktree at .macao/worktrees/<agent_id>/<task_id>/r<round>
        2. Spawns real CLI session in isolated worktree
        3. Injects review prompt
        4. Extracts and validates .review.yml
        5. Atomically removes worktree
        """
        agent_id = reviewer_cfg.get("id", "reviewer")
        worktree_path = self.project_root / ".macao" / "worktrees" / agent_id / task_id / f"r{review_round}"

        adapter_cfg = dict(reviewer_cfg)
        adapter_cfg["isolated_worktree_path"] = str(worktree_path)
        adapter_cfg["role"] = "reviewer"
        adapter = self.get_adapter_for_reviewer(adapter_cfg)

        created_worktree = False
        start_time = time.time()

        try:
            # 1. Create worktree
            worktree_dir = self.git.create_isolated_worktree(agent_id, task_id, review_round, checkpoint_ref)
            created_worktree = True
            worktree_path = worktree_dir

            # 2. Prepare review prompt and payload
            payload = {
                "checkpoint_ref": checkpoint_ref,
                "review_round": review_round,
                "diff": diff_context,
                "review_context": {
                    "task_id": task_id,
                    "checkpoint_ref": checkpoint_ref,
                    "target_output": f".macao/.reviews/{agent_id}.review.yml"
                }
            }

            # 3. Start CLI in worktree
            started = adapter.start()
            if not started:
                return {
                    "agent_id": agent_id,
                    "status": "FAIL",
                    "error": f"Failed to start CLI adapter for {agent_id}"
                }

            # 4. Inject review instruction
            adapter.inject_task(payload)

            # 5. Monitor and wait for output or deadline
            deadline = time.time() + timeout_sec
            manifest_path = self.project_root / ".macao" / ".reviews" / f"{agent_id}.review.yml"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)

            while time.time() < deadline:
                # Check if CLI directly wrote file into worktree
                direct_file = worktree_path / ".macao" / ".reviews" / f"{agent_id}.review.yml"
                if direct_file.exists():
                    try:
                        content = yaml.safe_load(direct_file.read_text(encoding="utf-8"))
                        if isinstance(content, dict):
                            is_val, validated_doc, _ = ReviewExtractor.extract_and_validate(
                                yaml.safe_dump(content), agent_id, checkpoint_ref, review_round
                            )
                            if is_val and validated_doc:
                                manifest_path.write_text(yaml.safe_dump(validated_doc), encoding="utf-8")
                                return {
                                    "agent_id": agent_id,
                                    "status": "SUCCESS",
                                    "manifest_path": str(manifest_path),
                                    "vote": validated_doc["vote"],
                                    "duration": round(time.time() - start_time, 2)
                                }
                    except Exception:
                        pass

                # Try Level 1 extraction from terminal logs
                output_log = adapter.get_logs(300)
                is_valid, parsed_manifest, _ = ReviewExtractor.extract_and_validate(
                    output_log, agent_id, checkpoint_ref, review_round
                )
                if is_valid and parsed_manifest:
                    manifest_path.write_text(yaml.safe_dump(parsed_manifest), encoding="utf-8")
                    return {
                        "agent_id": agent_id,
                        "status": "SUCCESS",
                        "manifest_path": str(manifest_path),
                        "vote": parsed_manifest["vote"],
                        "duration": round(time.time() - start_time, 2)
                    }

                time.sleep(0.5)

            # Timed out
            return {
                "agent_id": agent_id,
                "status": "TIMEOUT",
                "vote": "ABSTAIN",
                "error": f"Reviewer {agent_id} timed out after {timeout_sec}s"
            }

        except Exception as e:
            return {
                "agent_id": agent_id,
                "status": "FAIL",
                "error": str(e)
            }
        finally:
            adapter.stop("dispatch_finished")
            if created_worktree:
                self.git.remove_isolated_worktree(agent_id, task_id, review_round)
