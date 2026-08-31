"""Cursor Agent CLI Adapter Implementation (PRD §12.3 / Agent Integration)."""

import shutil
import subprocess
from typing import Dict, Any, Optional

from macao.core.types import ExecutionMode, PreflightCheckResult, CapabilityManifest
from macao.adapter.base import AgentAdapter
from macao.adapter.pty_session import PTYSession


class CursorAgentAdapter(AgentAdapter):
    """Adapter for Cursor Agent CLI (agent / cursor) supporting both Executor and Reviewer."""

    def __init__(self, agent_id: str = "cursor", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, "cursor", config)
        self.session: Optional[PTYSession] = None

    def capabilities(self) -> CapabilityManifest:
        return CapabilityManifest(
            can_execute=True,
            can_review=True,
            supports_hook=False,
            supports_noninteractive=True,
            supports_worktree=True,
            execution_mode=ExecutionMode.SANDBOXED,
            cli_version_range=">=2025.0.0"
        )

    def preflight(self) -> PreflightCheckResult:
        exe = shutil.which("agent") or shutil.which("cursor")
        if not exe:
            return PreflightCheckResult(
                cli_name=self.cli_name,
                installed=False,
                execution_mode=self.capabilities().execution_mode,
                details="Cursor Agent CLI ('agent' or 'cursor') not found in PATH",
                remediation="Ensure Cursor Agent CLI (agent) is installed in PATH."
            )
        try:
            res = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=5)
            version = res.stdout.strip() or "2026.0.0"
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
                remediation="Ensure agent CLI is executable."
            )

    def start(self) -> bool:
        exe = shutil.which("agent") or shutil.which("cursor") or "agent"
        cmd = [exe, "--trust", "--sandbox", "enabled", "-p"]

        # Support model parameter specified by orchestrator
        model = self.config.get("model")
        if model:
            cmd.extend(["--model", str(model)])

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
            rnd = task_payload.get("review_round", 1)
            diff = task_payload.get("diff", "")
            diff_section = f"\nDiff Context:\n{diff}\n" if diff else ""
            prompt = (
                f"REVIEW_REQUEST:\n"
                f"Review code in worktree {self.config.get('isolated_worktree_path')}.\n"
                f"Checkpoint ref: {ref}, review round: {rnd}.\n"
                f"{diff_section}"
                f"Output valid YAML review manifest with vote ('YES_APPROVE' | 'NO_APPROVE' | 'ABSTAIN') "
                f"and write to .macao/.reviews/{self.agent_id}.review.yml."
            )


        return self.session.write_input(prompt)

    def ack(self, message_id: str) -> bool:
        return True

    def cancel(self, reason: str = "user_cancel") -> bool:
        return self.stop(reason)

    def get_logs(self, tail_lines: int = 300) -> str:
        return "\n".join(self.session.get_clean_logs(tail_lines)) if self.session else ""
