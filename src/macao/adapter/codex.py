"""Codex Adapter Implementation (PRD §12.3)."""

import shutil
import subprocess
from typing import Dict, Any, Optional

from macao.core.types import ExecutionMode, PreflightCheckResult
from macao.adapter.base import AgentAdapter, CapabilityManifest
from macao.adapter.pty_session import PTYSession


class CodexAdapter(AgentAdapter):
    """Adapter for Codex CLI (Executor / Reviewer)."""

    def __init__(self, agent_id: str = "codex", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, "codex", config)
        self.session: Optional[PTYSession] = None

    def capabilities(self) -> CapabilityManifest:
        return CapabilityManifest(
            can_execute=True,
            can_review=True,
            supports_hook=False,
            supports_noninteractive=True,
            supports_worktree=True,
            execution_mode=ExecutionMode.SANDBOXED,
            cli_version_range=">=2.0.0"
        )

    def preflight(self) -> PreflightCheckResult:
        exe = shutil.which("codex")
        if not exe:
            return PreflightCheckResult(
                cli_name=self.cli_name,
                installed=False,
                details="Codex CLI executable not found in PATH",
                remediation="Install or configure codex CLI."
            )
        return PreflightCheckResult(
            cli_name=self.cli_name,
            installed=True,
            version="2.1.0",
            execution_mode=self.capabilities().execution_mode,
            auth_valid=True,
            in_matrix=True,
            details=f"Found {exe}"
        )

    def start(self) -> bool:
        cmd = ["codex", "--quiet"]

        # Support model parameter specified by orchestrator
        model = self.config.get("model")
        if model:
            cmd.extend(["-m", str(model)])

        cwd = self.config.get("isolated_worktree_path", self.config.get("workspace_path", "."))
        self.session = PTYSession(cmd, cwd=cwd)
        self.is_running = self.session.start()
        return self.is_running

    def stop(self, reason: str = "normal") -> bool:
        if self.session:
            self.session.terminate()
            self.is_running = False
            return True
        return False

    def inject_task(self, task_payload: Dict[str, Any]) -> bool:
        if not self.session or not self.is_running:
            return False

        # If acting as Executor
        if self.config.get("role") == "executor" or "task_description" in task_payload:
            desc = task_payload.get("task_description", "")
            criteria = task_payload.get("success_criteria", {})
            prompt = (
                f"TASK: {desc}\n"
                f"Acceptance Criteria: {criteria}\n"
                "Implement the required changes, ensure tests pass, and create .macao/.dev.yml manifest."
            )
        else:
            # Acting as Reviewer
            ref = task_payload.get("checkpoint_ref", "")
            prompt = (
                f"REVIEW_REQUEST:\n"
                f"Review code in worktree {self.config.get('isolated_worktree_path')}.\n"
                f"Checkpoint ref: {ref}.\n"
                f"Write review manifest to .macao/.reviews/{self.agent_id}.review.yml."
            )

        return self.session.write_input(prompt)

    def ack(self, message_id: str) -> bool:
        return True

    def cancel(self, reason: str = "user_cancel") -> bool:
        return self.stop(reason)

    def get_logs(self, tail_lines: int = 300) -> str:
        return "\n".join(self.session.get_clean_logs(tail_lines)) if self.session else ""
