"""Mock and Simulation Agent Adapter for Safe Automated Testing (No real CLI binaries required)."""

import os
import yaml
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable

from macao.core.types import ExecutionMode, PreflightCheckResult, Vote, OpinionStatus
from macao.adapter.base import AgentAdapter, CapabilityManifest
from macao.core.schema import validate_dev_manifest, validate_review_manifest


class MockAgentAdapter(AgentAdapter):
    """
    Simulated Agent Adapter used for automated test suites and Phase 0/1 development.
    Avoids executing real CLI binaries while fully adhering to Adapter Contract v1.
    """

    def __init__(
        self,
        agent_id: str,
        cli_name: str = "mock-cli",
        role: str = "reviewer", # executor | reviewer
        config: Optional[Dict[str, Any]] = None,
        behavior_fn: Optional[Callable[["MockAgentAdapter", Dict[str, Any]], None]] = None,
        project_root: Optional[str] = None
    ):
        super().__init__(agent_id, cli_name, config)
        self.role = role
        self.project_root = project_root

        self.behavior_fn = behavior_fn
        self.injected_tasks: List[Dict[str, Any]] = []
        self.logs: List[str] = []

    def capabilities(self) -> CapabilityManifest:
        is_exec = (self.role == "executor")
        return CapabilityManifest(
            can_execute=is_exec,
            can_review=not is_exec,
            supports_hook=True,
            supports_noninteractive=True,
            supports_worktree=not is_exec,
            execution_mode=ExecutionMode.FULL if is_exec else ExecutionMode.SANDBOXED,
            cli_version_range=">=1.0.0"
        )

    def preflight(self) -> PreflightCheckResult:
        return PreflightCheckResult(
            agent_id=self.agent_id,
            cli_name=self.cli_name,
            installed=True,
            version="1.0.0-mock",
            execution_mode=ExecutionMode.FULL if self.role == "executor" else ExecutionMode.SANDBOXED,
            auth_valid=True,
            in_matrix=True,
            details="Mock Adapter initialized for testing"
        )

    def start(self) -> bool:
        self.is_running = True
        return True

    def stop(self, reason: str = "normal") -> bool:
        self.is_running = False
        return True

    def inject_task(self, task_payload: Dict[str, Any]) -> bool:
        self.injected_tasks.append(task_payload)
        if self.behavior_fn:
            self.behavior_fn(self, task_payload)
        else:
            ref = task_payload.get("checkpoint_ref", "HEAD")
            rnd = task_payload.get("review_round", 1)
            cfg_dict = self.config or {}
            vote_val = cfg_dict.get("mock_vote", "YES_APPROVE")
            status_val = cfg_dict.get("mock_status", "APPROVED" if vote_val == "YES_APPROVE" else "CHANGES_REQUESTED")

            manifest_data = {
                "version": "1.0",
                "checkpoint_ref": ref,
                "review_round": rnd,
                "reviewer": {
                    "id": self.agent_id,
                    "cli": self.cli_name
                },
                "vote": vote_val,
                "opinion": {
                    "status": status_val,
                    "confidence": 0.95,
                    "feedback": {
                        "summary": "Mock reviewer validated code changes."
                    }
                }
            }
            manifest_yaml = yaml.safe_dump(manifest_data)
            self.logs.append(f"```yaml\n{manifest_yaml}\n```")

            wt_path = cfg_dict.get("isolated_worktree_path")
            if wt_path and Path(wt_path).exists():
                rev_dir = Path(wt_path) / ".macao" / ".reviews"
                rev_dir.mkdir(parents=True, exist_ok=True)
                (rev_dir / f"{self.agent_id}.review.yml").write_text(manifest_yaml, encoding="utf-8")

        return True


    def ack(self, message_id: str) -> bool:
        """AEP message acknowledgment."""
        return True

    def cancel(self, reason: str = "user_cancel") -> bool:
        return self.stop(reason)

    def get_logs(self, tail_lines: int = 300) -> str:
        if tail_lines > 0:
            return "\n".join(self.logs[-tail_lines:])
        return "\n".join(self.logs)

    def simulate_produce_dev_manifest(
        self,
        project_root: str,
        commit_sha: str,
        review_round: int = 1,
        tests_passed: bool = True
    ) -> Path:
        """Simulates Executor generating .macao/.dev.yml."""
        out_dir = Path(project_root) / ".macao"
        out_dir.mkdir(parents=True, exist_ok=True)
        dev_file = out_dir / ".dev.yml"

        data: Dict[str, Any] = {
            "version": "1.0",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "executor": {
                "id": self.agent_id,
                "role": "executor",
                "cli": self.cli_name
            },
            "development": {
                "description": "Simulated development output",
                "artifacts": [{"path": "src/main.py"}],
                "quality_metrics": {
                    "tests_passed": tests_passed
                },
                "git": {
                    "latest_commit": commit_sha
                }
            },
            "review_round": review_round,
            "status": "ready_for_review",
            "signal": "EXPLICIT"
        }
        is_valid, err = validate_dev_manifest(data)
        if not is_valid:
            raise ValueError(f"Mock generated invalid dev manifest: {err}")

        with open(dev_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, sort_keys=False)

        return dev_file

    def simulate_produce_review_manifest(
        self,
        project_root: str,
        checkpoint_ref: str,
        review_round: int = 1,
        vote: Any = Vote.YES_APPROVE,
        opinion_status: Any = OpinionStatus.APPROVED,
        issues: Optional[List[Dict[str, Any]]] = None,
        items: Optional[List[Dict[str, Any]]] = None,
        filename: Optional[str] = None,
        confidence: float = 0.95
    ) -> Path:
        """Simulates Reviewer generating .macao/.reviews/<id>.review.yml."""
        out_dir = Path(project_root) / ".macao" / ".reviews"
        out_dir.mkdir(parents=True, exist_ok=True)
        file_name = filename or f"{self.agent_id}.review.yml"
        rev_file = out_dir / file_name

        vote_val = vote.value if hasattr(vote, "value") else str(vote)
        status_val = opinion_status.value if hasattr(opinion_status, "value") else str(opinion_status)

        data: Dict[str, Any] = {
            "version": "1.0",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "reviewer": {
                "id": self.agent_id,
                "cli": self.cli_name
            },
            "checkpoint_ref": checkpoint_ref,
            "review_round": review_round,
            "opinion": {
                "status": status_val,
                "confidence": float(confidence),
                "summary": "Simulated review feedback",
                "feedback": {
                    "summary": "Review complete",
                    "categories": issues or []
                }
            },
            "vote": vote_val
        }
        converted_items = []
        if items is not None:
            converted_items = items
        elif issues:
            for idx, itm in enumerate(issues):
                if isinstance(itm, dict) and "issue_id" in itm:
                    converted_items.append(itm)
                elif isinstance(itm, dict):
                    converted_items.append({
                        "issue_id": f"{self.agent_id}/ISSUE-{idx+1}",
                        "disposition_class": "BLOCKING" if vote_val == "NO_APPROVE" else "ADVISORY",
                        "severity": itm.get("severity", "major"),
                        "title": itm.get("issue") or itm.get("description") or itm.get("summary") or "Simulated issue"
                    })
        elif vote_val == "NO_APPROVE":
            converted_items = [
                {
                    "issue_id": f"{self.agent_id}/ISSUE-01",
                    "disposition_class": "BLOCKING",
                    "severity": "major",
                    "title": "Simulated blocking issue"
                }
            ]

        if vote_val == "ABSTAIN":
            data["items"] = []
            data["abstain_reason"] = "Simulated abstain reason"
        else:
            data["items"] = converted_items

        is_valid, err = validate_review_manifest(data)
        if not is_valid:
            raise ValueError(f"Mock generated invalid review manifest: {err}")

        with open(rev_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, sort_keys=False)

        return rev_file
