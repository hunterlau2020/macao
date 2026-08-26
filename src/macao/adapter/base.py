"""MACAO Agent Adapter Contract v1 (PRD §12.1)."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field

from macao.core.types import ExecutionMode, PreflightCheckResult


@dataclass
class CapabilityManifest:
    """Capability Manifest of an Agent CLI Adapter (PRD §12.2)."""
    can_execute: bool
    can_review: bool
    supports_hook: bool
    supports_noninteractive: bool
    supports_worktree: bool
    execution_mode: ExecutionMode
    supported_os: List[str] = field(default_factory=lambda: ["linux", "darwin"])
    cli_version_range: str = ">=1.0.0"


class AgentAdapter(ABC):
    """Abstract contract for CLI Agent Adapters."""

    def __init__(self, agent_id: str, cli_name: str, config: Optional[Dict[str, Any]] = None):
        self.agent_id = agent_id
        self.cli_name = cli_name
        self.config = config or {}
        self.is_running: bool = False

    @abstractmethod
    def capabilities(self) -> CapabilityManifest:
        """Reports adapter capabilities."""
        pass

    @abstractmethod
    def preflight(self) -> PreflightCheckResult:
        """Probes installation, auth, version matrix, and returns remediation suggestions."""
        pass

    @abstractmethod
    def start(self) -> bool:
        """Spawns CLI session in PTY / background."""
        pass

    @abstractmethod
    def stop(self, reason: str = "normal") -> bool:
        """Terminates CLI session and recycles child processes."""
        pass

    @abstractmethod
    def inject_task(self, task_payload: Dict[str, Any]) -> bool:
        """Injects development or review instruction into the agent."""
        pass

    @abstractmethod
    def ack(self, message_id: str) -> bool:
        """Idempotent ACK for received message."""
        pass

    @abstractmethod
    def cancel(self, reason: str = "user_cancel") -> bool:
        """Cancels current task and terminates process tree."""
        pass

    @abstractmethod
    def get_logs(self, tail_lines: int = 300) -> str:
        """Returns cleaned ANSI-stripped terminal logs."""
        pass
