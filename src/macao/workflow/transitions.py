"""Unified Transition Table Specification (E1 ~ E10, PRD §3.3)."""

from typing import Optional, Dict, Any, Tuple
from macao.core.types import AgentState, StateChange


class TransitionTable:
    """Encapsulates the 10-state transition rules (PRD §3.3)."""

    @staticmethod
    def can_transition(from_state: AgentState, to_state: AgentState, trigger_id: str) -> bool:
        """Validates if a state transition is legal according to the unified transition table."""
        valid_transitions = {
            "E1": (AgentState.IDLE, AgentState.CODING),
            "E2": (AgentState.READY_FOR_REVIEW, AgentState.WAITING_REVIEW),
            "E3": (AgentState.WAITING_REVIEW, AgentState.CONSENSUS_CHECK),
            "E4": (AgentState.CONSENSUS_CHECK, AgentState.MERGING),
            "E4a": (AgentState.MERGING, AgentState.DONE),
            "E4b": (AgentState.MERGING, AgentState.REWORK),
            "E5": (AgentState.CONSENSUS_CHECK, AgentState.REWORK),
            "E6": (AgentState.REWORK, AgentState.READY_FOR_REVIEW),
            "E7": (AgentState.CONSENSUS_CHECK, None), # Can transition to MERGING (E4) or REWORK (E5) based on override
            "E8": (None, AgentState.UNKNOWN),         # From any active state to UNKNOWN on severe timeout
            "E9": (AgentState.CONSENSUS_CHECK, AgentState.WAITING_REVIEW), # Retry review round
            "E10": (None, AgentState.CANCELLED),      # From any active state to CANCELLED on task cancel
        }

        rule = valid_transitions.get(trigger_id)
        if not rule:
            return False

        src_match = (rule[0] is None or rule[0] == from_state)
        tgt_match = (rule[1] is None or rule[1] == to_state)
        return src_match and tgt_match
