"""Unified Transition Table Specification (E1 ~ E10, PRD §3.3)."""

from typing import Optional, Dict, Any, Tuple
from macao.core.types import AgentState


class TransitionTable:
    """Encapsulates the 10-state transition rules (PRD §3.3)."""

    @staticmethod
    def can_transition(from_state: AgentState, to_state: AgentState, trigger_id: str) -> bool:
        """Validates if a state transition is legal according to the unified transition table."""
        # Non-terminal active states
        active_states = {
            AgentState.IDLE, AgentState.CODING, AgentState.READY_FOR_REVIEW,
            AgentState.WAITING_REVIEW, AgentState.CONSENSUS_CHECK,
            AgentState.MERGING, AgentState.REWORK, AgentState.UNKNOWN
        }

        valid_transitions = {
            "E1": (AgentState.IDLE, AgentState.CODING),
            "E1_PRODUCED": (AgentState.CODING, AgentState.READY_FOR_REVIEW),
            "E2": (AgentState.READY_FOR_REVIEW, AgentState.WAITING_REVIEW),
            "E3": (AgentState.WAITING_REVIEW, AgentState.CONSENSUS_CHECK),
            "E4": (AgentState.CONSENSUS_CHECK, AgentState.MERGING),
            "E4a": (AgentState.MERGING, AgentState.DONE),
            "E4b": (AgentState.MERGING, AgentState.REWORK),
            "E5": (AgentState.CONSENSUS_CHECK, AgentState.REWORK),
            "E6": (AgentState.REWORK, AgentState.READY_FOR_REVIEW),
            "E7": (AgentState.CONSENSUS_CHECK, None), # Overrides can route to MERGING, REWORK, WAITING_REVIEW, CANCELLED
            "E8": (None, AgentState.UNKNOWN),         # From any active non-terminal state to UNKNOWN
            "E9": (AgentState.CONSENSUS_CHECK, AgentState.WAITING_REVIEW), # Retry review round
            "E10": (None, AgentState.CANCELLED),      # From any active non-terminal state to CANCELLED
        }

        rule = valid_transitions.get(trigger_id)
        if not rule:
            return False

        # Guard against transitions out of terminal states (DONE, CANCELLED)
        if from_state in (AgentState.DONE, AgentState.CANCELLED):
            return False

        # Check source
        if rule[0] is not None and rule[0] != from_state:
            return False

        # Check target
        if rule[1] is not None and rule[1] != to_state:
            return False

        # For wildcard sources (E8, E10), ensure from_state is an active state
        if rule[0] is None and from_state not in active_states:
            return False

        return True
