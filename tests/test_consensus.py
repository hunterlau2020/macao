"""Unit tests for ConsensusEngine (PRD §2.3)."""

import unittest
from macao.consensus.engine import ConsensusEngine
from macao.core.types import Vote, Decision


class TestConsensusEngine(unittest.TestCase):

    def test_quorum_calculation(self):
        self.assertEqual(ConsensusEngine.calculate_minimum_quorum(2), 2)
        self.assertEqual(ConsensusEngine.calculate_minimum_quorum(3), 2)
        self.assertEqual(ConsensusEngine.calculate_minimum_quorum(4), 3)

    def test_2_reviewer_consensus(self):
        # 1. Full Approval
        votes_2_yes = [
            {"reviewer": "codex", "vote": Vote.YES_APPROVE},
            {"reviewer": "kimi", "vote": Vote.YES_APPROVE}
        ]
        d, _, _ = ConsensusEngine.evaluate(votes_2_yes, 2)
        self.assertEqual(d, Decision.APPROVED)

        # 2. Full Rejection
        votes_2_no = [
            {"reviewer": "codex", "vote": Vote.NO_APPROVE},
            {"reviewer": "kimi", "vote": Vote.NO_APPROVE}
        ]
        d, _, _ = ConsensusEngine.evaluate(votes_2_no, 2)
        self.assertEqual(d, Decision.REWORK_REQUIRED)

        # 3. 1:1 Deadlock
        votes_deadlock = [
            {"reviewer": "codex", "vote": Vote.YES_APPROVE},
            {"reviewer": "kimi", "vote": Vote.NO_APPROVE}
        ]
        d, _, _ = ConsensusEngine.evaluate(votes_deadlock, 2)
        self.assertEqual(d, Decision.DEADLOCK)

        # 4. 1 Vote + 1 Abstain -> Quorum Not Met -> Deadlock
        votes_abstain = [
            {"reviewer": "codex", "vote": Vote.YES_APPROVE},
            {"reviewer": "kimi", "vote": Vote.ABSTAIN}
        ]
        d, _, _ = ConsensusEngine.evaluate(votes_abstain, 2)
        self.assertEqual(d, Decision.DEADLOCK)

    def test_3_reviewer_consensus(self):
        # 1. 3/3 Approvals -> APPROVED
        votes_3_yes = [
            {"reviewer": "codex", "vote": Vote.YES_APPROVE},
            {"reviewer": "kimi", "vote": Vote.YES_APPROVE},
            {"reviewer": "gemini", "vote": Vote.YES_APPROVE}
        ]
        d, _, _ = ConsensusEngine.evaluate(votes_3_yes, 3)
        self.assertEqual(d, Decision.APPROVED)

        # 2. 2/3 Approvals + 1 Rejection -> 2/3 ratio met -> APPROVED
        votes_2_yes_1_no = [
            {"reviewer": "codex", "vote": Vote.YES_APPROVE},
            {"reviewer": "kimi", "vote": Vote.YES_APPROVE},
            {"reviewer": "gemini", "vote": Vote.NO_APPROVE}
        ]
        d, _, _ = ConsensusEngine.evaluate(votes_2_yes_1_no, 3)
        self.assertEqual(d, Decision.APPROVED)

        # 3. 1 Approval + 2 Rejections -> 2/3 reject ratio met -> REWORK_REQUIRED
        votes_1_yes_2_no = [
            {"reviewer": "codex", "vote": Vote.YES_APPROVE},
            {"reviewer": "kimi", "vote": Vote.NO_APPROVE},
            {"reviewer": "gemini", "vote": Vote.NO_APPROVE}
        ]
        d, _, _ = ConsensusEngine.evaluate(votes_1_yes_2_no, 3)
        self.assertEqual(d, Decision.REWORK_REQUIRED)

        # 4. 1 Approval + 1 Rejection + 1 Abstain -> 2 effective votes, 1:1 split -> DEADLOCK
        votes_split_abstain = [
            {"reviewer": "codex", "vote": Vote.YES_APPROVE},
            {"reviewer": "kimi", "vote": Vote.NO_APPROVE},
            {"reviewer": "gemini", "vote": Vote.ABSTAIN}
        ]
        d, _, _ = ConsensusEngine.evaluate(votes_split_abstain, 3)
        self.assertEqual(d, Decision.DEADLOCK)

    def test_weighted_counterexample_deadlock(self):
        """Codex P1-1: [YES w=2, NO w=1, NO w=1] in 3-seat system must result in DEADLOCK."""
        votes = [
            {"reviewer": "codex", "vote": Vote.YES_APPROVE, "weight": 2},
            {"reviewer": "kimi", "vote": Vote.NO_APPROVE, "weight": 1},
            {"reviewer": "gemini", "vote": Vote.NO_APPROVE, "weight": 1}
        ]
        decision, breakdown, _ = ConsensusEngine.evaluate(votes, configured_reviewers=3, configured_weight=4)
        self.assertEqual(decision, Decision.DEADLOCK)
        self.assertEqual(breakdown["approve_weight"], 2)
        self.assertEqual(breakdown["reject_weight"], 2)
        self.assertEqual(breakdown["effective_weight"], 4)

    def test_weighted_minimum_winning_seats_enforcement(self):
        """Even if weight reaches 2/3, single reviewer cannot win if minimum_winning_seats=2."""
        # 1 reviewer with weight 3 out of total weight 4 (hypothetical or configured)
        votes = [
            {"reviewer": "codex", "vote": Vote.YES_APPROVE, "weight": 3},
            {"reviewer": "kimi", "vote": Vote.NO_APPROVE, "weight": 1}
        ]
        # approve_weight = 3 >= 2/3 of 4 (3*3=9 >= 8), but approve_seats = 1 < minimum_winning_seats=2
        decision, _, _ = ConsensusEngine.evaluate(votes, configured_reviewers=2, configured_weight=4, policy={"minimum_winning_seats": 2, "seat_quorum_required": 2, "weight_quorum_required": 3})
        self.assertEqual(decision, Decision.DEADLOCK)


if __name__ == "__main__":
    unittest.main()
