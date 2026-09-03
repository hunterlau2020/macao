"""MACAO Consensus Engine: 2/3 Majority Voting Rule (PRD §2.3)."""

import math
from typing import List, Dict, Any, Tuple, Optional
from macao.core.types import Decision, Vote


class ConsensusEngine:
    """Calculates quorum and applies 2/3 majority arbitration logic."""

    @classmethod
    def calculate_minimum_quorum(cls, total_reviewers: int) -> int:
        """PRD §2.3 / §11.2: Minimum quorum = ceil(2 * N / 3), at least 2."""
        if total_reviewers <= 0:
            return 2
        return max(2, math.ceil(2 * total_reviewers / 3))

    @classmethod
    def evaluate(
        cls,
        votes: List[Dict[str, Any]],
        configured_reviewers: int = 2,
        configured_weight: Optional[int] = None,
        policy: Optional[Dict[str, Any]] = None
    ) -> Tuple[Decision, Dict[str, Any], float]:
        """
        Evaluates list of votes under PRD §2.3 weighted_2/3_v1 pure integer five gates:
            1. Dictator cap (configuration time)
            2. Seat quorum: E_N >= ceil(2N/3)
            3. Weight quorum: E_W >= ceil(2W/3)
            4. Winning weight threshold: 3*w >= 2*E_W (pure integer cross-multiplication)
            5. Minimum winning seats: winning_seats >= minimum_winning_seats (default 2)
        Returns:
            (Decision, vote_breakdown_dict, confidence_score)
        """
        approve_seats = 0
        approve_weight = 0
        reject_seats = 0
        reject_weight = 0
        abstain_seats = 0
        abstain_weight = 0

        for v in votes:
            vote_val = v.get("vote")
            w = int(v.get("weight", 1))
            if vote_val in (Vote.YES_APPROVE.value, "YES_APPROVE"):
                approve_seats += 1
                approve_weight += w
            elif vote_val in (Vote.NO_APPROVE.value, "NO_APPROVE"):
                reject_seats += 1
                reject_weight += w
            elif vote_val in (Vote.ABSTAIN.value, "ABSTAIN"):
                abstain_seats += 1
                abstain_weight += w

        effective_seats = approve_seats + reject_seats
        effective_weight = approve_weight + reject_weight

        total_weight = configured_weight if (configured_weight is not None and configured_weight > 0) else sum(v.get("weight", 1) for v in votes)
        if total_weight <= 0:
            total_weight = max(1, configured_reviewers)

        pol = policy or {}
        seat_quorum = pol.get("seat_quorum_required", math.ceil(2 * configured_reviewers / 3)) if configured_reviewers > 0 else 1
        weight_quorum = pol.get("weight_quorum_required", math.ceil(2 * total_weight / 3))
        min_winning_seats = pol.get("minimum_winning_seats", 2)

        breakdown = {
            "approve": approve_seats,
            "reject": reject_seats,
            "abstain": abstain_seats,
            "effective_votes": effective_seats,
            "effective_seats": effective_seats,
            "effective_weight": effective_weight,
            "approve_seats": approve_seats,
            "approve_weight": approve_weight,
            "reject_seats": reject_seats,
            "reject_weight": reject_weight,
            "abstain_seats": abstain_seats,
            "abstain_weight": abstain_weight,
            "effective_rate": round(effective_seats / configured_reviewers, 2) if configured_reviewers > 0 else 1.0,
            "yes_approve": approve_seats,
            "no_approve": reject_seats
        }

        # Gate 2: Seat quorum: E_N >= seat_quorum_required
        if effective_seats < seat_quorum:
            return Decision.DEADLOCK, breakdown, 0.5

        # Gate 3: Weight quorum: E_W >= weight_quorum_required
        if effective_weight < weight_quorum:
            return Decision.DEADLOCK, breakdown, 0.5

        # Gate 4 & 5 for APPROVE: 3 * approve_weight >= 2 * effective_weight AND approve_seats >= min_winning_seats
        if (3 * approve_weight >= 2 * effective_weight) and (approve_seats >= min_winning_seats):
            conf = approve_weight / effective_weight if effective_weight > 0 else 1.0
            return Decision.APPROVED, breakdown, round(conf, 2)

        # Gate 4 & 5 for REWORK: 3 * reject_weight >= 2 * effective_weight AND reject_seats >= min_winning_seats
        if (3 * reject_weight >= 2 * effective_weight) and (reject_seats >= min_winning_seats):
            conf = reject_weight / effective_weight if effective_weight > 0 else 1.0
            return Decision.REWORK_REQUIRED, breakdown, round(conf, 2)

        # Otherwise: DEADLOCK (neither side satisfies both gates)
        return Decision.DEADLOCK, breakdown, 0.5
