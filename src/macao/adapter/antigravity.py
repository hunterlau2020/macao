"""Google Antigravity (AGY) Adapter Implementation (PRD §12.3)."""

import shutil
import subprocess
from typing import Dict, Any, Optional

from macao.core.types import ExecutionMode, PreflightCheckResult, CapabilityManifest
from macao.adapter.base import AgentAdapter
from macao.adapter.pty_session import PTYSession


class AntigravityAdapter(AgentAdapter):
    """Adapter for Google Antigravity CLI (agy / antigravity)."""

    def __init__(self, agent_id: str = "antigravity", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, "agy", config)
        self.session: Optional[PTYSession] = None

    def capabilities(self) -> CapabilityManifest:
        return CapabilityManifest(
            can_execute=True,
            can_review=True,
            supports_hook=True,
            supports_noninteractive=True,
            supports_worktree=True,
            execution_mode=ExecutionMode.SANDBOXED,
            cli_version_range=">=1.0.0"
        )

    def preflight(self) -> PreflightCheckResult:
        exe = shutil.which("agy") or shutil.which("antigravity")
        if not exe:
            return PreflightCheckResult(
                cli_name=self.cli_name,
                installed=False,
                execution_mode=self.capabilities().execution_mode,
                details="Google Antigravity CLI (agy) not found in PATH",
                remediation="Ensure Google Antigravity CLI (agy) is installed and available in PATH."
            )
        try:
            res = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=5)
            version = res.stdout.strip() or "1.0.0"
            return PreflightCheckResult(
                cli_name=self.cli_name,
                installed=True,
                version=version,
                execution_mode=self.capabilities().execution_mode,
                auth_valid=True,
                in_matrix=True,
                details=f"Found {exe} ({version})"
            )
        except Exception as e:
            return PreflightCheckResult(
                cli_name=self.cli_name,
                installed=True,
                execution_mode=self.capabilities().execution_mode,
                details=f"Version probe error: {e}",
                remediation="Ensure agy is executable."
            )

    def start(self) -> bool:
        cmd = ["agy", "--quiet"]
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
        prompt = (
            f"Review code in worktree {self.config.get('isolated_worktree_path')}. "
            f"Checkpoint ref: {task_payload.get('checkpoint_ref')}. "
            "Write review manifest to .macao/.reviews/antigravity.review.yml."
        )
        return self.session.write_input(prompt)

    def ack(self, message_id: str) -> bool:
        return True
