"""Comprehensive Unit Tests for 'macao task adopt' (Scenario C / UC-11)."""

import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from click.testing import CliRunner

from macao.cli.main import cli
from macao.storage.store import StateStore
from macao.core.types import AgentState


class TestTaskAdopt(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="macao_test_adopt_"))
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmp_dir)

        # Initialize mock git repository
        import subprocess
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "TestUser"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, capture_output=True)

        readme = self.tmp_dir / "README.md"
        readme.write_text("# Test Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "chore: initial commit"], check=True, capture_output=True)

        # Create valid macao.yaml
        cfg_content = """version: "2.5"
project:
  name: "adopt-test-proj"
  repository:
    workspace_path: "."
    remote_name: "origin"
    default_branch: "main"
team:
  executor:
    id: "opencode-dev"
    cli: "opencode"
    adapter: "pty-wrapper"
  reviewers:
    - id: "rev-claude"
      cli: "claude-code"
      adapter: "pty-wrapper"
      vote_weight: 1
    - id: "rev-codex"
      cli: "codex"
      adapter: "pty-wrapper"
      vote_weight: 1
policy:
  consensus_rule: "weighted_2/3_v1"
  dictator_cap_enabled: true
  minimum_winning_seats: 2
  seat_quorum_required: 2
  weight_quorum_required: 2
"""
        (self.tmp_dir / "macao.yaml").write_text(cfg_content, encoding="utf-8")
        subprocess.run(["git", "add", "macao.yaml"], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "chore: add macao.yaml"], check=True, capture_output=True)
        import macao.storage.db as db_mod
        db_mod._db_manager = None
        self.runner = CliRunner()

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_adopt_dry_run_zero_side_effects(self):
        """Verify task adopt --dry-run previews plan with 100% zero mutations."""
        from macao.utils.git_utils import GitManager
        head_commit = GitManager(".").get_head_commit()

        # Create a pending review request in docs/reviews matching current HEAD
        rev_dir = self.tmp_dir / "docs" / "reviews"
        rev_dir.mkdir(parents=True, exist_ok=True)
        req_file = rev_dir / f"2026-09-07-review-request-{head_commit[:8]}.md"
        req_file.write_text(f"# Review Request for {head_commit[:8]}\n\nBaseline: {head_commit}\n", encoding="utf-8")

        result = self.runner.invoke(cli, ["task", "adopt", "--dry-run"])
        self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
        self.assertIn("MACAO Scenario C In-Flight Task Adoption Plan [DRY-RUN (Preview Only)]", result.output)
        self.assertIn("WAITING_REVIEW", result.output)
        self.assertIn(f"task-adopt-{head_commit[:8]}", result.output)
        self.assertIn("DRY-RUN", result.output)

        # Verify zero side-effects: state.db not created or has no active tasks
        state_db = self.tmp_dir / ".macao" / "state.db"
        if state_db.exists():
            store = StateStore(str(state_db))
            self.assertIsNone(store.get_active_task(), "Active task must not be created in dry-run mode")

    def test_adopt_executes_waiting_review(self):
        """Verify task adopt ingests pending review request into WAITING_REVIEW with formal FSM transition."""
        feat_file = self.tmp_dir / "feat.py"
        feat_file.write_text("print('feat')\n", encoding="utf-8")
        import subprocess
        subprocess.run(["git", "add", "feat.py"], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "feat: feature X"], check=True, capture_output=True)
        from macao.utils.git_utils import GitManager
        feat_commit = GitManager(".").get_head_commit()

        rev_dir = self.tmp_dir / "docs" / "reviews"
        rev_dir.mkdir(parents=True, exist_ok=True)
        req_file = rev_dir / f"2026-09-07-review-request-{feat_commit[:8]}.md"
        req_file.write_text(f"# Feature X Review Request\n\nBaseline: {feat_commit}\n", encoding="utf-8")

        result = self.runner.invoke(cli, ["task", "adopt", "--no-review"])
        self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
        self.assertIn(f"Successfully adopted task 'task-adopt-{feat_commit[:8]}' into state 'WAITING_REVIEW'", result.output)

        store = StateStore(".macao/state.db")
        active = store.get_active_task()
        self.assertIsNotNone(active)
        self.assertEqual(active["task_id"], f"task-adopt-{feat_commit[:8]}")
        self.assertEqual(active["state"], "WAITING_REVIEW")
        self.assertEqual(active["checkpoint_ref"], feat_commit[:8])

        # Verify formal FSM transition audit event is recorded (Codex P1-7bc8d70-01)
        audit_events = store.list_audit_events(task_id=active["task_id"])
        event_types = [e.get("type") for e in audit_events]
        self.assertIn("STATE_TRANSITION_E2_ADOPT", event_types)
        self.assertIn("TASK_ADOPTED", event_types)

    def test_adopt_rejects_nonexistent_baseline_commit(self):
        """UC-11 E1: Verify task adopt fails closed if declared baseline commit does not exist in git."""
        rev_dir = self.tmp_dir / "docs" / "reviews"
        rev_dir.mkdir(parents=True, exist_ok=True)
        req_file = rev_dir / "2026-09-08-review-request-deadbeef.md"
        req_file.write_text("# Review Request\n\nBaseline: deadbeef\n", encoding="utf-8")

        result = self.runner.invoke(cli, ["task", "adopt", "--no-review"])
        self.assertEqual(result.exit_code, 1, f"Expected non-zero exit for nonexistent commit, got: {result.exit_code}")
        self.assertIn("UC-11 E1 Error", result.output)
        self.assertIn("deadbeef", result.output)

        # Verify zero state mutation: no state.db created or no active task
        state_db = self.tmp_dir / ".macao" / "state.db"
        if state_db.exists():
            store = StateStore(str(state_db))
            self.assertIsNone(store.get_active_task())

    def test_adopt_in_flight_coding(self):
        """Verify task adopt ingests uncommitted code changes into CODING state."""
        dirty_file = self.tmp_dir / "dirty.py"
        dirty_file.write_text("x = 1\n", encoding="utf-8")

        # 1. Dry run
        dry_res = self.runner.invoke(cli, ["task", "adopt", "--dry-run"])
        self.assertEqual(dry_res.exit_code, 0)
        self.assertIn("态 1: 在途编码未提审", dry_res.output)
        self.assertIn("CODING", dry_res.output)

        # 2. Actual execution
        exec_res = self.runner.invoke(cli, ["task", "adopt"])
        self.assertEqual(exec_res.exit_code, 0)
        self.assertIn("Successfully adopted task", exec_res.output)
        self.assertIn("CODING", exec_res.output)

        store = StateStore(".macao/state.db")
        active = store.get_active_task()
        self.assertIsNotNone(active)
        self.assertEqual(active["state"], "CODING")

    def test_adopt_clean_idle_noop(self):
        """Verify task adopt on clean workspace without review request exits gracefully."""
        result = self.runner.invoke(cli, ["task", "adopt", "--dry-run"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No in-flight review requests or uncommitted code found to adopt", result.output)

    def test_adopt_force_supersedes_existing_task(self):
        """Verify --force supersedes already active task via E10."""
        (self.tmp_dir / ".macao").mkdir(parents=True, exist_ok=True)
        store = StateStore(".macao/state.db")
        store.create_task("task-old-zombie", "Old Task", "main", "main")
        store.update_task_state("task-old-zombie", AgentState.CODING)

        dirty_file = self.tmp_dir / "new_work.py"
        dirty_file.write_text("y = 2\n", encoding="utf-8")

        # Without --force -> blocked
        res_blocked = self.runner.invoke(cli, ["task", "adopt"])
        self.assertNotEqual(res_blocked.exit_code, 0)
        self.assertIn("Active task 'task-old-zombie' is already running", res_blocked.output)

        # With --force -> cancels old task and creates new one
        res_force = self.runner.invoke(cli, ["task", "adopt", "--force"])
        self.assertEqual(res_force.exit_code, 0)
        self.assertIn("Superseded active task 'task-old-zombie'", res_force.output)

        old_task = store.get_task("task-old-zombie")
        self.assertEqual(old_task["state"], "CANCELLED")

        active = store.get_active_task()
        self.assertIsNotNone(active)
        self.assertNotEqual(active["task_id"], "task-old-zombie")
        self.assertEqual(active["state"], "CODING")


if __name__ == "__main__":
    unittest.main()
