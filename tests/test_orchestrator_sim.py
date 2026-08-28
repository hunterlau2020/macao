"""End-to-End Multi-Agent Simulation Tests (PRD §3.4 Scenarios S1 ~ S6 & Safety Gates)."""

import os
import shutil
import unittest
import tempfile
import subprocess
from pathlib import Path

from macao.core.types import AgentState, Vote, OpinionStatus, OverrideChoice
from macao.adapter.mock import MockAgentAdapter
from macao.workflow.orchestrator import Orchestrator


class TestOrchestratorSimulation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, ".macao", "state.db")

        # Initialize clean git repository for worktree and diff support
        subprocess.run(["git", "init", "-b", "main"], cwd=self.tmpdir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test Bot"], cwd=self.tmpdir, check=True)
        subprocess.run(["git", "config", "user.email", "bot@test.dev"], cwd=self.tmpdir, check=True)
        readme = Path(self.tmpdir) / "README.md"
        readme.write_text("# Test Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.tmpdir, check=True)
        subprocess.run(["git", "commit", "-m", "chore: initial commit"], cwd=self.tmpdir, check=True)

        # Set up mock executor and reviewers
        self.mock_executor = MockAgentAdapter("cc-ds4", "claude-code", role="executor")
        self.mock_reviewer1 = MockAgentAdapter("cc-glm", "codex", role="reviewer")
        self.mock_reviewer2 = MockAgentAdapter("kimi", "kimi", role="reviewer")

        self.orchestrator = Orchestrator(
            project_root=self.tmpdir,
            db_path=self.db_path,
            executor_adapter=self.mock_executor,
            reviewer_adapters=[self.mock_reviewer1, self.mock_reviewer2],
            config={
                "max_rework_rounds": 2,
                "require_signoff": False,
                "remote_name": None,
                "reviewer_ids": ["cc-glm", "kimi"]
            }
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_commit(self, msg: str = "feat: test commit") -> str:
        subprocess.run(["git", "commit", "--allow-empty", "-m", msg], cwd=self.tmpdir, check=True, capture_output=True)
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.tmpdir, capture_output=True, text=True, check=True)
        return res.stdout.strip()

    def test_scenario_s1_happy_path_and_merge(self):
        """Scenario S1: Task Start -> Coding -> 2x Approvals -> MERGING -> DONE."""
        # 1. Start Task (E1: IDLE -> CODING)
        task = self.orchestrator.start_task(
            title="Implement OAuth2 Authentication",
            task_description="Add JWT token validation endpoint",
            acceptance_criteria={"tests_passed": True, "coverage": 0.90},
            source_branch="feature/oauth",
            target_branch="main",
            task_id="task-s1"
        )
        self.assertEqual(task["state"], AgentState.CODING.value)

        # 2. Executor completes work and produces .dev.yml
        commit_sha = self._make_commit("feat: oauth2 implementation")
        self.mock_executor.simulate_produce_dev_manifest(self.tmpdir, commit_sha=commit_sha, review_round=1)

        # 3. Orchestrator detects checkpoint (CODING -> READY_FOR_REVIEW)
        change_dev = self.orchestrator.check_development_checkpoint("task-s1")
        self.assertIsNotNone(change_dev)
        self.assertEqual(change_dev.to_state, AgentState.READY_FOR_REVIEW)

        # 4. Dispatch Reviews (E2: READY_FOR_REVIEW -> WAITING_REVIEW)
        change_dispatch = self.orchestrator.dispatch_review_requests("task-s1")
        self.assertEqual(change_dispatch.to_state, AgentState.WAITING_REVIEW)

        # Verify .dev.yml was archived
        archived_dev = Path(self.tmpdir) / ".macao" / "archive" / commit_sha / "r1" / ".dev.yml"
        self.assertTrue(archived_dev.exists())

        # 5. Reviewers produce approvals (.review.yml)
        self.mock_reviewer1.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref=commit_sha, review_round=1,
            vote=Vote.YES_APPROVE, opinion_status=OpinionStatus.APPROVED
        )
        self.mock_reviewer2.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref=commit_sha, review_round=1,
            vote=Vote.YES_APPROVE, opinion_status=OpinionStatus.APPROVED
        )

        # 6. Evaluate consensus (E3: WAITING_REVIEW -> CONSENSUS_CHECK -> E4: MERGING)
        change_final, vote_data = self.orchestrator.collect_and_evaluate_consensus("task-s1", configured_reviewers=2)
        self.assertIsNotNone(change_final)
        self.assertEqual(change_final.to_state, AgentState.MERGING)
        self.assertEqual(vote_data["decision"], "APPROVED")

        # 7. Execute Merge pipeline -> DONE (E4a)
        ok, msg, change_done = self.orchestrator.execute_merge("task-s1")
        self.assertTrue(ok)
        self.assertEqual(change_done.to_state, AgentState.DONE)
        self.assertEqual(self.orchestrator.store.get_task("task-s1")["state"], AgentState.DONE.value)

    def test_scenario_s2_rework_loop(self):
        """Scenario S2: Reviews Reject -> Rework Round 2 -> Approvals -> MERGING."""
        self.orchestrator.start_task(
            title="Refactor Cache",
            task_description="Memory LRU cache",
            acceptance_criteria={"tests_passed": True},
            task_id="task-s2"
        )
        c_r1 = self._make_commit("feat: cache r1")
        self.mock_executor.simulate_produce_dev_manifest(self.tmpdir, commit_sha=c_r1, review_round=1)
        self.orchestrator.check_development_checkpoint("task-s2")
        self.orchestrator.dispatch_review_requests("task-s2")

        # Round 1 Reviewers REJECT
        self.mock_reviewer1.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref=c_r1, review_round=1,
            vote=Vote.NO_APPROVE, opinion_status=OpinionStatus.REJECTED,
            issues=[{"type": "concurrency", "severity": "critical", "issue": "Missing lock"}]
        )
        self.mock_reviewer2.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref=c_r1, review_round=1,
            vote=Vote.NO_APPROVE, opinion_status=OpinionStatus.REJECTED,
            issues=[{"type": "resource", "severity": "major", "issue": "File descriptor leak"}]
        )

        # Evaluate consensus -> REWORK (E5)
        change_r1, vote_data = self.orchestrator.collect_and_evaluate_consensus("task-s2", configured_reviewers=2)
        self.assertEqual(change_r1.to_state, AgentState.REWORK)
        self.assertEqual(vote_data["decision"], "REWORK_REQUIRED")

        # Verify task is in REWORK with round=2
        task_r2 = self.orchestrator.store.get_task("task-s2")
        self.assertEqual(task_r2["review_round"], 2)

        # Round 2: Executor fixes issues and produces dev manifest (c_r2)
        c_r2 = self._make_commit("fix: cache r2")
        self.mock_executor.simulate_produce_dev_manifest(self.tmpdir, commit_sha=c_r2, review_round=2)
        self.orchestrator.check_development_checkpoint("task-s2")
        self.orchestrator.dispatch_review_requests("task-s2")

        # Round 2 Reviewers APPROVE
        self.mock_reviewer1.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref=c_r2, review_round=2,
            vote=Vote.YES_APPROVE, opinion_status=OpinionStatus.APPROVED
        )
        self.mock_reviewer2.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref=c_r2, review_round=2,
            vote=Vote.YES_APPROVE, opinion_status=OpinionStatus.APPROVED
        )

        change_r2, vote_data_r2 = self.orchestrator.collect_and_evaluate_consensus("task-s2", configured_reviewers=2)
        self.assertEqual(change_r2.to_state, AgentState.MERGING)
        self.assertEqual(vote_data_r2["decision"], "APPROVED")

    def test_p0_deadlock_does_not_write_fake_vote_result_and_holds(self):
        """P0-1 Regression Test: 1 Approve + 1 Reject -> Deadlock MUST HOLD and NOT write vote_result.json."""
        self.orchestrator.start_task(
            title="Deadlock Test",
            task_description="Testing deadlock HOLD semantics",
            acceptance_criteria={"tests_passed": True},
            task_id="task-deadlock"
        )
        commit_sha = self._make_commit("feat: deadlock test commit")
        self.mock_executor.simulate_produce_dev_manifest(self.tmpdir, commit_sha=commit_sha, review_round=1)
        self.orchestrator.check_development_checkpoint("task-deadlock")
        self.orchestrator.dispatch_review_requests("task-deadlock")

        # 1 Approve + 1 Reject
        self.mock_reviewer1.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref=commit_sha, review_round=1,
            vote=Vote.YES_APPROVE, opinion_status=OpinionStatus.APPROVED
        )
        self.mock_reviewer2.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref=commit_sha, review_round=1,
            vote=Vote.NO_APPROVE, opinion_status=OpinionStatus.REJECTED
        )

        # Collect consensus
        change, vote_data = self.orchestrator.collect_and_evaluate_consensus("task-deadlock", configured_reviewers=2)

        # State must NOT transition out of CONSENSUS_CHECK (returns None change)
        self.assertIsNone(change)
        task_now = self.orchestrator.store.get_task("task-deadlock")
        self.assertEqual(task_now["state"], AgentState.CONSENSUS_CHECK.value)

        # PRD §3.3 Rule: vote_result.json MUST NOT be written to disk on DEADLOCK
        vote_json_path = Path(self.tmpdir) / ".macao" / "vote_result.json"
        self.assertFalse(vote_json_path.exists())

    def test_p0_reviewer_deduplication(self):
        """P0-2 Regression Test: Duplicate reviews from same reviewer ID must not count as 2 votes."""
        self.orchestrator.start_task(
            title="Dedup Test",
            task_description="Testing reviewer deduplication",
            acceptance_criteria={"tests_passed": True},
            task_id="task-dedup"
        )
        commit_sha = self._make_commit("feat: dedup test commit")
        self.mock_executor.simulate_produce_dev_manifest(self.tmpdir, commit_sha=commit_sha, review_round=1)
        self.orchestrator.check_development_checkpoint("task-dedup")
        self.orchestrator.dispatch_review_requests("task-dedup")

        # Same reviewer produces 2 reviews
        self.mock_reviewer1.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref=commit_sha, review_round=1,
            vote=Vote.YES_APPROVE, opinion_status=OpinionStatus.APPROVED,
            filename="rev1_first.review.yml"
        )
        self.mock_reviewer1.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref=commit_sha, review_round=1,
            vote=Vote.YES_APPROVE, opinion_status=OpinionStatus.APPROVED,
            filename="rev1_second.review.yml"
        )

        # Quorum is 2, but only 1 unique reviewer -> cannot reach quorum (holds in WAITING_REVIEW)
        change, vote_data = self.orchestrator.collect_and_evaluate_consensus("task-dedup", configured_reviewers=2)
        self.assertIsNone(change)
        self.assertIsNone(vote_data)
        task_now = self.orchestrator.store.get_task("task-dedup")
        self.assertEqual(task_now["state"], AgentState.WAITING_REVIEW.value)

    def test_p1_max_rework_rounds_guard(self):
        """P1-1 Regression Test: When max rework rounds is reached, reject must trigger override rather than auto REWORK."""
        self.orchestrator.start_task(
            title="Max Rework Test",
            task_description="Testing max rework limit",
            acceptance_criteria={"tests_passed": True},
            task_id="task-max-rnd"
        )
        # Force task directly to round 2 (max_rework_rounds is 2)
        self.orchestrator.store.update_task_state("task-max-rnd", AgentState.CODING, review_round=2)

        commit_sha = self._make_commit("feat: max rework test commit")
        self.mock_executor.simulate_produce_dev_manifest(self.tmpdir, commit_sha=commit_sha, review_round=2)
        self.orchestrator.check_development_checkpoint("task-max-rnd")
        self.orchestrator.dispatch_review_requests("task-max-rnd")

        # Reviewers REJECT in round 2 (max round)
        self.mock_reviewer1.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref=commit_sha, review_round=2,
            vote=Vote.NO_APPROVE, opinion_status=OpinionStatus.REJECTED
        )
        self.mock_reviewer2.simulate_produce_review_manifest(
            self.tmpdir, checkpoint_ref=commit_sha, review_round=2,
            vote=Vote.NO_APPROVE, opinion_status=OpinionStatus.REJECTED
        )

        # Evaluate consensus -> should NOT auto-transition to REWORK, but hold in CONSENSUS_CHECK
        change, vote_data = self.orchestrator.collect_and_evaluate_consensus("task-max-rnd", configured_reviewers=2)
        self.assertIsNone(change)
        task_now = self.orchestrator.store.get_task("task-max-rnd")
        self.assertEqual(task_now["state"], AgentState.CONSENSUS_CHECK.value)


if __name__ == "__main__":
    unittest.main()
