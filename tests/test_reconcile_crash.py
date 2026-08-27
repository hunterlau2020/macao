"""Unit tests for Crash Reconciliation (PRD §11.5)."""

import os
import unittest
import tempfile
from pathlib import Path
from macao.core.types import AgentState, Vote, OpinionStatus
from macao.storage.store import StateStore
from macao.storage.reconcile import StateReconciler
from macao.adapter.mock import MockAgentAdapter
from macao.consensus.vote import VoteAggregator


class TestCrashReconcile(unittest.TestCase):

    def test_reconcile_unconsumed_dev_manifest_after_crash(self):
        """Simulate Orchestrator crashing after Executor wrote .dev.yml before DB was updated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            store = StateStore(db_path)
            store.create_task("task-crash-1", "Crash Test", "feat", "main")
            store.update_task_state("task-crash-1", AgentState.CODING)

            # Physical disk has valid .dev.yml
            mock_exec = MockAgentAdapter("cc-ds4", "claude-code", role="executor")
            mock_exec.simulate_produce_dev_manifest(tmpdir, commit_sha="commit-recovered-01", review_round=1)

            reconciler = StateReconciler(store, project_root=tmpdir)
            reconciled_task = reconciler.reconcile()

            self.assertEqual(reconciled_task["state"], AgentState.READY_FOR_REVIEW.value)
            self.assertEqual(reconciled_task["checkpoint_ref"], "commit-recovered-01")

    def test_reconcile_vote_result_after_crash(self):
        """Simulate crash after vote_result.json was written but before DB state transition."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            store = StateStore(db_path)
            store.create_task("task-crash-2", "Crash Test 2", "feat", "main")
            store.update_task_state("task-crash-2", AgentState.CONSENSUS_CHECK, checkpoint_ref="c-rev-02", review_round=1)

            # Physical disk has vote_result.json with APPROVED (2 Reviewer approvals)
            agg = VoteAggregator(project_root=tmpdir)
            mock_rev1 = MockAgentAdapter("cc-glm", "codex", role="reviewer")
            mock_rev2 = MockAgentAdapter("kimi", "kimi", role="reviewer")
            mock_rev1.simulate_produce_review_manifest(
                tmpdir, checkpoint_ref="c-rev-02", review_round=1,
                vote=Vote.YES_APPROVE, opinion_status=OpinionStatus.APPROVED
            )
            mock_rev2.simulate_produce_review_manifest(
                tmpdir, checkpoint_ref="c-rev-02", review_round=1,
                vote=Vote.YES_APPROVE, opinion_status=OpinionStatus.APPROVED
            )

            collected = agg.collect_reviews("c-rev-02", 1)
            agg.generate_vote_result("c-rev-02", "cc-ds4", 1, 2, collected)

            reconciler = StateReconciler(store, project_root=tmpdir)
            reconciled_task = reconciler.reconcile()

            self.assertEqual(reconciled_task["state"], AgentState.MERGING.value)


if __name__ == "__main__":
    unittest.main()
