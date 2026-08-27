"""Core Data Types, Enums, and Unified DTOs for MACAO (PRD v2.3.1)."""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


class AgentState(str, Enum):
    """10 FSM States defined in PRD §3.1."""
    IDLE = "IDLE"
    CODING = "CODING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    WAITING_REVIEW = "WAITING_REVIEW"
    CONSENSUS_CHECK = "CONSENSUS_CHECK"
    MERGING = "MERGING"
    DONE = "DONE"
    REWORK = "REWORK"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


class AEPType(str, Enum):
    """7 AEP/1.0 Message Types defined in PRD §2.4."""
    DEVELOPMENT_STARTED = "DEVELOPMENT_STARTED"
    REVIEW_REQUEST = "REVIEW_REQUEST"
    REVIEW_RESPONSE = "REVIEW_RESPONSE"
    REWORK_REQUEST = "REWORK_REQUEST"
    MERGE_COMPLETED = "MERGE_COMPLETED"
    STATE_CHANGED = "STATE_CHANGED"
    HUMAN_OVERRIDE_REQUEST = "HUMAN_OVERRIDE_REQUEST"


# Alias for backward compatibility
MessageType = AEPType


class Vote(str, Enum):
    """Reviewer Vote Enumeration (PRD §2.2, review_manifest.schema.json)."""
    YES_APPROVE = "YES_APPROVE"
    NO_APPROVE = "NO_APPROVE"
    ABSTAIN = "ABSTAIN"  # Used internally by Orchestrator upon timeout degradation


class OpinionStatus(str, Enum):
    """Reviewer Opinion Status (PRD §2.2, review_manifest.schema.json)."""
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    REJECTED = "REJECTED"


class Decision(str, Enum):
    """Consensus Decision Result (PRD §2.3, vote_result.schema.json)."""
    APPROVED = "APPROVED"
    REWORK_REQUIRED = "REWORK_REQUIRED"
    RETRY_REVIEW = "RETRY_REVIEW"
    CANCELLED = "CANCELLED"
    DEADLOCK = "DEADLOCK"  # Intermediate consensus state, never written to vote_result.json


class Resolution(str, Enum):
    """Decision Resolution Source."""
    AUTOMATIC = "automatic"
    HUMAN_OVERRIDE = "human_override"


class ExecutionMode(str, Enum):
    """Adapter Execution Permission Boundary (PRD §12.2)."""
    READ_ONLY = "read_only"
    SANDBOXED = "sandboxed"
    FULL = "full"


class OverrideChoice(str, Enum):
    """Human Override Choice Options (PRD §6.1 / §14.1)."""
    APPROVED = "APPROVED"
    REWORK = "REWORK"
    RETRY_REVIEW = "RETRY_REVIEW"
    CANCEL = "CANCEL"


@dataclass
class CapabilityManifest:
    """Capability Manifest of an Agent CLI Adapter (PRD §12.1 / §12.2)."""
    can_execute: bool = False
    can_review: bool = False
    supports_hook: bool = False
    supports_noninteractive: bool = False
    supports_worktree: bool = True
    execution_mode: ExecutionMode = ExecutionMode.SANDBOXED
    supported_os: List[str] = field(default_factory=lambda: ["linux", "darwin"])
    cli_version_range: str = ">=1.0.0"
    allowed_flags: List[str] = field(default_factory=list)


@dataclass
class PreflightCheckResult:
    """Result of agent preflight capability probe (PRD §12.2)."""
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
class AEPEnvelope:
    """AEP/1.0 Standard Message Envelope (PRD §2.4)."""
    message_id: str
    timestamp: int
    type: AEPType
    from_agent: str
    to_agent: str
    payload: Dict[str, Any]
    trace_id: Optional[str] = None
    reply_to: Optional[str] = None


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
