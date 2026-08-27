"""Unit and E2E tests for Phase 2 Micro-Task Collaboration Lifecycle (PRD §14)."""

import os
import unittest
from macao.workflow.e2e_runner import ControlledE2ERunner


class TestControlledE2EPhase2(unittest.TestCase):

    def test_e2e_micro_task_collaboration_cycle(self):
        """Verify the complete Phase 2 end-to-end cycle from start to fast-forward merge and DONE."""
        runner = ControlledE2ERunner()
        try:
            res = runner.run_e2e_cycle()
            self.assertEqual(res["status"], "PASS")
            self.assertEqual(res["final_state"], "DONE")
            self.assertEqual(res["decision"], "APPROVED")
            self.assertTrue(res["merge_exact_match"])
            self.assertEqual(len(res["steps"]), 5)
        finally:
            runner.cleanup()


if __name__ == "__main__":
    unittest.main()
