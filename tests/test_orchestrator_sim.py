"""End-to-End Multi-Agent Simulation Tests (PRD §3.4 Scenarios S1 ~ S6)."""

import os
import unittest
import tempfile
from pathlib import Path

from macao.core.types import AgentState, Vote, OpinionStatus, OverrideChoice
from macao.adapter.mock import MockAgentAdapter
from macao.workflow.orchestrator import Orchestrator


class TestOrchestratorSimulation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "state.db")

        # Set up mock executor and reviewers
        self.mock_executor = MockAgentAdapter("cc-ds4", "claude-code", role="executor")
        self.mock_reviewer1 = MockAgentAdapter("cc-glm", "codex", role="reviewer")
        self.mock_reviewer2 = MockAgentAdapter("kimi", "kimi", role="reviewer")

        self.orchestrator = Orchestrator(
            project_root=self.tmpdir,
            db_path=self.db_path,
            executor_adapter=self.mock_executor,
            reviewer_adapters=[self.mock_reviewer1, self.mock_reviewer2]
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_scenario_s1_happy_path(self):
        """Scenario S1: Task Start -> Coding -> 2x Approvals -> MERGING."""
        # 1. Start Task (E1: IDLE -> CODING)
        task = self.orchestrator.start_task(
            title="Implement OAuth2 Authentication",
            task_description="Add JWT token validation endpoint",
            acceptance_criteria={"tests_passed": True, "coverage": 90.0},
            source_branch="feature/oauth",
            target_branch="main",
            task_id="task-s1"
        )
        self.assertEqual(task["state"], AgentState.CODING.value)

        # 2. Executor completes work and produces .dev.yml
        self.mock_executor.simulate_produce_dev_manifest(self.tmpdir, commit_sha="commit-oauth-001", review_round=1)

        # 3. Orchestrator detects checkpoint (CODING -> READY_FOR_REVIEW)
        change_dev = self.orchestrator.check_development_checkpoint("task-s1")
        self.assertIsNotNone(change_dev)
        self.assertEqual(change_dev.to_state, AgentState.READY_FOR_REVIEW)

        # 4. Dispatch Reviews (E2: READY_FOR_REVIEW -> WAITING_REVIEW)
        change_dispatch = self.orchestrator.dispatch_review_requests("task-s1")
        self.assertEqual(change_dispatch.to_state, AgentState.WAITING_REVIEW)

        # Verify .dev.yml was archived
        archived_dev = Path(self.tmpdir) / ".macao" / "archive" / "commit-oauth-001" / "r1" / ".dev.yml"
        self.assertTrue(archived_dev.exists())

        # 5. Reviewers produce approvals (.review.yml)
        self.mock_reviewer1.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref="commit-oauth-001", review_round=1,
            vote=Vote.YES_APPROVE, opinion_status=OpinionStatus.APPROVED
        )
        self.mock_reviewer2.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref="commit-oauth-001", review_round=1,
            vote=Vote.YES_APPROVE, opinion_status=OpinionStatus.APPROVED
        )

        # 6. Evaluate consensus (E3: WAITING_REVIEW -> CONSENSUS_CHECK -> E4: MERGING)
        change_final, vote_data = self.orchestrator.collect_and_evaluate_consensus("task-s1", configured_reviewers=2)
        self.assertIsNotNone(change_final)
        self.assertEqual(change_final.to_state, AgentState.MERGING)
        self.assertEqual(vote_data["decision"], "APPROVED")

    def test_scenario_s2_rework_loop(self):
        """Scenario S2: Reviews Reject -> Rework Round 2 -> Approvals -> MERGING."""
        # 1. Start Task
        self.orchestrator.start_task(
            title="Refactor Cache",
            task_description="Memory LRU cache",
            acceptance_criteria={"tests_passed": True},
            task_id="task-s2"
        )
        # 2. Round 1 dev manifest
        self.mock_executor.simulate_produce_dev_manifest(self.tmpdir, commit_sha="c-r1", review_round=1)
        self.orchestrator.check_development_checkpoint("task-s2")
        self.orchestrator.dispatch_review_requests("task-s2")

        # 3. Round 1 Reviewers REJECT
        self.mock_reviewer1.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref="c-r1", review_round=1,
            vote=Vote.NO_APPROVE, opinion_status=OpinionStatus.REJECTED,
            issues=[{"type": "concurrency", "severity": "critical", "issue": "Missing lock"}]
        )
        self.mock_reviewer2.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref="c-r1", review_round=1,
            vote=Vote.NO_APPROVE, opinion_status=OpinionStatus.REJECTED,
            issues=[{"type": "resource", "severity": "major", "issue": "File descriptor leak"}]
        )

        # 4. Evaluate consensus -> REWORK (E5)
        change_r1, vote_data = self.orchestrator.collect_and_evaluate_consensus("task-s2", configured_reviewers=2)
        self.assertEqual(change_r1.to_state, AgentState.REWORK)
        self.assertEqual(vote_data["decision"], "REWORK_REQUIRED")
        
        # Verify task is in REWORK with round=2
        task_r2 = self.orchestrator.store.get_task("task-s2")
        self.assertEqual(task_r2["review_round"], 2)

        # 5. Executor fixes issues and produces Round 2 dev manifest (c-r2)
        self.mock_executor.simulate_produce_dev_manifest(self.tmpdir, commit_sha="c-r2", review_round=2)
        self.orchestrator.check_development_checkpoint("task-s2")
        self.orchestrator.dispatch_review_requests("task-s2")

        # 6. Round 2 Reviewers APPROVE
        self.mock_reviewer1.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref="c-r2", review_round=2,
            vote=Vote.YES_APPROVE, opinion_status=OpinionStatus.APPROVED
        )
        self.mock_reviewer2.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref="c-r2", review_round=2,
            vote=Vote.YES_APPROVE, opinion_status=OpinionStatus.APPROVED
        )

        # 7. Evaluate consensus -> MERGING (E4)
        change_r2, vote_data_r2 = self.orchestrator.collect_and_evaluate_consensus("task-s2", configured_reviewers=2)
        self.assertEqual(change_r2.to_state, AgentState.MERGING)
        self.assertEqual(vote_data_r2["decision"], "APPROVED")

    def test_scenario_s3_deadlock_and_override_approved(self):
        """Scenario S3: 1 Approve + 1 Reject -> Deadlock -> Human Override APPROVED -> MERGING."""
        self.orchestrator.start_task(
            title="Update dependencies",
            task_description="Upgrade PyYAML",
            acceptance_criteria={"tests_passed": True},
            task_id="task-s3"
        )
        self.mock_executor.simulate_produce_dev_manifest(self.tmpdir, commit_sha="c-s3", review_round=1)
        self.orchestrator.check_development_checkpoint("task-s3")
        self.orchestrator.dispatch_review_requests("task-s3")

        # 1 Approve + 1 Reject
        self.mock_reviewer1.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref="c-s3", review_round=1,
            vote=Vote.YES_APPROVE, opinion_status=OpinionStatus.APPROVED
        )
        self.mock_reviewer2.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref="c-s3", review_round=1,
            vote=Vote.NO_APPROVE, opinion_status=OpinionStatus.REJECTED
        )

        # Evaluate consensus -> Returns Deadlock (None change, remains in CONSENSUS_CHECK)
        change_deadlock, vote_data = self.orchestrator.collect_and_evaluate_consensus("task-s3", configured_reviewers=2)
        self.assertIsNone(change_deadlock)
        self.assertEqual(self.orchestrator.store.get_task("task-s3")["state"], AgentState.CONSENSUS_CHECK.value)

        # Human resolves override with APPROVED
        change_override = self.orchestrator.resolve_override("task-s3", OverrideChoice.APPROVED, note="Tech lead approved")
        self.assertEqual(change_override.to_state, AgentState.MERGING)
        self.assertEqual(self.orchestrator.store.get_task("task-s3")["state"], AgentState.MERGING.value)

    def test_scenario_s6_deadlock_and_cancel(self):
        """Scenario S6: Deadlock -> Human Override CANCEL -> CANCELLED."""
        self.orchestrator.start_task(
            title="Experimental Feature",
            task_description="Try experimental module",
            acceptance_criteria={"tests_passed": True},
            task_id="task-s6"
        )
        self.mock_executor.simulate_produce_dev_manifest(self.tmpdir, commit_sha="c-s6", review_round=1)
        self.orchestrator.check_development_checkpoint("task-s6")
        self.orchestrator.dispatch_review_requests("task-s6")

        # 1 Approve + 1 Reject -> Deadlock
        self.mock_reviewer1.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref="c-s6", review_round=1,
            vote=Vote.YES_APPROVE, opinion_status=OpinionStatus.APPROVED
        )
        self.mock_reviewer2.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref="c-s6", review_round=1,
            vote=Vote.NO_APPROVE, opinion_status=OpinionStatus.REJECTED
        )
        self.orchestrator.collect_and_evaluate_consensus("task-s6", configured_reviewers=2)

        # Human cancels task (E10)
        change_cancel = self.orchestrator.resolve_override("task-s6", OverrideChoice.CANCEL, note="Experiment aborted")
        self.assertEqual(change_cancel.to_state, AgentState.CANCELLED)
        self.assertEqual(self.orchestrator.store.get_task("task-s6")["state"], AgentState.CANCELLED.value)


if __name__ == "__main__":
    unittest.main()
