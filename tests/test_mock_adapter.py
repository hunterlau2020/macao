"""Unit tests for MockAgentAdapter."""

import os
import unittest
import tempfile
from macao.adapter.mock import MockAgentAdapter
from macao.core.types import ExecutionMode, Vote, OpinionStatus
from macao.core.schema import validate_dev_manifest, validate_review_manifest


class TestMockAdapter(unittest.TestCase):

    def test_mock_capabilities(self):
        exec_adapter = MockAgentAdapter("cc-ds4", "claude-code", role="executor")
        caps_exec = exec_adapter.capabilities()
        self.assertTrue(caps_exec.can_execute)
        self.assertFalse(caps_exec.can_review)
        self.assertEqual(caps_exec.execution_mode, ExecutionMode.FULL)

        rev_adapter = MockAgentAdapter("cc-glm", "codex", role="reviewer")
        caps_rev = rev_adapter.capabilities()
        self.assertFalse(caps_rev.can_execute)
        self.assertTrue(caps_rev.can_review)
        self.assertEqual(caps_rev.execution_mode, ExecutionMode.SANDBOXED)

    def test_mock_simulate_dev_and_review_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exec_adapter = MockAgentAdapter("cc-ds4", "claude-code", role="executor")
            dev_file = exec_adapter.simulate_produce_dev_manifest(tmpdir, "c1a2b3c", review_round=1)
            self.assertTrue(os.path.exists(dev_file))

            rev_adapter = MockAgentAdapter("cc-glm", "codex", role="reviewer")
            rev_file = rev_adapter.simulate_produce_review_manifest(
                tmpdir,
                checkpoint_ref="c1a2b3c",
                review_round=1,
                vote=Vote.YES_APPROVE,
                opinion_status=OpinionStatus.APPROVED
            )
            self.assertTrue(os.path.exists(rev_file))


if __name__ == "__main__":
    unittest.main()
