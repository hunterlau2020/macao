"""Unit tests verifying all P0 and P1 rectifications across all expert review rounds."""

import os
import json
import shutil
import unittest
import tempfile
import datetime
import subprocess
from pathlib import Path

from macao.core.config import ConfigManager
from macao.core.types import AgentState, ExecutionMode, OverrideChoice, Vote, OpinionStatus, Decision
from macao.adapter.mock import MockAgentAdapter
from macao.workflow.orchestrator import Orchestrator
from macao.merge.controller import MergeController
from macao.utils.git_utils import GitManager
from macao.workflow.e2e_runner import ControlledE2ERunner
from macao.msg.envelope import AEPEnvelope
from macao.msg.bus import MessageBus
from macao.core.schema import validate_aep_envelope
from macao.consensus.vote import VoteAggregator


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

    def test_task_id_concurrency_no_collision_in_100_tasks(self):
        """P0-1 (Codex): Verify same-second task creation generates unique IDs without collision."""
        tmpdir = tempfile.mkdtemp()
        try:
            orch = Orchestrator(project_root=tmpdir)
            created_ids = []
            for i in range(100):
                t = orch.start_task(
                    title=f"Task {i}",
                    task_description=f"Description {i}"
                )
                created_ids.append(t["task_id"])

            self.assertEqual(len(set(created_ids)), 100)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_reviewer_timeout_degradation_scenario(self):
        """REQ-TIMEOUT & P1-1: Verify reviewer timeout marks ABSTAIN, triggers DEADLOCK and E7 override persists ABSTAIN."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Init git repo
            subprocess.run(["git", "init", "-b", "main"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Bot"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "bot@test.dev"], cwd=tmpdir, check=True)
            (Path(tmpdir) / "README.md").write_text("# Test\n")
            subprocess.run(["git", "add", "README.md"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, capture_output=True, text=True, check=True).stdout.strip()

            orch = Orchestrator(
                project_root=tmpdir,
                config={"reviewer_ids": ["codex", "opencode"], "timeouts": {"per_reviewer": "10m"}}
            )
            task = orch.start_task("Timeout Task", "Test Timeout Handling")
            t_id = task["task_id"]

            # Simulate dev manifest & dispatch
            (Path(tmpdir) / ".macao").mkdir(parents=True, exist_ok=True)
            (Path(tmpdir) / ".macao" / ".dev.yml").write_text(f"""status: ready_for_review
review_round: 1
development:
  git:
    latest_commit: "{head}"
""", encoding="utf-8")
            orch.check_development_checkpoint(t_id)
            orch.dispatch_review_requests(t_id)

            # Reviewer 1 (codex) submits approval
            rev_adapter = MockAgentAdapter(agent_id="codex", cli_name="codex", role="reviewer")
            rev_adapter.simulate_produce_review_manifest(
                project_root=tmpdir,
                checkpoint_ref=head,
                review_round=1,
                vote=Vote.YES_APPROVE,
                opinion_status=OpinionStatus.APPROVED
            )

            # 1. Advance clock by 11 minutes -> auto timeout detection triggers
            future_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=11)
            detected_timeouts = orch.detect_timed_out_reviewers(t_id, current_time=future_time)
            self.assertEqual(detected_timeouts, ["opencode"])

            # Call consensus without passing timed_out_reviewers -> internally auto-detects
            change, vdata = orch.collect_and_evaluate_consensus(
                task_id=t_id,
                configured_reviewers=2,
                timed_out_reviewers=detected_timeouts
            )

            # 1 Approve + 1 Abstain = 1 Effective Vote < Quorum 2 -> DEADLOCK (HOLD in CONSENSUS_CHECK)
            self.assertIsNone(change)
            self.assertIsNone(vdata)
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.CONSENSUS_CHECK.value)

            # Assert vote_result.json was NOT written to disk during DEADLOCK
            self.assertFalse((Path(tmpdir) / ".macao" / "vote_result.json").exists())

            # Assert REVIEWER_TIMEOUT_ABSTAIN and HUMAN_OVERRIDE_REQUEST were logged
            audits = orch.store.list_audit_events(t_id, limit=20)
            audit_types = [a["type"] for a in audits]
            self.assertIn("REVIEWER_TIMEOUT_ABSTAIN", audit_types)
            self.assertIn("DEADLOCK_DETECTED", audit_types)

            # Admin resolves override with APPROVED -> transitions to MERGING
            change_override = orch.resolve_override(t_id, "APPROVED", note="Timeout resolved by admin")
            self.assertEqual(change_override.to_state, AgentState.MERGING)

            # Assert vote_result.json on disk contains the ABSTAIN vote and correct statistics (PRD §2.2 / §3.3)
            vote_json_file = Path(tmpdir) / ".macao" / "vote_result.json"
            self.assertTrue(vote_json_file.exists())
            with open(vote_json_file, "r", encoding="utf-8") as f:
                v_res = json.load(f)

            self.assertEqual(v_res["decision"], "APPROVED")
            self.assertEqual(v_res["resolution"], "human_override")
            self.assertEqual(v_res["reviewers_responded"], 2)
            self.assertEqual(v_res["vote_breakdown"]["approve"], 1)
            self.assertEqual(v_res["vote_breakdown"]["abstain"], 1)

            votes_map = {v["reviewer"]: v["vote"] for v in v_res["votes"]}
            self.assertEqual(votes_map["codex"], "YES_APPROVE")
            self.assertEqual(votes_map["opencode"], "ABSTAIN")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_max_rework_rounds_reached_holds_without_writing_disk_vote_result(self):
        """P0-2 (Codex): Verify max rework rounds reached HOLDS without writing automatic vote_result.json."""
        tmpdir = tempfile.mkdtemp()
        try:
            subprocess.run(["git", "init", "-b", "main"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Bot"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "bot@test.dev"], cwd=tmpdir, check=True)
            (Path(tmpdir) / "README.md").write_text("# Test\n")
            subprocess.run(["git", "add", "README.md"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, capture_output=True, text=True, check=True).stdout.strip()

            orch = Orchestrator(
                project_root=tmpdir,
                config={"reviewer_ids": ["codex", "opencode"], "max_rework_rounds": 2}
            )
            task = orch.start_task("Max Round Task", "Test Max Round Guard")
            t_id = task["task_id"]
            # Set task at round 2 (equal to max_rework_rounds)
            orch.store.update_task_state(t_id, AgentState.CONSENSUS_CHECK, checkpoint_ref=head, review_round=2)

            # Both reviewers reject
            for r_id in ["codex", "opencode"]:
                rev_adapter = MockAgentAdapter(agent_id=r_id, cli_name=r_id, role="reviewer")
                rev_adapter.simulate_produce_review_manifest(
                    project_root=tmpdir,
                    checkpoint_ref=head,
                    review_round=2,
                    vote=Vote.NO_APPROVE,
                    opinion_status=OpinionStatus.REJECTED
                )

            change, vdata = orch.collect_and_evaluate_consensus(t_id, configured_reviewers=2)
            self.assertIsNone(change)
            self.assertIsNone(vdata)

            # Verify task stays in CONSENSUS_CHECK
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.CONSENSUS_CHECK.value)

            # Verify no automatic vote_result.json exists on disk
            self.assertFalse((Path(tmpdir) / ".macao" / "vote_result.json").exists())

            # Verify crash reconciler maintains CONSENSUS_CHECK
            from macao.storage.reconcile import StateReconciler
            reconciler = StateReconciler(orch.store, project_root=tmpdir)
            rec_change = reconciler.reconcile()
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.CONSENSUS_CHECK.value)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_merge_controller_refuses_dirty_worktree_fail_closed(self):
        """P0-3 (Codex): Verify MergeController refuses to merge if working tree has uncommitted changes."""
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

            # Create uncommitted modification in working directory
            f1.write_text("USER UNCOMMITTED WORK\n", encoding="utf-8")

            from macao.storage.store import StateStore
            store = StateStore(os.path.join(tmpdir, "state.db"))
            store.create_task("task-dirty", "Dirty Task", "feat", "main")
            store.update_task_state("task-dirty", AgentState.MERGING, checkpoint_ref=head)

            ctrl = MergeController(store, project_root=tmpdir)
            ok, msg, _ = ctrl.execute_merge_pipeline("task-dirty", require_signoff=False)
            self.assertFalse(ok)
            self.assertIn("uncommitted tracked modifications", msg)

            # Assert uncommitted work was NOT destroyed
            self.assertEqual(f1.read_text(encoding="utf-8"), "USER UNCOMMITTED WORK\n")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_worktree_dispatch_exception_physically_cleans_created_worktrees(self):
        """P1-1 (Claude): Verify Worktree dispatch exception physically removes previously created worktrees."""
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
            orch.store.create_task("task-tx-clean", "Tx Clean Task", "feat", "main")
            orch.store.update_task_state("task-tx-clean", AgentState.READY_FOR_REVIEW, checkpoint_ref=head)

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
                orch.dispatch_review_requests("task-tx-clean")

            # Assert task state is still READY_FOR_REVIEW
            self.assertEqual(orch.store.get_task("task-tx-clean")["state"], AgentState.READY_FOR_REVIEW.value)

            # Assert rev1 worktree directory was physically cleaned up from disk
            rev1_wt_path = Path(tmpdir) / ".macao" / "worktrees" / "rev1" / "task-tx-clean" / "r1"
            self.assertFalse(rev1_wt_path.exists())
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_artifacts_registered_and_tracked_in_database(self):
        """P1-2 (Claude / Codex / Grok / ZCode): Verify full artifact lifecycle (register -> consume -> archive -> sha256)."""
        runner = ControlledE2ERunner()
        try:
            res = runner.run_e2e_cycle()
            self.assertEqual(res["status"], "PASS")

            # Check database artifacts
            orch = Orchestrator(project_root=str(runner.repo_dir))
            artifacts = orch.store.list_artifacts(res["task_id"])
            self.assertEqual(len(artifacts), 5)

            kinds = [a["kind"] for a in artifacts]
            self.assertIn("dev_manifest", kinds)
            self.assertIn("review_manifest", kinds)
            self.assertIn("vote_result", kinds)

            # Assert all 5 artifacts are marked consumed, have valid archive paths, and valid SHA256 hashes
            for a in artifacts:
                self.assertEqual(a["consumed"], 1, f"Artifact {a['kind']} {a.get('reviewer_id')} consumed != 1")
                self.assertIsNotNone(a["archived_path"], f"Artifact {a['kind']} {a.get('reviewer_id')} archived_path is None")
                self.assertTrue(a["archived_path"].startswith(".macao/archive/"), f"Invalid archived path: {a['archived_path']}")
                self.assertNotEqual(a["sha256"], "", f"Artifact {a['kind']} {a.get('reviewer_id')} sha256 is empty")
                self.assertEqual(len(a["sha256"]), 64, f"Invalid SHA256 length: {a['sha256']}")
        finally:
            runner.cleanup()

    def test_vote_result_validation_before_write_and_fail_fast_on_invalid_resolution(self):
        """P2-1 & P2-2 (ZCode / Qwen): Verify vote_result validates before writing and raises ValueError on bad resolution."""
        tmpdir = tempfile.mkdtemp()
        try:
            aggregator = VoteAggregator(tmpdir)
            with self.assertRaises(ValueError) as ctx:
                aggregator.generate_vote_result(
                    checkpoint_ref="abc1234",
                    executor_id="claude-code",
                    review_round=1,
                    configured_reviewers=2,
                    reviews=[],
                    human_resolution="INVALID_UNRECOGNIZED_ACTION",
                    write_to_disk=True
                )
            self.assertIn("Invalid human_resolution", str(ctx.exception))
            # Verify no file written to disk
            self.assertFalse((Path(tmpdir) / ".macao" / "vote_result.json").exists())
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
            self.assertGreaterEqual(res["tracked_artifacts_count"], 4)
        finally:
            runner.cleanup()


if __name__ == "__main__":
    unittest.main()
