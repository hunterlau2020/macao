"""Unit tests verifying P0 and P1 rectifications from 4-expert review of 906b17e and e7ba2d2."""

import os
import shutil
import unittest
import tempfile
import subprocess
from pathlib import Path

from macao.core.config import ConfigManager
from macao.core.types import AgentState, ExecutionMode, OverrideChoice, Vote, OpinionStatus
from macao.adapter.mock import MockAgentAdapter
from macao.workflow.orchestrator import Orchestrator
from macao.merge.controller import MergeController
from macao.utils.git_utils import GitManager
from macao.workflow.e2e_runner import ControlledE2ERunner
from macao.msg.envelope import AEPEnvelope
from macao.msg.bus import MessageBus
from macao.core.schema import validate_aep_envelope


class TestP0P1Rectification(unittest.TestCase):

    def test_message_id_entropy_zero_collisions_in_5000(self):
        """P0-NEW-1: Verify message_id generation has 0 collisions across 5,000 samples."""
        ids = [AEPEnvelope.generate_message_id() for _ in range(5000)]
        self.assertEqual(len(set(ids)), 5000)
        for mid in ids[:50]:
            self.assertTrue(mid.startswith("msg-"))
            self.assertEqual(len(mid.split("-")), 3)

        # Database publish verification with 500 high-frequency messages
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(tmpdir, "test_msg.db")
            bus = MessageBus(db_path)
            for i in range(500):
                bus.publish(
                    msg_type="STATE_CHANGED",
                    from_agent="test",
                    to_agent="all",
                    payload={"index": i}
                )
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_resolve_override_all_four_choices_and_valid_aep(self):
        """P0-NEW-2: Verify resolve_override handles all 4 choices and produces schema-valid AEP messages."""
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(tmpdir, "test_ov.db")
            orch = Orchestrator(
                project_root=tmpdir,
                db_path=db_path,
                config={"reviewer_ids": ["codex", "opencode"]}
            )

            choices = [
                (OverrideChoice.APPROVED, AgentState.MERGING),
                ("REWORK", AgentState.REWORK),
                ("RETRY_REVIEW", AgentState.WAITING_REVIEW),
                ("CANCEL", AgentState.CANCELLED)
            ]

            for i, (choice, expected_state) in enumerate(choices):
                t_id = f"task-ov-{i}"
                orch.store.create_task(t_id, f"Override Task {i}", "feat", "main")
                orch.store.update_task_state(t_id, AgentState.CONSENSUS_CHECK, checkpoint_ref=f"commit-{i}", review_round=1)

                change = orch.resolve_override(t_id, choice, note=f"Human decision {i}")
                self.assertEqual(change.to_state, expected_state)
                self.assertEqual(orch.store.get_task(t_id)["state"], expected_state.value)

            # Verify all published messages validate against schema
            messages = orch.store.list_messages(limit=50)
            self.assertGreaterEqual(len(messages), 4)
            for m in messages:
                val, err = validate_aep_envelope(m)
                self.assertTrue(val, f"Schema error on message: {err}")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_merge_controller_ci_gate_failure_rollback(self):
        """P0-NEW-3: Verify CI gate failure atomically rolls back target branch to pre-merge commit."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Init git repo
            subprocess.run(["git", "init", "-b", "main"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Bot"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "bot@test.dev"], cwd=tmpdir, check=True)

            f1 = Path(tmpdir) / "f1.txt"
            f1.write_text("initial\n", encoding="utf-8")
            subprocess.run(["git", "add", "f1.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "initial commit"], cwd=tmpdir, check=True)
            initial_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, capture_output=True, text=True, check=True).stdout.strip()

            # Create feature branch commit
            subprocess.run(["git", "checkout", "-b", "feat/ci-test"], cwd=tmpdir, check=True, capture_output=True)
            f2 = Path(tmpdir) / "f2.txt"
            f2.write_text("feature code\n", encoding="utf-8")
            subprocess.run(["git", "add", "f2.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "feature commit"], cwd=tmpdir, check=True)
            feat_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, capture_output=True, text=True, check=True).stdout.strip()

            # Switch back to main
            subprocess.run(["git", "checkout", "main"], cwd=tmpdir, check=True, capture_output=True)

            from macao.storage.store import StateStore
            store = StateStore(os.path.join(tmpdir, "state.db"))
            store.create_task("task-ci-fail", "CI Fail Task", "feat/ci-test", "main")
            store.update_task_state("task-ci-fail", AgentState.MERGING, checkpoint_ref=feat_head)

            ctrl = MergeController(store, project_root=tmpdir)
            # Run with failing CI command
            ok, msg, _ = ctrl.execute_merge_pipeline(
                "task-ci-fail",
                target_branch="main",
                ci_gate_command="python3 -c 'import sys; sys.exit(1)'",
                require_signoff=False
            )
            self.assertFalse(ok)
            self.assertIn("CI gate command failed", msg)

            # Assert main branch was rolled back to initial_head
            current_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, capture_output=True, text=True, check=True).stdout.strip()
            self.assertEqual(current_head, initial_head)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_merge_controller_missing_remote_fail_closed(self):
        """P0-NEW-3: Verify MergeController fails closed when configured remote does not exist."""
        tmpdir = tempfile.mkdtemp()
        try:
            subprocess.run(["git", "init", "-b", "main"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Bot"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "bot@test.dev"], cwd=tmpdir, check=True)
            f1 = Path(tmpdir) / "f1.txt"
            f1.write_text("initial\n", encoding="utf-8")
            subprocess.run(["git", "add", "f1.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "initial commit"], cwd=tmpdir, check=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, capture_output=True, text=True, check=True).stdout.strip()

            from macao.storage.store import StateStore
            store = StateStore(os.path.join(tmpdir, "state.db"))
            store.create_task("task-rem-fail", "Remote Fail Task", "feat", "main")
            store.update_task_state("task-rem-fail", AgentState.MERGING, checkpoint_ref=head)

            ctrl = MergeController(store, project_root=tmpdir)
            ok, msg, _ = ctrl.execute_merge_pipeline(
                "task-rem-fail",
                target_branch="main",
                require_signoff=False,
                remote_name="nonexistent_origin"
            )
            self.assertFalse(ok)
            self.assertIn("not found in repository remotes", msg)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_worktree_dispatch_transactional_fail_closed(self):
        """P1-1: Verify worktree creation failure is transactional and does not advance FSM."""
        tmpdir = tempfile.mkdtemp()
        try:
            subprocess.run(["git", "init", "-b", "main"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Bot"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "bot@test.dev"], cwd=tmpdir, check=True)
            f1 = Path(tmpdir) / "f1.txt"
            f1.write_text("initial\n", encoding="utf-8")
            subprocess.run(["git", "add", "f1.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "initial commit"], cwd=tmpdir, check=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, capture_output=True, text=True, check=True).stdout.strip()

            orch = Orchestrator(
                project_root=tmpdir,
                config={"reviewer_ids": ["rev1", "rev2"]}
            )
            orch.store.create_task("task-tx", "Tx Task", "feat", "main")
            orch.store.update_task_state("task-tx", AgentState.READY_FOR_REVIEW, checkpoint_ref=head)

            # Mock second worktree to fail
            orig_fn = orch.git.create_isolated_worktree
            call_count = [0]
            def faulty_worktree(reviewer_id, task_id, rnd, commit_sha):
                call_count[0] += 1
                if call_count[0] > 1:
                    raise IOError("Simulated disk error on second worktree")
                return orig_fn(reviewer_id, task_id, rnd, commit_sha)

            orch.git.create_isolated_worktree = faulty_worktree

            with self.assertRaises(RuntimeError):
                orch.dispatch_review_requests("task-tx")

            # Assert task state is still READY_FOR_REVIEW (not WAITING_REVIEW)
            self.assertEqual(orch.store.get_task("task-tx")["state"], AgentState.READY_FOR_REVIEW.value)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_config_keys_penetration_and_require_signoff_fail_closed(self):
        """P0-1: Verify config keys penetration to Orchestrator and signoff fail-closed gate."""
        tmpdir = tempfile.mkdtemp()
        try:
            cfg_file = Path(tmpdir) / "macao.yaml"
            cfg_content = """project:
  name: "test-signoff"
  repository:
    workspace_path: "."
    remote_name: "origin"
    default_branch: "main"

team:
  executor:
    id: "claude-code"
    cli: "claude-code"
    adapter: "claude-hook"
  reviewers:
    - id: "codex"
      cli: "codex"
      adapter: "pty-wrapper"
    - id: "opencode"
      cli: "opencode"
      adapter: "pty-wrapper"

policy:
  consensus_rule: "2/3_majority"
  min_effective_votes: 2
  max_rework_rounds: 5
  review_strategy: "delta_plus_focus"

merge:
  strategy: "ff_only"
  ci_gate_command: "pytest tests"
  require_human_signoff: true
  rebase_before_merge: false
"""
            cfg_file.write_text(cfg_content, encoding="utf-8")
            config = ConfigManager.load_config(str(cfg_file))

            self.assertTrue(config["require_signoff"])
            self.assertEqual(config["max_rework_rounds"], 5)
            self.assertEqual(config["ci_gate_command"], "pytest tests")
            self.assertEqual(config["remote_name"], "origin")
            self.assertEqual(config["target_branch"], "main")
            self.assertEqual(config["reviewer_ids"], ["codex", "opencode"])

            orchestrator = Orchestrator(project_root=tmpdir, config=config)
            self.assertTrue(orchestrator.config["require_signoff"])
            self.assertEqual(orchestrator.config["max_rework_rounds"], 5)
            self.assertEqual(orchestrator.config["ci_gate_command"], "pytest tests")
            self.assertEqual(orchestrator.config["reviewer_ids"], ["codex", "opencode"])

            orchestrator.store.create_task("task-signoff", "Signoff Task", "feat", "main")
            orchestrator.store.update_task_state("task-signoff", AgentState.MERGING, checkpoint_ref="dummy-ref")
            ok, msg, _ = orchestrator.execute_merge("task-signoff")
            self.assertFalse(ok)
            self.assertIn("Human signoff required", msg)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_merge_controller_non_git_fail_closed(self):
        """P1-2: Verify MergeController returns False (fail-closed) on non-git directory."""
        tmpdir = tempfile.mkdtemp()
        try:
            from macao.storage.store import StateStore
            store = StateStore(os.path.join(tmpdir, "state.db"))
            store.create_task("task-nogit", "Non Git Task", "feat", "main")
            store.update_task_state("task-nogit", AgentState.MERGING, checkpoint_ref="c-123")

            ctrl = MergeController(store, project_root=tmpdir)
            ok, msg, _ = ctrl.execute_merge_pipeline("task-nogit", require_signoff=False)
            self.assertFalse(ok)
            self.assertIn("not a valid git repository", msg)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_git_utils_fail_closed_and_no_dummy_data(self):
        """P1-3 & P1-6: Verify worktree creation fail-closed on non-git and no fake diff files."""
        tmpdir = tempfile.mkdtemp()
        try:
            git = GitManager(tmpdir)
            with self.assertRaises(RuntimeError) as ctx:
                git.create_isolated_worktree("codex", "task-1", 1, "c-123")
            self.assertIn("not a valid git repository", str(ctx.exception))

            changed = git.get_changed_files("main", "feat")
            self.assertEqual(changed, [])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_e2e_runner_truthful_evidence_and_archive(self):
        """P0-2: Verify E2E runner executes with 3 reviewers, votes_yes=3, and non-empty archive."""
        runner = ControlledE2ERunner()
        try:
            res = runner.run_e2e_cycle()
            self.assertEqual(res["status"], "PASS")
            self.assertEqual(res["final_state"], "DONE")
            self.assertEqual(res["decision"], "APPROVED")
            self.assertTrue(res["merge_exact_match"])

            step3 = [s for s in res["steps"] if s.get("step") == "3. Worktree Dispatch"][0]
            self.assertEqual(step3["reviewers_count"], 3)
            self.assertEqual(step3["reviewers"], ["codex", "opencode", "antigravity"])

            step4 = [s for s in res["steps"] if s.get("step") == "4. Consensus Evaluation"][0]
            self.assertEqual(step4["votes_yes"], 3)
            self.assertEqual(step4["effective_votes"], 3)

            self.assertGreaterEqual(res["archived_count"], 4)
            self.assertIn(".dev.yml", res["archived_files"])
            self.assertIn("vote_result.json", res["archived_files"])
        finally:
            runner.cleanup()


if __name__ == "__main__":
    unittest.main()
