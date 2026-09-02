"""Core Data Types and Enumerations for MACAO (PRD §2, §3, §4)."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


class AgentState(str, Enum):
    """10-State Finite State Machine (PRD §3.1, §3.3)."""
    IDLE = "IDLE"
    CODING = "CODING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    WAITING_REVIEW = "WAITING_REVIEW"
    CONSENSUS_CHECK = "CONSENSUS_CHECK"
    REWORK = "REWORK"
    MERGING = "MERGING"
    DONE = "DONE"
    UNKNOWN = "UNKNOWN"
    CANCELLED = "CANCELLED"


class AEPType(str, Enum):
    """AEP/1.1 Standard Message Types (PRD §2.4, Schema Draft-07)."""
    DEVELOPMENT_STARTED = "DEVELOPMENT_STARTED"
    REVIEW_REQUEST = "REVIEW_REQUEST"
    REVIEW_RESPONSE = "REVIEW_RESPONSE"
    REWORK_REQUEST = "REWORK_REQUEST"
    DISPOSITION_REQUIRED = "DISPOSITION_REQUIRED"
    MERGE_COMPLETED = "MERGE_COMPLETED"
    STATE_CHANGED = "STATE_CHANGED"
    HUMAN_OVERRIDE_REQUEST = "HUMAN_OVERRIDE_REQUEST"


class Vote(str, Enum):
    """Three-value voting outcomes (PRD §2.3)."""
    YES_APPROVE = "YES_APPROVE"
    NO_APPROVE = "NO_APPROVE"
    ABSTAIN = "ABSTAIN"


class OpinionStatus(str, Enum):
    """Reviewer opinion status in .review.yml (Draft-07 Schema)."""
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    REJECTED = "REJECTED"
    ABSTAINED = "ABSTAINED"



class Decision(str, Enum):
    """Four-value final consensus decisions (PRD §2.3, §3.2 Layer 1c)."""
    APPROVED = "APPROVED"
    REWORK_REQUIRED = "REWORK_REQUIRED"
    RETRY_REVIEW = "RETRY_REVIEW"
    CANCELLED = "CANCELLED"
    # Intermediate / non-terminal states
    DEADLOCK = "DEADLOCK"


class Resolution(str, Enum):
    AUTOMATIC = "automatic"
    HUMAN_OVERRIDE = "human_override"


class OverrideChoice(str, Enum):
    """Valid choices for human override (PRD §3.3 E7, §15.2)."""
    APPROVED = "APPROVED"
    REWORK = "REWORK"
    RETRY_REVIEW = "RETRY_REVIEW"
    CANCEL = "CANCEL"


class ExecutionMode(str, Enum):
    FULL = "full"
    SANDBOXED = "sandboxed"  # Worktree and working directory isolation (Process-isolated; Container namespaces planned for Phase 3)


@dataclass
class CapabilityManifest:
    """Agent CLI runtime capability and isolation declaration."""
    can_execute: bool = False
    can_review: bool = True
    supports_hook: bool = False
    supports_noninteractive: bool = True
    supports_worktree: bool = True
    execution_mode: ExecutionMode = ExecutionMode.SANDBOXED
    cli_version_range: str = ">=1.0.0"
    supports_interactive: bool = True
    supports_json_output: bool = False
    supported_models: List[str] = field(default_factory=list)


@dataclass
class PreflightCheckResult:
    """Result of agent/tool CLI preflight probe (PRD §12.2)."""
    agent_id: str = ""
    cli_name: str = ""
    installed: bool = False
    version: Optional[str] = None
    execution_mode: Optional[ExecutionMode] = None
    auth_valid: bool = True
    in_matrix: bool = True
    details: Optional[str] = None
    remediation: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if not self.cli_name and self.agent_id:
            self.cli_name = self.agent_id
        if not self.agent_id and self.cli_name:
            self.agent_id = self.cli_name

    @property
    def is_ok(self) -> bool:
        return self.installed and self.auth_valid and (self.error is None)


@dataclass
class StateChange:
    """FSM State Transition Result."""
    task_id: str
    from_state: AgentState
    to_state: AgentState
    trigger: str
    review_round: int
    checkpoint_ref: Optional[str] = None
    note: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)
