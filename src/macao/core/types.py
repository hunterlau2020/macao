"""MACAO Core Types, Enumerations, and Data Models."""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import datetime


class AgentState(str, Enum):
    """10 FSM Business States (PRD §3.3)."""
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


class MessageType(str, Enum):
    """7 AEP Message Types (PRD §2.4)."""
    DEVELOPMENT_STARTED = "DEVELOPMENT_STARTED"
    REVIEW_REQUEST = "REVIEW_REQUEST"
    REVIEW_RESPONSE = "REVIEW_RESPONSE"
    REWORK_REQUEST = "REWORK_REQUEST"
    MERGE_COMPLETED = "MERGE_COMPLETED"
    STATE_CHANGED = "STATE_CHANGED"
    HUMAN_OVERRIDE_REQUEST = "HUMAN_OVERRIDE_REQUEST"


class Vote(str, Enum):
    """Reviewer Vote Enumeration (PRD §2.2)."""
    YES_APPROVE = "YES_APPROVE"
    NO_APPROVE = "NO_APPROVE"
    ABSTAIN = "ABSTAIN"


class OpinionStatus(str, Enum):
    """Reviewer Opinion Status (PRD §2.2)."""
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    REJECTED = "REJECTED"
    ABSTAIN = "ABSTAIN"


class Decision(str, Enum):
    """Consensus Decision Result (PRD §2.3)."""
    APPROVED = "APPROVED"
    REWORK_REQUIRED = "REWORK_REQUIRED"
    DEADLOCK = "DEADLOCK"


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
class StateChange:
    """Represents a state machine transition event."""
    from_state: AgentState
    to_state: AgentState
    source: str
    transition_id: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


@dataclass
class PreflightCheckResult:
    """Result of CLI preflight probe."""
    cli_name: str
    installed: bool
    version: Optional[str] = None
    auth_valid: bool = False
    in_matrix: bool = False
    details: str = ""
    remediation: Optional[str] = None
