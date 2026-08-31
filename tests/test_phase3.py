"""Unit and Integration tests for Phase 3 Components (LiveDispatcher, Daemon, Wizard, LiveRunner)."""

import os
import shutil
import subprocess
import unittest
import tempfile
import yaml
from pathlib import Path


from macao.core.types import AgentState, Decision, Vote
from macao.core.schema import SchemaValidator, validate_review_manifest
from macao.workflow.live_dispatcher import ReviewExtractor, LiveAgentDispatcher
from macao.workflow.daemon import OrchestratorDaemon
from macao.workflow.live_runner import LiveWorkflowRunner
from macao.cli.wizard import probe_available_clis, detect_git_context, detect_ci_command, ensure_gitignore_isolation, generate_smart_config


class TestPhase3Engine(unittest.TestCase):

    def test_review_extractor_markdown_fenced_yaml(self):
        """Verify ReviewExtractor successfully parses YAML wrapped in markdown fences."""
        raw_output = """
Here is my review of the changes:
```yaml
version: "1.0"
checkpoint_ref: "4e38ed6a"
review_round: 1
reviewer:
  id: "codex"
  cli: "codex"
vote: "YES_APPROVE"
opinion:
  status: "APPROVED"
  confidence: 0.98
  feedback:
    summary: "Code quality is excellent."
```
Let me know if you need anything else!
"""
        is_val, manifest, err = ReviewExtractor.extract_and_validate(raw_output, "codex", "4e38ed6a", 1)
        self.assertTrue(is_val, f"Extraction failed: {err}")
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest["vote"], "YES_APPROVE")
        self.assertEqual(manifest["opinion"]["status"], "APPROVED")

    def test_review_extractor_self_heals_omitted_metadata(self):
        """Verify ReviewExtractor automatically injects missing baseline fields and harmonizes opinion/vote."""
        raw_output = """
```yaml
opinion:
  status: "APPROVED"
  confidence: 0.90
  feedback:
    summary: "Looks good"
```
"""
        is_val, manifest, err = ReviewExtractor.extract_and_validate(raw_output, "opencode", "abc1234", 2)
        self.assertTrue(is_val, f"Self-healing extraction failed: {err}")
        self.assertEqual(manifest["reviewer"]["id"], "opencode")
        self.assertEqual(manifest["checkpoint_ref"], "abc1234")
        self.assertEqual(manifest["review_round"], 2)
        self.assertEqual(manifest["vote"], "YES_APPROVE")

    def test_review_extractor_rejects_missing_vote_and_status(self):
        """Verify ReviewExtractor strictly fails closed on arbitrary/non-review YAML."""
        non_review_samples = [
            "```yaml\nnote: I ran out of context\n```",
            "```yaml\nmodel: gemini-2.0-pro\ntemperature: 0.2\n```",
            "```yaml\nfoo: 1\n```",
            "```yaml\n{}\n```",
            "This change is UNSAFE and must not be merged."
        ]
        for sample in non_review_samples:
            is_val, manifest, err = ReviewExtractor.extract_and_validate(sample, "codex", "abc1234", 1)
            self.assertFalse(is_val, f"Expected sample to fail extraction: {sample}")
            self.assertIsNone(manifest)

    def test_review_extractor_rejects_mismatched_context(self):
        """Verify ReviewExtractor rejects YAML containing wrong checkpoint_ref, round, or reviewer ID."""
        # 1. Mismatched checkpoint_ref
        mismatched_ref = """
```yaml
checkpoint_ref: "stale-commit-999"
vote: "YES_APPROVE"
opinion:
  status: "APPROVED"
```
"""
        is_val, _, _ = ReviewExtractor.extract_and_validate(mismatched_ref, "codex", "expected-ref-111", 1)
        self.assertFalse(is_val)

        # 2. Mismatched review_round
        mismatched_round = """
```yaml
review_round: 99
vote: "YES_APPROVE"
opinion:
  status: "APPROVED"
```
"""
        is_val, _, _ = ReviewExtractor.extract_and_validate(mismatched_round, "codex", "expected-ref-111", 1)
        self.assertFalse(is_val)

        # 3. Mismatched reviewer ID
        mismatched_reviewer = """
```yaml
reviewer:
  id: "opencode"
vote: "YES_APPROVE"
opinion:
  status: "APPROVED"
```
"""
        is_val, _, _ = ReviewExtractor.extract_and_validate(mismatched_reviewer, "codex", "expected-ref-111", 1)
        self.assertFalse(is_val)

    def test_wizard_probes_and_smart_config(self):
        """Verify setup wizard auto-discovery functions work correctly without raising exceptions."""
        clis = probe_available_clis()
        self.assertIsInstance(clis, list)

        with tempfile.TemporaryDirectory() as tmpdir:
            proj = Path(tmpdir)
            (proj / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
            ci = detect_ci_command(proj)
            self.assertEqual(ci, "pytest -q")

            cfg = generate_smart_config(proj, executor_cli="opencode", executor_model="GLM 5.3 max")
            self.assertEqual(cfg["team"]["executor"]["model"], "GLM 5.3 max")
            self.assertEqual(cfg["merge"]["ci_gate_command"], "pytest -q")

            # Verify .gitignore isolation injection
            added = ensure_gitignore_isolation(proj)
            self.assertTrue(added)
            gi_content = (proj / ".gitignore").read_text(encoding="utf-8")
            self.assertIn(".macao/worktrees/", gi_content)
            self.assertIn(".macao/.reviews/", gi_content)

            # Second call is idempotent
            added_again = ensure_gitignore_isolation(proj)
            self.assertFalse(added_again)

    def test_daemon_scanner_single_tick_idle(self):
        """Verify daemon scanner handles empty/idle state gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            daemon = OrchestratorDaemon(tmpdir)
            res = daemon.scan_once()
            self.assertIsNone(res["active_task"])
            self.assertEqual(res["action_taken"], "NONE")

    def test_daemon_active_task_timeout_degradation(self):
        """Verify daemon scans active WAITING_REVIEW task, identifies timeout, and records ABSTAIN."""
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            proj = Path(tmpdir)
            # Init git repo
            subprocess.run(["git", "init", "-b", "main"], cwd=str(proj), check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=str(proj), check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(proj), check=True)
            (proj / "README.md").write_text("initial", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=str(proj), check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=str(proj), check=True, capture_output=True)

            # Config with 0s timeout
            cfg_yaml = """
project:
  name: "daemon-test"
  repository:
    workspace_path: "."
    remote_name: "origin"
    default_branch: "main"
team:
  executor: { id: "dev", cli: "opencode", adapter: "pty-wrapper" }
  reviewers:
    - { id: "rev1", cli: "opencode", adapter: "pty-wrapper" }
    - { id: "rev2", cli: "codex", adapter: "pty-wrapper" }
timeouts:
  per_reviewer: "0s"
"""
            (proj / "macao.yaml").write_text(cfg_yaml, encoding="utf-8")

            daemon = OrchestratorDaemon(str(proj))
            # Start a task and move to WAITING_REVIEW
            task = daemon.orchestrator.start_task("Timeout Test", "desc")
            t_id = task["task_id"]

            (proj / "code.py").write_text("print(1)", encoding="utf-8")
            subprocess.run(["git", "add", "code.py"], cwd=str(proj), check=True)
            subprocess.run(["git", "commit", "-m", "add code"], cwd=str(proj), check=True, capture_output=True)
            head = daemon.orchestrator.git.get_head_commit()

            (proj / ".macao").mkdir(parents=True, exist_ok=True)
            (proj / ".macao" / ".dev.yml").write_text(yaml.safe_dump({
                "version": "1.0", "status": "ready_for_review", "signal": "EXPLICIT",
                "review_round": 1, "executor": {"id": "dev", "cli": "opencode"},
                "development": {"git": {"latest_commit": head}, "quality_metrics": {"tests_passed": True}}
            }), encoding="utf-8")

            daemon.orchestrator.check_development_checkpoint(t_id)
            daemon.orchestrator.dispatch_review_requests(t_id)

            # Task is now in WAITING_REVIEW
            curr_task = daemon.store.get_task(t_id)
            self.assertEqual(curr_task["state"], AgentState.WAITING_REVIEW.value)

            # Run daemon scanner
            res = daemon.scan_once()
            self.assertEqual(res["action_taken"], "TIMEOUT_DEGRADATION")
            self.assertIn("rev1", res["timed_out_reviewers"])
            self.assertIn("rev2", res["timed_out_reviewers"])

            # Verify audit events
            audits = daemon.store.get_audit_events_by_type(t_id, "REVIEWER_TIMEOUT_ABSTAIN")
            self.assertEqual(len(audits), 2)

    def test_review_extractor_last_valid_block_wins(self):
        """Verify ReviewExtractor takes the last valid manifest block when multiple blocks appear in session logs."""
        raw_output = """
Draft thought:
```yaml
version: "1.0"
checkpoint_ref: "abc1234"
review_round: 1
reviewer:
  id: "codex"
  cli: "codex"
vote: "YES_APPROVE"
opinion:
  status: "APPROVED"
```

After reviewing the unit tests, I found a bug. Here is my final review:
```yaml
version: "1.0"
checkpoint_ref: "abc1234"
review_round: 1
reviewer:
  id: "codex"
  cli: "codex"
vote: "NO_APPROVE"
opinion:
  status: "CHANGES_REQUESTED"
  feedback:
    summary: "Found regression in math calculation"
items:
  - issue_id: "codex/BUG-01"
    disposition_class: "BLOCKING"
    severity: "major"
    title: "Math regression"
```
"""
        is_val, manifest, err = ReviewExtractor.extract_and_validate(raw_output, "codex", "abc1234", 1)
        self.assertTrue(is_val, f"Extraction failed: {err}")
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest["vote"], "NO_APPROVE")
        self.assertEqual(manifest["opinion"]["status"], "CHANGES_REQUESTED")

    def test_review_extractor_rejects_contradictory_vote_and_status(self):
        """Verify ReviewExtractor rejects manifests with contradictory vote and status (Fail-Closed)."""
        contradictory_samples = [
            """
```yaml
vote: "NO_APPROVE"
opinion:
  status: "APPROVED"
```
""",
            """
```yaml
vote: "YES_APPROVE"
opinion:
  status: "REJECTED"
```
""",
            """
```yaml
vote: "ABSTAIN"
opinion:
  status: "APPROVED"
```
"""
        ]
        for sample in contradictory_samples:
            is_val, manifest, err = ReviewExtractor.extract_and_validate(sample, "opencode", "abc1234", 1)
            self.assertFalse(is_val, f"Expected contradictory sample to be rejected: {sample}")
            self.assertIsNone(manifest)

    def test_review_extractor_supports_abstain(self):
        """Verify ReviewExtractor cleanly extracts and validates explicit ABSTAIN votes."""
        raw_output = """
```yaml
version: "1.0"
checkpoint_ref: "abc1234"
review_round: 1
reviewer:
  id: "opencode"
  cli: "opencode"
vote: "ABSTAIN"
abstain_reason: "No domain knowledge on this file."
opinion:
  status: "ABSTAINED"
  feedback:
    summary: "No domain knowledge on this file."
```
"""
        is_val, manifest, err = ReviewExtractor.extract_and_validate(raw_output, "opencode", "abc1234", 1)
        self.assertTrue(is_val, f"ABSTAIN extraction failed: {err}")
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest["vote"], "ABSTAIN")
        self.assertEqual(manifest["opinion"]["status"], "ABSTAINED")

    def test_wizard_gitignore_isolation_upgrade(self):
        """Verify .gitignore upgrade correctly appends missing rules to legacy files without duplicates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            proj = Path(tmpdir)
            gi = proj / ".gitignore"
            gi.write_text(".macao/worktrees/\n*.pyc\n", encoding="utf-8")

            added = ensure_gitignore_isolation(proj)
            self.assertTrue(added)

            content = gi.read_text(encoding="utf-8")
            self.assertEqual(content.count(".macao/worktrees/"), 1)
            self.assertIn(".macao/.reviews/", content)
            self.assertIn(".macao/*.db", content)
            self.assertIn(".macao/*.db-journal", content)
            self.assertIn(".macao/*.db-wal", content)
            self.assertIn(".macao/*.db-shm", content)

    def test_live_dispatcher_worktree_mock_execution(self):
        """Verify LiveAgentDispatcher creates isolated worktree, extracts review, and removes worktree."""
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            proj = Path(tmpdir)
            subprocess.run(["git", "init", "-b", "main"], cwd=str(proj), check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=str(proj), check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(proj), check=True)
            (proj / "README.md").write_text("initial", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=str(proj), check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=str(proj), check=True, capture_output=True)
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(proj), text=True).strip()

            dispatcher = LiveAgentDispatcher(str(proj))
            r_cfg = {"id": "test-mock-rev", "cli": "mock-cli", "mock_vote": "YES_APPROVE"}

            res = dispatcher.dispatch_review_in_worktree(
                reviewer_cfg=r_cfg,
                task_id="task-test-01",
                checkpoint_ref=commit,
                review_round=1,
                diff_context="+ def hello(): pass",
                timeout_sec=5.0
            )
            self.assertEqual(res["status"], "SUCCESS")
            self.assertEqual(res["vote"], "YES_APPROVE")
            manifest_file = Path(res["manifest_path"])
            self.assertTrue(manifest_file.exists())

            # Verify isolated worktree was cleaned up
            wt_path = proj / ".macao" / "worktrees" / "test-mock-rev" / "task-test-01" / "r1"
            self.assertFalse(wt_path.exists())

    def test_manual_override_resolution(self):
        """Verify manual override can unblock a task in CONSENSUS_CHECK to allow merge."""
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            proj = Path(tmpdir)
            subprocess.run(["git", "init", "-b", "main"], cwd=str(proj), check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=str(proj), check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(proj), check=True)
            (proj / "README.md").write_text("initial", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=str(proj), check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=str(proj), check=True, capture_output=True)

            cfg = generate_smart_config(proj)
            cfg["project"]["repository"]["remote_name"] = ""
            from macao.workflow.orchestrator import Orchestrator
            orch = Orchestrator(str(proj), config=cfg)


            task = orch.start_task("Override Test", "Testing manual override", source_branch="feat/test")
            t_id = task["task_id"]

            subprocess.run(["git", "checkout", "-b", "feat/test"], cwd=str(proj), check=True, capture_output=True)
            (proj / "file.txt").write_text("new content", encoding="utf-8")
            subprocess.run(["git", "add", "file.txt"], cwd=str(proj), check=True)
            subprocess.run(["git", "commit", "-m", "feat: file"], cwd=str(proj), check=True, capture_output=True)
            dev_commit = orch.git.get_head_commit()

            (proj / ".macao").mkdir(parents=True, exist_ok=True)
            (proj / ".macao" / ".dev.yml").write_text(yaml.safe_dump({
                "version": "1.0", "status": "ready_for_review", "signal": "EXPLICIT",
                "review_round": 1, "executor": {"id": "dev", "cli": "opencode"},
                "development": {"git": {"latest_commit": dev_commit}, "quality_metrics": {"tests_passed": True}}
            }), encoding="utf-8")

            orch.check_development_checkpoint(t_id)
            orch.dispatch_review_requests(t_id)

            # Force transition to CONSENSUS_CHECK with DEADLOCK (1 YES, 1 NO, 1 Timeout ABSTAIN)
            reviews_dir = proj / ".macao" / ".reviews"
            reviews_dir.mkdir(parents=True, exist_ok=True)
            (reviews_dir / "cursor-rev.review.yml").write_text(yaml.safe_dump({
                "version": "1.0", "checkpoint_ref": dev_commit, "review_round": 1,
                "reviewer": {"id": "cursor-rev", "cli": "agent"},
                "vote": "YES_APPROVE", "opinion": {"status": "APPROVED", "feedback": {"summary": "Approved"}}
            }), encoding="utf-8")
            (reviews_dir / "claude-rev.review.yml").write_text(yaml.safe_dump({
                "version": "1.0", "checkpoint_ref": dev_commit, "review_round": 1,
                "reviewer": {"id": "claude-rev", "cli": "claude-code"},
                "vote": "NO_APPROVE", "opinion": {"status": "CHANGES_REQUESTED", "feedback": {"summary": "Need changes"}}
            }), encoding="utf-8")

            change_cons, vdata = orch.collect_and_evaluate_consensus(
                t_id,
                configured_reviewers=3,
                timed_out_reviewers=["agy-rev"]
            )
            # DEADLOCK holds in CONSENSUS_CHECK without auto-transition
            self.assertIsNone(change_cons)
            self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.CONSENSUS_CHECK.value)

            # Manual human override approval from CONSENSUS_CHECK HOLD
            override_change = orch.resolve_override(
                task_id=t_id,
                choice="APPROVED",
                note="Manual architectural override approved."
            )
            self.assertIsNotNone(override_change)
            self.assertEqual(override_change.to_state, AgentState.MERGING)




            # Operator signs off merge
            orch.store.log_audit_event(t_id, "HUMAN_MERGE_APPROVED", {
                "checkpoint_ref": dev_commit,
                "signer": "lead-architect",
                "note": "Architect signoff"
            })

            # Merge and complete
            subprocess.run(["git", "checkout", "main"], cwd=str(proj), check=True, capture_output=True)
            merge_ok, merge_msg, final_change = orch.execute_merge(t_id)
            self.assertTrue(merge_ok, f"Merge failed: {merge_msg}")
            self.assertEqual(final_change.to_state, AgentState.DONE)

    def test_live_workflow_runner_end_to_end_cycle(self):
        """Verify Phase 3 LiveWorkflowRunner executes complete lifecycle cleanly."""
        runner = LiveWorkflowRunner()
        try:
            res = runner.run_live_cycle()
            self.assertEqual(res["status"], "PASS")
            self.assertEqual(res["final_state"], AgentState.DONE.value)
            self.assertEqual(len(res["steps"]), 7)
            self.assertGreater(res["archived_count"], 0)
        finally:
            runner.cleanup()

    def test_review_extractor_rejects_contradictory_final_block_even_if_first_valid(self):

        """Codex P1-4: Verify ReviewExtractor strictly fails closed if the final block has a contradiction, even if an earlier block was valid."""
        log_with_valid_then_contradictory = """
Here is an initial draft:
```yaml
version: "1.0"
review_round: 1
checkpoint_ref: "365185eb24650b7a1c2d3e4f5a6b7c8d9e0f1a2b"
reviewer:
  id: "claude-rev"
vote: "YES_APPROVE"
opinion:
  status: "APPROVED"
```

Wait, after checking the test failures, here is my final decision:
```yaml
version: "1.0"
review_round: 1
checkpoint_ref: "365185eb24650b7a1c2d3e4f5a6b7c8d9e0f1a2b"
reviewer:
  id: "claude-rev"
vote: "NO_APPROVE"
opinion:
  status: "APPROVED"
```
"""
        ok, res, err = ReviewExtractor.extract_and_validate(
            log_with_valid_then_contradictory,
            agent_id="claude-rev",
            checkpoint_ref="365185eb24650b7a1c2d3e4f5a6b7c8d9e0f1a2b",
            review_round=1
        )
        self.assertFalse(ok)
        self.assertIsNone(res)
        self.assertIn("Contradictory vote", str(err))

    def test_review_extractor_rejects_short_and_invalid_checkpoint_prefix(self):
        """Claude P2-F-1: Verify ReviewExtractor rejects short (<7 chars) or non-matching checkpoint prefix."""
        full_ref = "365185eb24650b7a1c2d3e4f5a6b7c8d9e0f1a2b"

        # 1 char prefix: Rejected
        log_1_char = f'vote: YES_APPROVE\nopinion:\n  status: APPROVED\ncheckpoint_ref: "3"\n'
        ok, _, _ = ReviewExtractor.extract_and_validate(log_1_char, "claude-rev", full_ref, 1)
        self.assertFalse(ok)

        # 2 char prefix: Rejected
        log_2_char = f'vote: YES_APPROVE\nopinion:\n  status: APPROVED\ncheckpoint_ref: "36"\n'
        ok, _, _ = ReviewExtractor.extract_and_validate(log_2_char, "claude-rev", full_ref, 1)
        self.assertFalse(ok)

        # Mismatched prefix: Rejected
        log_mismatch = f'vote: YES_APPROVE\nopinion:\n  status: APPROVED\ncheckpoint_ref: "deadbeef"\n'
        ok, _, _ = ReviewExtractor.extract_and_validate(log_mismatch, "claude-rev", full_ref, 1)
        self.assertFalse(ok)

        # Valid 8-char Git short SHA prefix: Accepted
        log_valid_short = f'vote: YES_APPROVE\nopinion:\n  status: APPROVED\ncheckpoint_ref: "365185eb"\n'
        ok, doc, _ = ReviewExtractor.extract_and_validate(log_valid_short, "claude-rev", full_ref, 1)
        self.assertTrue(ok)
        self.assertEqual(doc["checkpoint_ref"], full_ref)

    def test_cli_manual_takeover_ops_walkthrough(self):
        """Claude §六 R1 / Grok P1-1: Verify full CLI blackbox manual takeover walkthrough via subprocess."""
        tmpdir = tempfile.mkdtemp()
        try:
            # 1. Initialize git repository
            subprocess.run(["git", "init", "-b", "main"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Tester"], cwd=tmpdir, check=True)
            subprocess.run(["git", "config", "user.email", "test@macao.dev"], cwd=tmpdir, check=True)
            (Path(tmpdir) / "README.md").write_text("# OPS Test\n")
            subprocess.run(["git", "add", "README.md"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, capture_output=True, text=True, check=True).stdout.strip()

            # 2. Write valid macao.yaml with 0s reviewer timeout
            cfg_content = f"""project:
  name: ops-project
  repository:
    workspace_path: .
    remote_name: origin
    default_branch: main
team:


  executor:
    id: opencode-dev
    cli: opencode
    adapter: pty-wrapper
  reviewers:
    - id: rev-1
      cli: mock-cli
      adapter: pty-wrapper
    - id: rev-2
      cli: mock-cli
      adapter: pty-wrapper
    - id: rev-3
      cli: mock-cli
      adapter: pty-wrapper

policy:
  consensus_rule: 2/3_majority
  min_effective_votes: 2
  max_rework_rounds: 3
merge:
  strategy: ff_only
  require_human_signoff: true
timeouts:
  development: 2h
  checkpoint_validation: 1m
  review_request: 30m
  per_reviewer: 0s
  consensus_check: 1m
security:
  allowed_clis:
    - opencode
    - mock-cli
"""
            (Path(tmpdir) / "macao.yaml").write_text(cfg_content, encoding="utf-8")

            # 3. Create task via Orchestrator / state store in repo
            from macao.workflow.orchestrator import Orchestrator
            orch = Orchestrator(tmpdir)
            task = orch.start_task("OPS Task", "Testing manual takeover CLI walkthrough")
            t_id = task["task_id"]

            # Development commit on branch
            subprocess.run(["git", "checkout", "-b", "feature/ops"], cwd=tmpdir, check=True, capture_output=True)
            (Path(tmpdir) / "ops.txt").write_text("ops data\n")
            subprocess.run(["git", "add", "ops.txt"], cwd=tmpdir, check=True)
            subprocess.run(["git", "commit", "-m", "feat: ops commit"], cwd=tmpdir, check=True)
            dev_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmpdir, capture_output=True, text=True, check=True).stdout.strip()

            (Path(tmpdir) / ".macao").mkdir(parents=True, exist_ok=True)
            (Path(tmpdir) / ".macao" / ".dev.yml").write_text(f"""version: "1.0"
status: ready_for_review
signal: EXPLICIT
review_round: 1
executor:
  id: opencode-dev
  cli: opencode
development:
  quality_metrics:
    tests_passed: true
  git:
    latest_commit: "{dev_commit}"
""", encoding="utf-8")
            orch.check_development_checkpoint(t_id)
            orch.dispatch_review_requests(t_id)

            # Submit 1 approval and 1 rejection; reviewer 3 does not submit (times out)
            rev_dir = Path(tmpdir) / ".macao" / ".reviews"
            rev_dir.mkdir(parents=True, exist_ok=True)
            (rev_dir / "rev-1.review.yml").write_text(f"""version: "1.0"
review_round: 1
checkpoint_ref: "{dev_commit}"
reviewer:
  id: rev-1
vote: YES_APPROVE
opinion:
  status: APPROVED
""", encoding="utf-8")

            (rev_dir / "rev-2.review.yml").write_text(f"""version: "1.0"
review_round: 1
checkpoint_ref: "{dev_commit}"
reviewer:
  id: rev-2
vote: NO_APPROVE
opinion:
  status: CHANGES_REQUESTED
""", encoding="utf-8")

            env = dict(os.environ)
            src_dir = str(Path(__file__).resolve().parent.parent / "src")
            env["PYTHONPATH"] = src_dir + (f":{env['PYTHONPATH']}" if "PYTHONPATH" in env else "")


            # 4. CLI: Run daemon --once (Detects timeout, evaluates 1 Yes + 1 No + 1 Timeout Abstain -> DEADLOCK HOLD in CONSENSUS_CHECK)
            res_daemon = subprocess.run(
                ["python3", "-m", "macao.cli.main", "daemon", "--once"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                env=env
            )
            self.assertEqual(res_daemon.returncode, 0, f"daemon --once failed: {res_daemon.stderr}")

            # 5. CLI: Check status shows CONSENSUS_CHECK
            res_status = subprocess.run(
                ["python3", "-m", "macao.cli.main", "status"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                env=env
            )
            self.assertEqual(res_status.returncode, 0)
            self.assertIn("CONSENSUS_CHECK", res_status.stdout)

            # 6. CLI: Run override resolve --choice APPROVED
            res_override = subprocess.run(
                ["python3", "-m", "macao.cli.main", "override", "resolve", "--choice", "APPROVED", "--note", "Resolved by lead operator"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                env=env
            )
            self.assertEqual(res_override.returncode, 0, f"override resolve failed: {res_override.stderr}")
            self.assertIn("Override resolved successfully", res_override.stdout)

            # 7. CLI: Run merge approve
            res_approve = subprocess.run(
                ["python3", "-m", "macao.cli.main", "merge", "approve", "--note", "Lead operator signed off merge"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                env=env
            )
            self.assertEqual(res_approve.returncode, 0, f"merge approve failed: {res_approve.stderr}")
            self.assertIn("Merge signoff recorded", res_approve.stdout)

            # 8. Verify final state transitioned cleanly
            final_task = orch.store.get_task(t_id)
            self.assertEqual(final_task["state"], AgentState.MERGING.value)

        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
