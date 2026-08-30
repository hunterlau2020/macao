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
    """Extracts, cleans, and self-heals review YAML from LLM CLI terminal output (PRD §12.5)."""

    YAML_BLOCK_PATTERN = re.compile(r"```(?:yaml|yml)?\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)

    @classmethod
    def extract_and_validate(cls, raw_terminal_output: str, agent_id: str, checkpoint_ref: str, review_round: int) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Level 1: Regex extraction and Draft-07 schema validation.
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
                if not isinstance(parsed, dict):
                    continue

                # Inject or enforce baseline identifiers if omitted by CLI
                parsed.setdefault("version", "1.0")
                parsed.setdefault("review_round", review_round)
                parsed.setdefault("checkpoint_ref", checkpoint_ref)
                if "reviewer" not in parsed:
                    parsed["reviewer"] = {"id": agent_id, "cli": agent_id}

                # Harmonize opinion status and vote if only one is present
                opinion = parsed.setdefault("opinion", {})
                status = opinion.get("status")
                vote = parsed.get("vote") or opinion.get("vote")

                if status == "APPROVED" and not vote:
                    vote = "YES_APPROVE"
                elif status in ("CHANGES_REQUESTED", "REJECTED") and not vote:
                    vote = "NO_APPROVE"
                elif vote == "YES_APPROVE" and not status:
                    status = "APPROVED"
                elif vote in ("NO_APPROVE", "ABSTAIN") and not status:
                    status = "CHANGES_REQUESTED"

                parsed["vote"] = vote or "YES_APPROVE"
                opinion["status"] = status or "APPROVED"

                is_valid, err = validate_review_manifest(parsed)
                if is_valid:
                    return True, parsed, None

            except Exception as e:
                continue

        return False, None, "Failed to extract schema-valid YAML review manifest from terminal logs"


class LiveAgentDispatcher:
    """Manages real CLI PTY execution in isolated Git Worktrees."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.git = GitManager(str(self.project_root))
        self.active_sessions: Dict[str, Any] = {}

    def get_adapter_for_reviewer(self, reviewer_cfg: Dict[str, Any]) -> AgentAdapter:
        cli_type = reviewer_cfg.get("cli", "opencode").lower()
        adapter_cls = CLI_ADAPTER_REGISTRY.get(cli_type, OpenCodeAdapter)
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
        1. Creates isolated Git Worktree at .macao/worktrees/<task_id>/<reviewer_id>
        2. Spawns real CLI session
        3. Injects review prompt
        4. Extracts and validates .review.yml
        5. Atomically removes worktree
        """
        agent_id = reviewer_cfg.get("id", "reviewer")
        worktree_path = self.project_root / ".macao" / "worktrees" / task_id / agent_id
        worktree_path.parent.mkdir(parents=True, exist_ok=True)

        adapter_cfg = dict(reviewer_cfg)
        adapter_cfg["isolated_worktree_path"] = str(worktree_path)
        adapter_cfg["role"] = "reviewer"
        adapter = self.get_adapter_for_reviewer(adapter_cfg)

        created_worktree = False
        start_time = time.time()

        try:
            # 1. Create worktree
            created_worktree = self.git.create_worktree(str(worktree_path), checkpoint_ref)
            if not created_worktree and not worktree_path.exists():
                return {
                    "agent_id": agent_id,
                    "status": "FAIL",
                    "error": f"Failed to create git worktree at {worktree_path}"
                }

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
            output_log = ""
            manifest_path = self.project_root / ".macao" / ".reviews" / f"{agent_id}.review.yml"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)

            while time.time() < deadline:
                output_log = adapter.get_logs(300)

                # Check if CLI directly wrote file into worktree
                direct_file = worktree_path / ".macao" / ".reviews" / f"{agent_id}.review.yml"
                if direct_file.exists():
                    try:
                        content = yaml.safe_load(direct_file.read_text(encoding="utf-8"))
                        is_val, _ = validate_review_manifest(content)
                        if is_val:
                            manifest_path.write_text(yaml.safe_dump(content), encoding="utf-8")
                            return {
                                "agent_id": agent_id,
                                "status": "SUCCESS",
                                "manifest_path": str(manifest_path),
                                "vote": content.get("opinion", {}).get("vote", "YES_APPROVE"),
                                "duration": round(time.time() - start_time, 2)
                            }
                    except Exception:
                        pass

                # Try Level 1 extraction from terminal logs
                is_valid, parsed_manifest, _ = ReviewExtractor.extract_and_validate(
                    output_log, agent_id, checkpoint_ref, review_round
                )
                if is_valid and parsed_manifest:
                    manifest_path.write_text(yaml.safe_dump(parsed_manifest), encoding="utf-8")
                    return {
                        "agent_id": agent_id,
                        "status": "SUCCESS",
                        "manifest_path": str(manifest_path),
                        "vote": parsed_manifest.get("opinion", {}).get("vote", "YES_APPROVE"),
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

        finally:
            adapter.stop("dispatch_finished")
            if created_worktree or worktree_path.exists():
                self.git.remove_worktree(str(worktree_path))
