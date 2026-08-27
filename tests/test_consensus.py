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


if __name__ == "__main__":
    unittest.main()
