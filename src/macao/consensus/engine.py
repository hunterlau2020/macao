"""Consensus Engine: 2/3 Majority + Minimum Quorum Decision Logic (PRD §2.3)."""

import math
from typing import List, Dict, Any, Tuple
from macao.core.types import Vote, Decision, Resolution


class ConsensusEngine:
    """Calculates consensus decisions based on collected Reviewer votes."""

    @staticmethod
    def calculate_minimum_quorum(configured_reviewers: int) -> int:
        """minimum_quorum = ceil(2 * configured_reviewers / 3)."""
        return math.ceil(2 * configured_reviewers / 3)

    @classmethod
    def evaluate(
        cls,
        votes: List[Dict[str, Any]],
        configured_reviewers: int = 2
    ) -> Tuple[Decision, Dict[str, int], float]:
        """
        Evaluates votes against the 2/3 consensus rules.

        Returns:
            (Decision, vote_breakdown, confidence)
        """
        approve_count = 0
        reject_count = 0
        abstain_count = 0

        for v in votes:
            vote_val = v.get("vote")
            if vote_val == Vote.YES_APPROVE.value or vote_val == "YES_APPROVE":
                approve_count += 1
            elif vote_val == Vote.NO_APPROVE.value or vote_val == "NO_APPROVE":
                reject_count += 1
            elif vote_val == Vote.ABSTAIN.value or vote_val == "ABSTAIN":
                abstain_count += 1

        effective_votes = approve_count + reject_count
        quorum = cls.calculate_minimum_quorum(configured_reviewers)
        breakdown = {
            "approve": approve_count,
            "reject": reject_count,
            "abstain": abstain_count
        }

        # Rule 1: Effective votes must be >= minimum quorum
        if effective_votes < quorum:
            return Decision.DEADLOCK, breakdown, 0.5

        # Rule 2: Approve ratio >= 2/3 -> APPROVED
        if approve_count / effective_votes >= (2.0 / 3.0 - 1e-6):
            conf = approve_count / effective_votes
            return Decision.APPROVED, breakdown, round(conf, 2)

        # Rule 3: Reject ratio >= 2/3 -> REWORK_REQUIRED
        if reject_count / effective_votes >= (2.0 / 3.0 - 1e-6):
            conf = reject_count / effective_votes
            return Decision.REWORK_REQUIRED, breakdown, round(conf, 2)

        # Rule 4: Neither reached 2/3 (e.g. 1:1 or 1:1:1) -> DEADLOCK
        return Decision.DEADLOCK, breakdown, 0.5
