"""Unit tests for ConsensusEngine (PRD §2.3)."""

import unittest
from macao.core.types import Decision, Vote
from macao.consensus.engine import ConsensusEngine


class TestConsensusEngine(unittest.TestCase):

    def test_quorum_calculation(self):
        self.assertEqual(ConsensusEngine.calculate_minimum_quorum(2), 2)
        self.assertEqual(ConsensusEngine.calculate_minimum_quorum(3), 2)
        self.assertEqual(ConsensusEngine.calculate_minimum_quorum(4), 3)

    def test_2_reviewer_consensus(self):
        # 2 Approve -> APPROVED
        votes = [{"vote": "YES_APPROVE"}, {"vote": "YES_APPROVE"}]
        decision, breakdown, conf = ConsensusEngine.evaluate(votes, configured_reviewers=2)
        self.assertEqual(decision, Decision.APPROVED)
        self.assertEqual(breakdown["approve"], 2)

        # 2 Reject -> REWORK_REQUIRED
        votes = [{"vote": "NO_APPROVE"}, {"vote": "NO_APPROVE"}]
        decision, breakdown, conf = ConsensusEngine.evaluate(votes, configured_reviewers=2)
        self.assertEqual(decision, Decision.REWORK_REQUIRED)
        self.assertEqual(breakdown["reject"], 2)

        # 1 Approve + 1 Reject -> 1:1 DEADLOCK
        votes = [{"vote": "YES_APPROVE"}, {"vote": "NO_APPROVE"}]
        decision, breakdown, conf = ConsensusEngine.evaluate(votes, configured_reviewers=2)
        self.assertEqual(decision, Decision.DEADLOCK)

        # 1 Abstain + 1 Approve -> Effective 1 < Quorum 2 -> DEADLOCK
        votes = [{"vote": "ABSTAIN"}, {"vote": "YES_APPROVE"}]
        decision, breakdown, conf = ConsensusEngine.evaluate(votes, configured_reviewers=2)
        self.assertEqual(decision, Decision.DEADLOCK)


if __name__ == "__main__":
    unittest.main()
