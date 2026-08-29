"""Kimi Adapter Implementation (PRD §12.3)."""

import shutil
from typing import Dict, Any, Optional

from macao.core.types import ExecutionMode, PreflightCheckResult
from macao.adapter.base import AgentAdapter, CapabilityManifest
from macao.adapter.pty_session import PTYSession


class KimiAdapter(AgentAdapter):
    """Adapter for Kimi Coding CLI (Reviewer)."""

    def __init__(self, agent_id: str = "kimi", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, "kimi", config)
        self.session: Optional[PTYSession] = None

    def capabilities(self) -> CapabilityManifest:
        return CapabilityManifest(
            can_execute=False,
            can_review=True,
            supports_hook=False,
            supports_noninteractive=True,
            supports_worktree=True,
            execution_mode=ExecutionMode.SANDBOXED,
            cli_version_range=">=1.0.0"
        )

    def preflight(self) -> PreflightCheckResult:
        exe = shutil.which("kimi") or shutil.which("kimi-code")
        if not exe:
            return PreflightCheckResult(
                cli_name=self.cli_name,
                installed=False,
                details="Kimi CLI executable not found in PATH",
                remediation="Install or configure kimi CLI."
            )
        return PreflightCheckResult(
            cli_name=self.cli_name,
            installed=True,
            version="1.0.0",
            execution_mode=self.capabilities().execution_mode,
            auth_valid=True,
            in_matrix=True,
            details=f"Found {exe}"
        )

    def start(self) -> bool:
        cmd = ["kimi", "--non-interactive"]
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
        prompt = f"REVIEW_REQUEST:\nPlease perform code review and write .macao/.reviews/{self.agent_id}.review.yml."
        return self.session.write_input(prompt)

    def ack(self, message_id: str) -> bool:
        return True

    def cancel(self, reason: str = "user_cancel") -> bool:
        return self.stop(reason)

    def get_logs(self, tail_lines: int = 300) -> str:
        return "\n".join(self.session.get_clean_logs(tail_lines)) if self.session else ""
