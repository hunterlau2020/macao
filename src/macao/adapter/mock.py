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
        cli_name: str,
        role: str = "reviewer", # executor | reviewer
        config: Optional[Dict[str, Any]] = None,
        behavior_fn: Optional[Callable[["MockAgentAdapter", Dict[str, Any]], None]] = None
    ):
        super().__init__(agent_id, cli_name, config)
        self.role = role
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
            cli_name=self.cli_name,
            installed=True,
            version="1.0.0-mock",
            auth_valid=True,
            in_matrix=True,
            details=f"Mock {self.cli_name} adapter ready"
        )

    def start(self) -> bool:
        self.is_running = True
        self.logs.append(f"[Mock] {self.agent_id} started session.")
        return True

    def stop(self, reason: str = "normal") -> bool:
        self.is_running = False
        self.logs.append(f"[Mock] {self.agent_id} stopped: {reason}")
        return True

    def inject_task(self, task_payload: Dict[str, Any]) -> bool:
        self.injected_tasks.append(task_payload)
        self.logs.append(f"[Mock] {self.agent_id} received task: {task_payload.get('task_description', '')}")

        if self.behavior_fn:
            self.behavior_fn(self, task_payload)
        return True

    def ack(self, message_id: str) -> bool:
        self.logs.append(f"[Mock] {self.agent_id} acked message: {message_id}")
        return True

    def cancel(self, reason: str = "user_cancel") -> bool:
        return self.stop(reason)

    def get_logs(self, tail_lines: int = 300) -> str:
        return "\n".join(self.logs[-tail_lines:])

    # --- Simulation Helpers ---
    def simulate_produce_dev_manifest(
        self,
        project_root: str,
        commit_sha: str,
        review_round: int = 1,
        description: str = "Simulated development changes"
    ) -> Path:
        """Simulates Executor generating .macao/.dev.yml."""
        out_dir = Path(project_root) / ".macao"
        out_dir.mkdir(parents=True, exist_ok=True)
        dev_file = out_dir / ".dev.yml"

        data = {
            "version": "1.0",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "executor": {
                "id": self.agent_id,
                "role": "executor",
                "cli": self.cli_name
            },
            "development": {
                "description": description,
                "artifacts": [{"path": "src/module.py"}],
                "quality_metrics": {
                    "tests_passed": True,
                    "tests_exempt": False,
                    "coverage_delta": "+2.5%"
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
        vote: Vote = Vote.YES_APPROVE,
        opinion_status: OpinionStatus = OpinionStatus.APPROVED,
        issues: Optional[List[Dict[str, Any]]] = None
    ) -> Path:
        """Simulates Reviewer generating .macao/.reviews/<id>.review.yml."""
        out_dir = Path(project_root) / ".macao" / ".reviews"
        out_dir.mkdir(parents=True, exist_ok=True)
        rev_file = out_dir / f"{self.agent_id}.review.yml"

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
                "status": opinion_status.value,
                "confidence": 0.95,
                "summary": "Simulated review feedback",
                "feedback": {
                    "summary": "Review complete",
                    "categories": issues or []
                }
            },
            "vote": vote.value
        }
        is_valid, err = validate_review_manifest(data)
        if not is_valid:
            raise ValueError(f"Mock generated invalid review manifest: {err}")

        with open(rev_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, sort_keys=False)

        return rev_file
