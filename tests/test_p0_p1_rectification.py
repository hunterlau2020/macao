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
            (Path(tmpdir) / ".macao" / ".dev.yml").write_text(f"""version: "1.0"
status: ready_for_review
signal: EXPLICIT
review_round: 1
executor:
  id: claude
  cli: claude
development:
  quality_metrics:
    tests_passed: true
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

    def test_three_reviewer_timeout_must_hold_and_require_human_override(self):
        """P1-NEW-3: In 3-reviewer scenario (2 Approve + 1 Timeout), timeout MUST HOLD and NOT auto-merge."""
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
                config={"reviewer_ids": ["codex", "opencode", "antigravity"], "timeouts": {"per_reviewer": "10m"}}
            )
            task = orch.start_task("Timeout 3Rev Task", "Test 3Rev Timeout Handling")
            t_id = task["task_id"]

            (Path(tmpdir) / ".macao").mkdir(parents=True, exist_ok=True)
            (Path(tmpdir) / ".macao" / ".dev.yml").write_text(f"""version: "1.0"
status: ready_for_review
signal: EXPLICIT
review_round: 1
executor:
  id: claude
  cli: claude
development:
  quality_metrics:
    tests_passed: true
  git:
    latest_commit: "{head}"
""", encoding="utf-8")
            orch.check_development_checkpoint(t_id)
            orch.dispatch_review_requests(t_id)

            # Reviewer 1 & 2 submit approval (2 of 3)
            for r_id in ["codex", "antigravity"]:
                rev_adapter = MockAgentAdapter(agent_id=r_id, cli_name=r_id, role="reviewer")
                rev_adapter.simulate_produce_review_manifest(
                    project_root=tmpdir,
                    checkpoint_ref=head,
                    review_round=1,
                    vote=Vote.YES_APPROVE,
                    opinion_status=OpinionStatus.APPROVED
                )

            # Advance clock by 11 minutes -> opencode times out
            future_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=11)
            detected_timeouts = orch.detect_timed_out_reviewers(t_id, current_time=future_time)
            self.assertEqual(detected_timeouts, ["opencode"])

            # Call consensus: Even though 2/3 approved, because opencode timed out, it MUST HOLD in CONSENSUS_CHECK!
            change, vdata = orch.collect_and_evaluate_consensus(
                task_id=t_id,
                configured_reviewers=3,
                timed_out_reviewers=detected_timeouts
            )

            self.assertIsNone(change)
            self.assertIsNone(vdata)
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.CONSENSUS_CHECK.value)
            # Automatic vote_result.json must NOT be written to disk
            self.assertFalse((Path(tmpdir) / ".macao" / "vote_result.json").exists())

            # Human resolves override with APPROVED -> moves to MERGING
            change_ov = orch.resolve_override(t_id, "APPROVED", note="Approved by human admin despite timeout")
            self.assertEqual(change_ov.to_state, AgentState.MERGING)

            # Assert vote_result.json is written with 3 reviewers, 2 approve, 1 abstain
            vote_json_file = Path(tmpdir) / ".macao" / "vote_result.json"
            self.assertTrue(vote_json_file.exists())
            with open(vote_json_file, "r", encoding="utf-8") as f:
                v_res = json.load(f)

            self.assertEqual(v_res["decision"], "APPROVED")
            self.assertEqual(v_res["resolution"], "human_override")
            self.assertEqual(v_res["reviewers_responded"], 3)
            self.assertEqual(v_res["vote_breakdown"]["approve"], 2)
            self.assertEqual(v_res["vote_breakdown"]["abstain"], 1)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_audit_polling_over_50_does_not_lose_timeout_reviewers(self):
        """P1-NEW-4: Polling repeatedly (>80 events) does not push out dispatch event or lose timeout reviewers."""
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
                config={"reviewer_ids": ["codex", "opencode"], "timeouts": {"per_reviewer": "10m"}}
            )
            task = orch.start_task("Poll Overflow Task", "Test Robust Query")
            t_id = task["task_id"]

            (Path(tmpdir) / ".macao").mkdir(parents=True, exist_ok=True)
            (Path(tmpdir) / ".macao" / ".dev.yml").write_text(f"""version: "1.0"
status: ready_for_review
signal: EXPLICIT
review_round: 1
executor:
  id: claude
  cli: claude
development:
  quality_metrics:
    tests_passed: true
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

            future_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=11)

            # Simulate heavy polling generating 100 dummy audit events
            for i in range(100):
                orch.store.log_audit_event(t_id, "POLL_HEARTBEAT", {"poll_seq": i, "review_round": 1})

            # Detect timeout must still accurately find opencode
            detected = orch.detect_timed_out_reviewers(t_id, current_time=future_time)
            self.assertEqual(detected, ["opencode"])

            # Call consensus
            orch.collect_and_evaluate_consensus(t_id, configured_reviewers=2, timed_out_reviewers=detected)

            # Generate 50 more dummy audit events
            for i in range(50):
                orch.store.log_audit_event(t_id, "POLL_HEARTBEAT", {"poll_seq": 100 + i, "review_round": 1})

            # Resolve override
            orch.resolve_override(t_id, "APPROVED", note="Override after heavy polling")

            # Assert vote_result.json still contains opencode ABSTAIN
            vote_json_file = Path(tmpdir) / ".macao" / "vote_result.json"
            self.assertTrue(vote_json_file.exists())
            with open(vote_json_file, "r", encoding="utf-8") as f:
                v_res = json.load(f)

            self.assertEqual(v_res["reviewers_responded"], 2)
            self.assertEqual(v_res["vote_breakdown"]["abstain"], 1)
            votes_map = {v["reviewer"]: v["vote"] for v in v_res["votes"]}
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
            subprocess.run(["git", "init", "-b", "main"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Bot"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "bot@test.dev"], cwd=tmpdir, check=True)
            f_init = Path(tmpdir) / "init.txt"
            f_init.write_text("init\n", encoding="utf-8")
            subprocess.run(["git", "add", "init.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, capture_output=True, text=True, check=True).stdout.strip()

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
                orch.store.update_task_state(t_id, AgentState.CONSENSUS_CHECK, checkpoint_ref=head, review_round=1)

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

    def test_signoff_bound_to_checkpoint_ref_prevents_stale_merge(self):
        """P1-NEW-5: Verify human signoff must match checkpoint_ref, preventing stale round 1 signoff from merging round 2 code."""
        tmpdir = tempfile.mkdtemp()
        try:
            subprocess.run(["git", "init", "-b", "main"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Bot"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "bot@test.dev"], cwd=tmpdir, check=True)

            # Initial commit on main
            f_init = Path(tmpdir) / "init.txt"
            f_init.write_text("init\n", encoding="utf-8")
            subprocess.run(["git", "add", "init.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True)

            # Round 1 commit (ref_r1)
            subprocess.run(["git", "checkout", "-b", "feat/p1-test"], cwd=tmpdir, check=True, capture_output=True)
            f_r1 = Path(tmpdir) / "r1.txt"
            f_r1.write_text("round 1 code\n", encoding="utf-8")
            subprocess.run(["git", "add", "r1.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "r1 commit"], cwd=tmpdir, check=True)
            ref_r1 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, capture_output=True, text=True, check=True).stdout.strip()

            # Round 2 commit (ref_r2)
            f_r2 = Path(tmpdir) / "r2.txt"
            f_r2.write_text("round 2 rework code\n", encoding="utf-8")
            subprocess.run(["git", "add", "r2.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "r2 commit"], cwd=tmpdir, check=True)
            ref_r2 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, capture_output=True, text=True, check=True).stdout.strip()

            # Switch back to main
            subprocess.run(["git", "checkout", "main"], cwd=tmpdir, check=True, capture_output=True)

            from macao.storage.store import StateStore
            store = StateStore(os.path.join(tmpdir, "state.db"), project_root=tmpdir)
            store.create_task("task-stale-signoff", "Stale Signoff Task", "feat/p1-test", "main")
            store.update_task_state("task-stale-signoff", AgentState.MERGING, checkpoint_ref=ref_r2, review_round=2)

            # Grant signoff ONLY for Round 1 (ref_r1)
            store.log_audit_event("task-stale-signoff", "HUMAN_MERGE_APPROVED", {
                "checkpoint_ref": ref_r1,
                "note": "Signed off round 1 commit"
            })

            ctrl = MergeController(store, project_root=tmpdir)

            # Attempt merge of round 2 commit (ref_r2) with stale signoff
            ok, msg, _ = ctrl.execute_merge_pipeline(
                "task-stale-signoff",
                target_branch="main",
                require_signoff=True
            )
            self.assertFalse(ok)
            self.assertIn("Human signoff required for checkpoint", msg)
            self.assertIn(ref_r2, msg)

            # Now grant valid signoff for Round 2 (ref_r2)
            store.log_audit_event("task-stale-signoff", "HUMAN_MERGE_APPROVED", {
                "checkpoint_ref": ref_r2,
                "note": "Signed off round 2 commit"
            })
            ok_valid, msg_valid, merged_commit = ctrl.execute_merge_pipeline(
                "task-stale-signoff",
                target_branch="main",
                require_signoff=True
            )
            self.assertTrue(ok_valid)
            self.assertEqual(merged_commit, ref_r2)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_late_review_after_timeout_maintains_hold_and_does_not_auto_merge(self):
        """P1-NEW-7 / P1-Q2: Verify late review submission after timeout disposition cannot bypass HOLD or trigger auto-merge."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Initialize git repo
            subprocess.run(["git", "init", "-b", "main"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Bot"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "bot@test.dev"], cwd=tmpdir, check=True)
            f_init = Path(tmpdir) / "init.txt"
            f_init.write_text("init\n", encoding="utf-8")
            subprocess.run(["git", "add", "init.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, capture_output=True, text=True, check=True).stdout.strip()

            orch = Orchestrator(
                project_root=tmpdir,
                config={
                    "reviewer_ids": ["codex", "opencode"],
                    "timeouts": {"per_reviewer": "0s"}
                }
            )
            t = orch.start_task("Late Review Test", "Testing late submission protection")
            t_id = t["task_id"]

            orch.store.update_task_state(t_id, AgentState.WAITING_REVIEW, checkpoint_ref=head, review_round=1)

            # Dispatch audit logged in the past
            past_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=10)).isoformat()
            orch.store.log_audit_event(t_id, "REVIEW_REQUESTS_DISPATCHED", {
                "checkpoint_ref": head,
                "review_round": 1,
                "reviewers": ["codex", "opencode"],
                "deadline": past_time
            })

            # codex submits YES review via MockAgentAdapter
            codex_adapter = MockAgentAdapter(agent_id="codex", cli_name="codex", role="reviewer")
            codex_adapter.simulate_produce_review_manifest(
                project_root=tmpdir,
                checkpoint_ref=head,
                review_round=1,
                vote=Vote.YES_APPROVE,
                opinion_status=OpinionStatus.APPROVED
            )

            # First collect: opencode times out -> system must HOLD in CONSENSUS_CHECK and log REVIEWER_TIMEOUT_ABSTAIN
            change, vdata = orch.collect_and_evaluate_consensus(t_id)
            self.assertIsNone(change)
            self.assertIsNone(vdata)
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.CONSENSUS_CHECK.value)

            timeout_audits = orch.store.get_audit_events_by_type(t_id, "REVIEWER_TIMEOUT_ABSTAIN", review_round=1)
            self.assertEqual(len(timeout_audits), 1)
            self.assertEqual(timeout_audits[0]["detail"]["reviewer_id"], "opencode")

            # Now simulate opencode LATE submitting a YES review
            opencode_adapter = MockAgentAdapter(agent_id="opencode", cli_name="opencode", role="reviewer")
            opencode_adapter.simulate_produce_review_manifest(
                project_root=tmpdir,
                checkpoint_ref=head,
                review_round=1,
                vote=Vote.YES_APPROVE,
                opinion_status=OpinionStatus.APPROVED
            )

            # Second collect: Even with opencode file now present, timeout disposition must HOLD and NOT auto-merge
            change2, vdata2 = orch.collect_and_evaluate_consensus(t_id)
            self.assertIsNone(change2)
            self.assertIsNone(vdata2)
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.CONSENSUS_CHECK.value)

            late_audits = orch.store.get_audit_events_by_type(t_id, "LATE_REVIEW_ISOLATED", review_round=1)
            self.assertGreaterEqual(len(late_audits), 1)

            # Confirm only explicit human override can transition to MERGING with human_override resolution
            change_human = orch.resolve_override(t_id, "APPROVED", note="Human override signoff")
            self.assertEqual(change_human.to_state, AgentState.MERGING)
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.MERGING.value)

            vote_res_file = Path(tmpdir) / ".macao" / "vote_result.json"
            self.assertTrue(vote_res_file.exists())
            with open(vote_res_file, "r") as f:
                vr = json.load(f)
            self.assertEqual(vr["resolution"], "human_override")
            self.assertEqual(vr["reviewers_responded"], 2)
            self.assertEqual(vr["vote_breakdown"]["abstain"], 1)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_retry_review_override_clears_reviews_and_redispatches_fresh_requests(self):
        """P1-NEW-6: Verify RETRY_REVIEW (E9) clears active reviews and re-dispatches with fresh deadline."""
        tmpdir = tempfile.mkdtemp()
        try:
            subprocess.run(["git", "init", "-b", "main"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Bot"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "bot@test.dev"], cwd=tmpdir, check=True)
            f_init = Path(tmpdir) / "init.txt"
            f_init.write_text("init\n", encoding="utf-8")
            subprocess.run(["git", "add", "init.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True)
            head_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, capture_output=True, text=True, check=True).stdout.strip()

            orch = Orchestrator(
                project_root=tmpdir,
                config={
                    "reviewer_ids": ["codex", "opencode"],
                    "timeouts": {"per_reviewer": "10m"}
                }
            )
            t = orch.start_task("Retry Test", "Testing E9 retry dispatch")
            t_id = t["task_id"]

            orch.store.update_task_state(t_id, AgentState.CONSENSUS_CHECK, checkpoint_ref=head_sha, review_round=1)

            # Put some review files in .macao/.reviews/
            reviews_dir = Path(tmpdir) / ".macao" / ".reviews"
            reviews_dir.mkdir(parents=True, exist_ok=True)
            (reviews_dir / "codex.review.yml").write_text("reviewer: codex\n", encoding="utf-8")
            (reviews_dir / "opencode.review.yml").write_text("reviewer: opencode\n", encoding="utf-8")

            # Resolve override with RETRY_REVIEW
            change = orch.resolve_override(t_id, "RETRY_REVIEW", note="Retrying review round")
            self.assertEqual(change.to_state, AgentState.WAITING_REVIEW)
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.WAITING_REVIEW.value)

            # Assert .reviews/ active directory is cleared of old review files
            remaining_reviews = list(reviews_dir.glob("*.review.yml"))
            self.assertEqual(remaining_reviews, [])

            # Assert fresh REVIEW_REQUESTS_DISPATCHED audit event is logged
            dispatch_audits = orch.store.get_audit_events_by_type(t_id, "REVIEW_REQUESTS_DISPATCHED", review_round=1)
            self.assertGreaterEqual(len(dispatch_audits), 1)

            # Assert fresh messages published
            msgs = orch.store.list_messages()
            rev_msgs = [m for m in msgs if m.get("type") == "REVIEW_REQUEST"]
            self.assertGreaterEqual(len(rev_msgs), 2)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_resolve_override_invalid_transition_does_not_write_orphan_vote_result(self):
        """P2-NEW-2: Verify illegal state transition in resolve_override raises ValueError without leaving orphan vote_result.json."""
        tmpdir = tempfile.mkdtemp()
        try:
            orch = Orchestrator(project_root=tmpdir)
            t = orch.start_task("Invalid Transition Task", "Testing fail-closed override")
            t_id = t["task_id"]

            # Task is in CODING state; override to APPROVED is illegal
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.CODING.value)

            with self.assertRaises(ValueError) as ctx:
                orch.resolve_override(t_id, "APPROVED", note="Attempt illegal transition")
            self.assertIn("Illegal state transition", str(ctx.exception))

            # Verify no orphan vote_result.json was written to disk
            vote_file = Path(tmpdir) / ".macao" / "vote_result.json"
            self.assertFalse(vote_file.exists())

            # Verify no vote_result was registered in artifacts table
            artifacts = orch.store.list_artifacts(t_id)
            vote_artifacts = [a for a in artifacts if a.get("kind") == "vote_result"]
            self.assertEqual(vote_artifacts, [])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_retry_review_override_full_recovery_and_consensus(self):
        """P1-NEW-8 / P1-Q3 / Codex P1-1: Verify RETRY_REVIEW voids prior generation timeouts, allowing full consensus recovery when timely approvals are submitted."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "TestUser"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True)
            (Path(tmpdir) / "init.txt").write_text("initial commit\n", encoding="utf-8")
            subprocess.run(["git", "add", "init.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True, capture_output=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, check=True, capture_output=True, text=True).stdout.strip()

            orch = Orchestrator(project_root=tmpdir, config={
                "reviewer_ids": ["codex", "opencode"],
                "min_effective_votes": 2,
                "max_rework_rounds": 3,
                "require_signoff": False
            })

            task = orch.start_task("E9 Retry Recovery Task", "Testing clean recovery after retry")
            t_id = task["task_id"]

            # Dispatch generation 1
            (Path(tmpdir) / ".macao").mkdir(parents=True, exist_ok=True)
            (Path(tmpdir) / ".macao" / ".dev.yml").write_text(f"""version: "1.0"
status: ready_for_review
signal: EXPLICIT
review_round: 1
executor:
  id: claude
  cli: claude
development:
  quality_metrics:
    tests_passed: true
  git:
    latest_commit: "{head}"
""", encoding="utf-8")
            orch.check_development_checkpoint(t_id)
            orch.dispatch_review_requests(t_id)

            # Generation 1: codex approves, opencode times out
            rev_codex = MockAgentAdapter(agent_id="codex", cli_name="codex", role="reviewer")
            rev_codex.simulate_produce_review_manifest(
                project_root=tmpdir,
                checkpoint_ref=head,
                review_round=1,
                vote="YES_APPROVE",
                opinion_status="APPROVED",
                confidence=0.95
            )

            # Generation 1 consensus evaluation with timeout -> HOLDS in CONSENSUS_CHECK
            change1 = orch.collect_and_evaluate_consensus(t_id, configured_reviewers=2, timed_out_reviewers=["opencode"])
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.CONSENSUS_CHECK.value)
            self.assertFalse((Path(tmpdir) / ".macao" / "vote_result.json").exists())

            # Admin triggers RETRY_REVIEW (E9)
            change_retry = orch.resolve_override(t_id, "RETRY_REVIEW", note="Retrying round 1 review with fresh dispatch")
            self.assertEqual(change_retry.to_state, AgentState.WAITING_REVIEW)
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.WAITING_REVIEW.value)

            # Generation 2: Both codex AND opencode submit timely YES_APPROVE manifests
            rev_codex.simulate_produce_review_manifest(
                project_root=tmpdir,
                checkpoint_ref=head,
                review_round=1,
                vote="YES_APPROVE",
                opinion_status="APPROVED",
                confidence=0.95
            )
            rev_opencode = MockAgentAdapter(agent_id="opencode", cli_name="opencode", role="reviewer")
            rev_opencode.simulate_produce_review_manifest(
                project_root=tmpdir,
                checkpoint_ref=head,
                review_round=1,
                vote="YES_APPROVE",
                opinion_status="APPROVED",
                confidence=0.95
            )

            # Generation 2 consensus evaluation -> MUST NOT ISOLATE OPENCODE, MUST ACHIEVE MERGING
            change2, vdata2 = orch.collect_and_evaluate_consensus(t_id, configured_reviewers=2)
            self.assertIsNotNone(change2)
            self.assertEqual(change2.to_state, AgentState.MERGING)
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.MERGING.value)

            # Assert vote_result.json is written with 2 YES approvals and 0 ABSTAIN
            vote_file = Path(tmpdir) / ".macao" / "vote_result.json"
            self.assertTrue(vote_file.exists())
            with open(vote_file, "r", encoding="utf-8") as f:
                vdata = json.load(f)
            self.assertEqual(vdata["decision"], "APPROVED")
            self.assertEqual(vdata["resolution"], "automatic")
            self.assertEqual(vdata["vote_breakdown"]["approve"], 2)
            self.assertEqual(vdata["vote_breakdown"]["abstain"], 0)

            # Assert no LATE_REVIEW_ISOLATED events were logged in Generation 2
            late_audits = orch.store.get_audit_events_by_type(t_id, "LATE_REVIEW_ISOLATED", review_round=1)
            self.assertEqual(len(late_audits), 0)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_retry_review_override_repeated_timeout_holds(self):
        """P1-NEW-8: Verify that if a reviewer times out AGAIN in the new generation after RETRY_REVIEW, the system correctly records the new timeout and HOLDS."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "TestUser"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True)
            (Path(tmpdir) / "init.txt").write_text("initial commit\n", encoding="utf-8")
            subprocess.run(["git", "add", "init.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True, capture_output=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, check=True, capture_output=True, text=True).stdout.strip()

            orch = Orchestrator(project_root=tmpdir, config={
                "reviewer_ids": ["codex", "opencode"],
                "min_effective_votes": 2,
                "max_rework_rounds": 3,
                "require_signoff": False
            })

            task = orch.start_task("E9 Repeated Timeout Task", "Testing repeated timeout detection")
            t_id = task["task_id"]

            (Path(tmpdir) / ".macao").mkdir(parents=True, exist_ok=True)
            (Path(tmpdir) / ".macao" / ".dev.yml").write_text(f"""version: "1.0"
status: ready_for_review
signal: EXPLICIT
review_round: 1
executor:
  id: claude
  cli: claude
development:
  quality_metrics:
    tests_passed: true
  git:
    latest_commit: "{head}"
""", encoding="utf-8")
            orch.check_development_checkpoint(t_id)
            orch.dispatch_review_requests(t_id)

            # Gen 1 timeout -> HOLD -> RETRY_REVIEW
            orch.collect_and_evaluate_consensus(t_id, configured_reviewers=2, timed_out_reviewers=["opencode"])
            orch.resolve_override(t_id, "RETRY_REVIEW", note="Retrying review")

            # Gen 2: codex approves, opencode times out AGAIN in Generation 2
            rev_codex = MockAgentAdapter(agent_id="codex", cli_name="codex", role="reviewer")
            rev_codex.simulate_produce_review_manifest(
                project_root=tmpdir,
                checkpoint_ref=head,
                review_round=1,
                vote="YES_APPROVE",
                opinion_status="APPROVED",
                confidence=0.95
            )

            # Collect consensus with new Generation 2 timeout
            change_gen2 = orch.collect_and_evaluate_consensus(t_id, configured_reviewers=2, timed_out_reviewers=["opencode"])
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.CONSENSUS_CHECK.value)

            # Assert 2 distinct REVIEWER_TIMEOUT_ABSTAIN events exist in total (one per dispatch generation)
            all_timeouts = orch.store.get_audit_events_by_type(t_id, "REVIEWER_TIMEOUT_ABSTAIN", review_round=1)
            self.assertEqual(len(all_timeouts), 2)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_multi_generation_archiving_preserves_gen1_evidence_immutable(self):
        """P1-NEW-9: Verify that across E9 RETRY_REVIEW generations, Gen 1 evidence is NOT overwritten or destroyed."""
        tmpdir = tempfile.mkdtemp()
        try:
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "TestUser"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True)
            (Path(tmpdir) / "init.txt").write_text("initial commit\n", encoding="utf-8")
            subprocess.run(["git", "add", "init.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True, capture_output=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, check=True, capture_output=True, text=True).stdout.strip()

            orch = Orchestrator(project_root=tmpdir, config={"reviewer_ids": ["codex", "opencode"], "require_signoff": False})
            task = orch.start_task("Multi-Gen Archive Task", "Testing non-destructive archiving")
            t_id = task["task_id"]

            (Path(tmpdir) / ".macao").mkdir(parents=True, exist_ok=True)
            (Path(tmpdir) / ".macao" / ".dev.yml").write_text(f"""version: "1.0"
status: ready_for_review
signal: EXPLICIT
review_round: 1
executor:
  id: claude
  cli: claude
development:
  quality_metrics:
    tests_passed: true
  git:
    latest_commit: "{head}"
""", encoding="utf-8")
            orch.check_development_checkpoint(t_id)
            orch.dispatch_review_requests(t_id)

            # Gen 1: codex submits NO_APPROVE with dissent, opencode submits YES_APPROVE
            rev_codex = MockAgentAdapter(agent_id="codex", cli_name="codex", role="reviewer")
            rev_codex.simulate_produce_review_manifest(
                project_root=tmpdir,
                checkpoint_ref=head,
                review_round=1,
                vote="NO_APPROVE",
                opinion_status="REJECTED",
                issues=[{"type": "security", "severity": "critical", "issue": "GEN1-DISSENT"}],
                confidence=0.99
            )
            rev_opencode = MockAgentAdapter(agent_id="opencode", cli_name="opencode", role="reviewer")
            rev_opencode.simulate_produce_review_manifest(
                project_root=tmpdir,
                checkpoint_ref=head,
                review_round=1,
                vote="YES_APPROVE",
                opinion_status="APPROVED",
                issues=[],
                confidence=0.95
            )

            # Evaluate consensus -> 1:1 deadlock -> HOLDS in CONSENSUS_CHECK
            change_hold = orch.collect_and_evaluate_consensus(t_id, configured_reviewers=2)
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.CONSENSUS_CHECK.value)

            # Resolve override with RETRY_REVIEW from CONSENSUS_CHECK -> archives Gen 1 vote_result & review
            orch.resolve_override(t_id, "RETRY_REVIEW", note="Retrying review after dissent")

            # Check Gen 1 archived file content
            archive_dir = Path(tmpdir) / ".macao" / "archive" / head / "r1"
            gen1_files = list(archive_dir.glob("*.review.yml"))
            self.assertGreaterEqual(len(gen1_files), 1)
            gen1_content = (archive_dir / "codex.review.yml").read_text(encoding="utf-8")
            self.assertIn("GEN1-DISSENT", gen1_content)

            # Gen 2: codex and opencode both submit YES_APPROVE in generation 2
            rev_codex.simulate_produce_review_manifest(
                project_root=tmpdir,
                checkpoint_ref=head,
                review_round=1,
                vote="YES_APPROVE",
                opinion_status="APPROVED",
                issues=[],
                confidence=0.95
            )
            rev_opencode.simulate_produce_review_manifest(
                project_root=tmpdir,
                checkpoint_ref=head,
                review_round=1,
                vote="YES_APPROVE",
                opinion_status="APPROVED",
                issues=[],
                confidence=0.95
            )

            # Evaluate consensus -> MERGING -> archives Gen 2
            orch.collect_and_evaluate_consensus(t_id, configured_reviewers=2)

            # Assert Gen 1 dissent was NOT destroyed or overwritten!
            all_archived_reviews = list(archive_dir.rglob("*.review.yml"))
            self.assertGreaterEqual(len(all_archived_reviews), 2)
            dissent_found = any("GEN1-DISSENT" in f.read_text(encoding="utf-8") for f in all_archived_reviews)
            self.assertTrue(dissent_found, "Gen 1 dissent review evidence must be preserved on disk")

            # Assert ARTIFACT_ARCHIVED audit events exist for both generations
            arch_audits = orch.store.get_audit_events_by_type(t_id, "ARTIFACT_ARCHIVED", review_round=1)
            self.assertGreaterEqual(len(arch_audits), 2)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_retry_review_cleans_active_vote_result_file(self):
        """P2-NEW-4: Verify RETRY_REVIEW removes active .macao/vote_result.json so crash reconcile does not revert state."""
        tmpdir = tempfile.mkdtemp()
        try:
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "TestUser"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True)
            (Path(tmpdir) / "init.txt").write_text("initial commit\n", encoding="utf-8")
            subprocess.run(["git", "add", "init.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True, capture_output=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, check=True, capture_output=True, text=True).stdout.strip()

            orch = Orchestrator(project_root=tmpdir, config={"reviewer_ids": ["codex", "opencode"], "require_signoff": False})
            task = orch.start_task("Clean Vote File Task", "Testing active vote_result cleanup")
            t_id = task["task_id"]

            (Path(tmpdir) / ".macao").mkdir(parents=True, exist_ok=True)
            (Path(tmpdir) / ".macao" / ".dev.yml").write_text(f"""version: "1.0"
status: ready_for_review
signal: EXPLICIT
review_round: 1
executor:
  id: claude
  cli: claude
development:
  quality_metrics:
    tests_passed: true
  git:
    latest_commit: "{head}"
""", encoding="utf-8")
            orch.check_development_checkpoint(t_id)
            orch.dispatch_review_requests(t_id)

            # Reviewer times out -> collect_and_evaluate_consensus -> HOLDS in CONSENSUS_CHECK
            orch.collect_and_evaluate_consensus(t_id, configured_reviewers=2, timed_out_reviewers=["opencode"])
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.CONSENSUS_CHECK.value)

            # Override with RETRY_REVIEW from CONSENSUS_CHECK
            orch.resolve_override(t_id, "RETRY_REVIEW", note="Retrying review")

            # Assert .macao/vote_result.json is NOT in active directory
            active_vote = Path(tmpdir) / ".macao" / "vote_result.json"
            self.assertFalse(active_vote.exists())
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_late_review_isolated_audit_is_idempotent(self):
        """P3-NEW-7: Verify that repeated consensus evaluation with a timed out reviewer logs LATE_REVIEW_ISOLATED idempotently."""
        tmpdir = tempfile.mkdtemp()
        try:
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "TestUser"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True)
            (Path(tmpdir) / "init.txt").write_text("initial commit\n", encoding="utf-8")
            subprocess.run(["git", "add", "init.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True, capture_output=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, check=True, capture_output=True, text=True).stdout.strip()

            orch = Orchestrator(project_root=tmpdir, config={"reviewer_ids": ["codex", "opencode"], "require_signoff": False})
            task = orch.start_task("Idempotency Task", "Testing LATE_REVIEW_ISOLATED idempotency")
            t_id = task["task_id"]

            (Path(tmpdir) / ".macao").mkdir(parents=True, exist_ok=True)
            (Path(tmpdir) / ".macao" / ".dev.yml").write_text(f"""version: "1.0"
status: ready_for_review
signal: EXPLICIT
review_round: 1
executor:
  id: claude
  cli: claude
development:
  quality_metrics:
    tests_passed: true
  git:
    latest_commit: "{head}"
""", encoding="utf-8")
            orch.check_development_checkpoint(t_id)
            orch.dispatch_review_requests(t_id)

            # Opencode times out and is recorded
            orch.collect_and_evaluate_consensus(t_id, configured_reviewers=2, timed_out_reviewers=["opencode"])

            # Late manifest arrives
            rev_opencode = MockAgentAdapter(agent_id="opencode", cli_name="opencode", role="reviewer")
            rev_opencode.simulate_produce_review_manifest(
                project_root=tmpdir,
                checkpoint_ref=head,
                review_round=1,
                vote="YES_APPROVE",
                opinion_status="APPROVED",
                confidence=0.95
            )

            # Poll 20 times repeatedly
            for _ in range(20):
                orch.collect_and_evaluate_consensus(t_id, configured_reviewers=2, timed_out_reviewers=["opencode"])

            # Assert exactly 1 LATE_REVIEW_ISOLATED event is recorded (idempotent)
            isolated_audits = orch.store.get_audit_events_by_type(t_id, "LATE_REVIEW_ISOLATED", review_round=1)
            self.assertEqual(len(isolated_audits), 1)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_check_development_checkpoint_validation_fail_closed(self):
        """P1-NEW-11 (Claude) / P1-1 (Codex) / P1-2 (Kimi): Verify check_development_checkpoint strictly validates Schema and fails closed on missing/invalid fields."""
        tmpdir = tempfile.mkdtemp()
        try:
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "TestUser"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True)
            (Path(tmpdir) / "init.txt").write_text("initial commit\n", encoding="utf-8")
            subprocess.run(["git", "add", "init.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True, capture_output=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, check=True, capture_output=True, text=True).stdout.strip()

            orch = Orchestrator(project_root=tmpdir)
            task = orch.start_task("Validation Gate Task", "Testing dev checkpoint validation")
            t_id = task["task_id"]

            (Path(tmpdir) / ".macao").mkdir(parents=True, exist_ok=True)
            dev_path = Path(tmpdir) / ".macao" / ".dev.yml"

            # Case 1: Missing quality_metrics block entirely -> MUST FAIL (return None)
            dev_path.write_text(f"""version: "1.0"
status: ready_for_review
signal: EXPLICIT
review_round: 1
executor:
  id: claude
  cli: claude
development:
  git:
    latest_commit: "{head}"
""", encoding="utf-8")
            self.assertIsNone(orch.check_development_checkpoint(t_id))

            # Case 2: Missing signal field entirely -> MUST FAIL (return None)
            dev_path.write_text(f"""version: "1.0"
status: ready_for_review
review_round: 1
executor:
  id: claude
  cli: claude
development:
  quality_metrics:
    tests_passed: true
  git:
    latest_commit: "{head}"
""", encoding="utf-8")
            self.assertIsNone(orch.check_development_checkpoint(t_id))

            # Case 3: signal is IMPLICIT -> MUST FAIL (return None)
            dev_path.write_text(f"""version: "1.0"
status: ready_for_review
signal: IMPLICIT
review_round: 1
executor:
  id: claude
  cli: claude
development:
  quality_metrics:
    tests_passed: true
  git:
    latest_commit: "{head}"
""", encoding="utf-8")
            self.assertIsNone(orch.check_development_checkpoint(t_id))

            # Case 4: Missing version field entirely -> MUST FAIL (return None)
            dev_path.write_text(f"""status: ready_for_review
signal: EXPLICIT
review_round: 1
executor:
  id: claude
  cli: claude
development:
  quality_metrics:
    tests_passed: true
  git:
    latest_commit: "{head}"
""", encoding="utf-8")
            self.assertIsNone(orch.check_development_checkpoint(t_id))

            # Case 5: Bare minimum (only 4 lines, no schema metadata) -> MUST FAIL (return None)
            dev_path.write_text(f"""status: ready_for_review
review_round: 1
development:
  git:
    latest_commit: "{head}"
""", encoding="utf-8")
            self.assertIsNone(orch.check_development_checkpoint(t_id))

            # Case 6: tests_passed is False and not exempt -> MUST FAIL (return None)
            dev_path.write_text(f"""version: "1.0"
status: ready_for_review
signal: EXPLICIT
review_round: 1
executor:
  id: claude
  cli: claude
development:
  quality_metrics:
    tests_passed: false
    tests_exempt: false
  git:
    latest_commit: "{head}"
""", encoding="utf-8")
            self.assertIsNone(orch.check_development_checkpoint(t_id))

            # Case 7: commit does not exist in git -> MUST FAIL (return None)
            dev_path.write_text(f"""version: "1.0"
status: ready_for_review
signal: EXPLICIT
review_round: 1
executor:
  id: claude
  cli: claude
development:
  quality_metrics:
    tests_passed: true
  git:
    latest_commit: "0000000000000000000000000000000000000000"
""", encoding="utf-8")
            self.assertIsNone(orch.check_development_checkpoint(t_id))

            # Case 8: Valid manifest with tests_exempt: true -> MUST PASS
            dev_path.write_text(f"""version: "1.0"
status: ready_for_review
signal: EXPLICIT
review_round: 1
executor:
  id: claude
  cli: claude
development:
  quality_metrics:
    tests_passed: false
    tests_exempt: true
  git:
    latest_commit: "{head}"
""", encoding="utf-8")
            res_exempt = orch.check_development_checkpoint(t_id)
            self.assertIsNotNone(res_exempt)
            self.assertEqual(res_exempt.to_state, AgentState.READY_FOR_REVIEW)

            # Reset task state back to CODING for next test
            orch.store.update_task_state(t_id, AgentState.CODING)

            # Case 9: Fully valid manifest with tests_passed: true -> MUST PASS
            dev_path.write_text(f"""version: "1.0"
status: ready_for_review
signal: EXPLICIT
review_round: 1
executor:
  id: claude
  cli: claude
development:
  quality_metrics:
    tests_passed: true
  git:
    latest_commit: "{head}"
""", encoding="utf-8")
            res_valid = orch.check_development_checkpoint(t_id)
            self.assertIsNotNone(res_valid)
            self.assertEqual(res_valid.to_state, AgentState.READY_FOR_REVIEW)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
