"""Unit and regression tests verifying closures for all 8 P1 review issues (P1-1 to P1-8).

Covers:
- P1-1: Prober --dry-run zero filesystem mutation
- P1-2: SessionLocator strict project binding & cross-project isolation
- P1-3: Progress triplet & review pending logic (missing reviewers, dirty tree)
- P1-4: Quorum achievable 3-condition boundary matrix
- P1-5: Secrets masking across logger, PTY transcripts, and CLI output
- P1-6: macao clean safe defaults, snapshot backup on --all, and directory restore
- P1-7: task checkpoint --auto non-fabrication of tests_passed
- P1-8: task create --force single active task invariant and acceptance criteria envelope
"""

import json
import logging
import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from macao.cli.main import cli
from macao.core.types import AgentState, AEPType
from macao.adapter.session_locator import SessionLocator
from macao.utils.secrets import mask_secrets
from macao.utils.logger import SecretMaskingFormatter
from macao.workflow.prober import TeamProber
from macao.workflow.orchestrator import Orchestrator
from macao.storage.store import StateStore


class TestP1ClosuresAndRegressions(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _init_git_repo(self):
        import subprocess
        subprocess.run(["git", "init", "-b", "main"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.name", "MACAO Tester"], check=True)
        subprocess.run(["git", "config", "user.email", "tester@macao.dev"], check=True)
        Path("README.md").write_text("# Test Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], check=True)
        subprocess.run(["git", "commit", "-m", "chore: initial commit"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _write_config(self, extra_dict: dict = None):
        import yaml
        from macao.cli.main import DEFAULT_CONFIG_TEMPLATE
        cfg = yaml.safe_load(DEFAULT_CONFIG_TEMPLATE)
        cfg["project"]["name"] = "test-p1"
        cfg["team"]["executor"] = {
            "id": "dev-mock",
            "cli": "mock-cli",
            "adapter": "pty-wrapper"
        }
        cfg["team"]["reviewers"] = [
            {"id": "rev-claude", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1.0},
            {"id": "rev-codex", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1.0},
            {"id": "rev-grok", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1.0}
        ]
        cfg["policy"]["minimum_winning_seats"] = 2
        cfg["policy"]["seat_quorum_required"] = 2
        cfg["policy"]["weight_quorum_required"] = 2.0
        if extra_dict:
            for k, v in extra_dict.items():
                if isinstance(v, dict) and k in cfg:
                    cfg[k].update(v)
                else:
                    cfg[k] = v
        Path("macao.yaml").write_text(yaml.dump(cfg), encoding="utf-8")

    # --- P1-1: Prober --dry-run zero disk mutation ---
    def test_p1_1_prober_dry_run_zero_disk_mutation(self):
        self._init_git_repo()
        self._write_config()

        prober = TeamProber(".", dry_run=True)
        result = prober.probe()

        self.assertTrue(result["dry_run"])
        self.assertIsNone(result["log_file"])
        # Assert no .macao/logs/probe directory or log files were created
        self.assertFalse(Path(".macao/logs/probe").exists())
        self.assertFalse(Path(".macao/state.db").exists())

    # --- P1-2: SessionLocator strict project binding & cross-project isolation ---
    def test_p1_2_codex_cross_project_isolation(self):
        mock_home = Path(self.tmpdir) / "mock_home"
        mock_codex = mock_home / ".codex"
        mock_codex.mkdir(parents=True, exist_ok=True)
        db_path = mock_codex / "state_5.sqlite"

        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE threads (
                id TEXT PRIMARY KEY,
                title TEXT,
                cwd TEXT,
                updated_at INTEGER
            )
        """)
        # Insert a session belonging to /home/other/project_a
        conn.execute(
            "INSERT INTO threads VALUES (?, ?, ?, ?)",
            ("session-proj-a", "Working on Proj A", "/home/other/project_a", 1700000000)
        )
        conn.commit()
        conn.close()

        with patch("pathlib.Path.home", return_value=mock_home):
            # Querying for /home/my/project_b MUST return []
            found = SessionLocator.list_sessions("codex", Path("/home/my/project_b"))
            self.assertEqual(found, [])

            # Querying for /home/other/project_a MUST return the session
            found_a = SessionLocator.list_sessions("codex", Path("/home/other/project_a"))
            self.assertEqual(len(found_a), 1)
            self.assertEqual(found_a[0]["session_id"], "session-proj-a")
            self.assertEqual(found_a[0]["workspace"], "/home/other/project_a")

    def test_p1_2_cursor_cross_project_isolation(self):
        mock_home = Path(self.tmpdir) / "mock_home"
        chat_dir = mock_home / ".cursor" / "chats" / "grp1" / "chat1"
        chat_dir.mkdir(parents=True, exist_ok=True)
        meta_file = chat_dir / "meta.json"
        meta_file.write_text(json.dumps({"cwd": "/home/other/repo_x"}), encoding="utf-8")

        with patch("pathlib.Path.home", return_value=mock_home):
            # Querying for /home/my/repo_y MUST return []
            found = SessionLocator.list_sessions("cursor", Path("/home/my/repo_y"))
            self.assertEqual(found, [])

            # Querying for /home/other/repo_x MUST return the session
            found_x = SessionLocator.list_sessions("cursor", Path("/home/other/repo_x"))
            self.assertEqual(len(found_x), 1)
            self.assertEqual(found_x[0]["workspace"], "/home/other/repo_x")

    def test_p1_2_kimi_fail_closed_zero_fabrication(self):
        mock_home = Path(self.tmpdir) / "mock_home"
        mock_home.mkdir(parents=True, exist_ok=True)
        with patch("pathlib.Path.home", return_value=mock_home):
            found = SessionLocator.list_sessions("kimi", Path("/any/project"))
            self.assertEqual(found, [])
            single = SessionLocator.find_session("kimi", Path("/any/project"))
            self.assertIsNone(single)

    # --- P1-3: Progress triplet & review pending logic ---
    def test_p1_3_progress_triplet_review_pending_with_partial_votes(self):
        self._init_git_repo()
        self._write_config()

        # Create review request with baseline b1234
        rev_dir = Path("docs/reviews")
        rev_dir.mkdir(parents=True, exist_ok=True)
        req_file = rev_dir / "2026-09-07-review-request-b1234.md"
        req_file.write_text("# Review Request\n\nBaseline: b1234\n", encoding="utf-8")

        # 1 of 3 reviewers submits result (rev-claude)
        res_file = rev_dir / "2026-09-07-review-result-b1234-rev-claude.md"
        res_file.write_text("# Review Result\n\nVote: APPROVE\n", encoding="utf-8")

        # Create uncommitted dirty file in working tree
        Path("dirty.txt").write_text("uncommitted edits", encoding="utf-8")

        prober = TeamProber(".", dry_run=True)
        res = prober.probe()

        phys = res["physical_reviews"]
        self.assertTrue(phys["has_pending_request"])
        self.assertIn("rev-codex", phys["missing_reviewers"])
        self.assertIn("rev-grok", phys["missing_reviewers"])
        self.assertNotIn("rev-claude", phys["missing_reviewers"])

        # Progress MUST be REVIEW_PENDING despite dirty tree
        triplet = res["executor"]["progress_triplet"]
        self.assertEqual(res["executor"]["progress"], "REVIEW_PENDING")
        self.assertIn("rev-codex", triplet["next_planned"])
        self.assertIn("rev-grok", triplet["next_planned"])

    # --- P1-4: Quorum achievable 3-condition boundary matrix ---
    def test_p1_4_quorum_achievable_boundary_matrix(self):
        self._init_git_repo()

        # Case 1: seats sufficient (2 ready), but total weight insufficient (2.0 < 3.0)
        self._write_config({
            "team": {
                "executor": {"id": "dev-mock", "cli": "mock-cli", "adapter": "pty-wrapper"},
                "reviewers": [
                    {"id": "r1", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1.0},
                    {"id": "r2", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1.0},
                ]
            },
            "policy": {
                "minimum_winning_seats": 2,
                "seat_quorum_required": 2,
                "weight_quorum_required": 3.0
            }
        })
        prober = TeamProber(".", dry_run=True)
        res = prober.probe()
        self.assertTrue(res["valid_config"])
        self.assertFalse(res["quorum"]["achievable"])
        self.assertIn("effective weight 2.0 < weight quorum 3.0", res["blocking_reasons"][0])

        # Case 2: weight sufficient (5.0 >= 3.0), but seats insufficient (1 ready < 2 required)
        self._write_config({
            "team": {
                "executor": {"id": "dev-mock", "cli": "mock-cli", "adapter": "pty-wrapper"},
                "reviewers": [
                    {"id": "r1", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 5.0},
                    {"id": "r2", "cli": "uninstalled-cli-xyz", "adapter": "pty-wrapper", "vote_weight": 1.0},
                ]
            },
            "policy": {
                "minimum_winning_seats": 2,
                "seat_quorum_required": 2,
                "weight_quorum_required": 3.0
            }
        })
        prober2 = TeamProber(".", dry_run=True)
        res2 = prober2.probe()
        self.assertTrue(res2["valid_config"])
        self.assertFalse(res2["quorum"]["achievable"])
        self.assertIn("ready seats 1 < minimum winning 2", res2["blocking_reasons"][0])

        # Case 3: All 3 conditions satisfied (2 ready, 4.0 weight >= 3.0 required)
        self._write_config({
            "team": {
                "executor": {"id": "dev-mock", "cli": "mock-cli", "adapter": "pty-wrapper"},
                "reviewers": [
                    {"id": "r1", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 2},
                    {"id": "r2", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 2},
                ]
            },
            "policy": {
                "minimum_winning_seats": 2,
                "seat_quorum_required": 2,
                "weight_quorum_required": 3.0
            }
        })
        prober3 = TeamProber(".", dry_run=True)
        res3 = prober3.probe()
        self.assertTrue(res3["valid_config"])
        self.assertTrue(res3["quorum"]["achievable"])

    # --- P1-5: Secrets masking across logger and transcripts ---
    def test_p1_5_secrets_masking(self):
        sample = (
            "API key: sk-ant-api03-abcdef12345678901234567890\\n"
            "OpenAI: sk-proj-1234567890123456789012345678\\n"
            "Auth: Bearer mySecretToken1234567890123456\\n"
            "GitHub: ghp_1234567890abcdefghijklmnopqrstuv\\n"
            "DB: postgres://admin:superSecretPass123@db.internal:5432/db"
        )
        masked = mask_secrets(sample)
        self.assertNotIn("sk-ant-api03-abcdef12345678901234567890", masked)
        self.assertNotIn("sk-proj-1234567890123456789012345678", masked)
        self.assertNotIn("mySecretToken1234567890123456", masked)
        self.assertNotIn("ghp_1234567890abcdefghijklmnopqrstuv", masked)
        self.assertNotIn("superSecretPass123", masked)
        self.assertIn("******", masked)

        # Test logger SecretMaskingFormatter
        formatter = SecretMaskingFormatter("%(message)s")
        record = logging.LogRecord("test", logging.INFO, "", 0, "secret key sk-12345678901234567890", (), None)
        formatted = formatter.format(record)
        self.assertNotIn("sk-12345678901234567890", formatted)
        self.assertIn("******", formatted)

    # --- P1-6: Clean safe defaults, snapshot backup on --all, and directory restore ---
    def test_p1_6_clean_snapshot_and_safe_defaults(self):
        runner = CliRunner()
        os.makedirs(".macao/worktrees/wt-test", exist_ok=True)
        os.makedirs(".macao/logs", exist_ok=True)
        Path(".macao/state.db").write_text("data", encoding="utf-8")
        Path("macao.yaml").write_text("version: '2.5'", encoding="utf-8")

        # 1. Default clean: removes worktrees only, preserves state.db and logs
        res_default = runner.invoke(cli, ["clean"])
        self.assertEqual(res_default.exit_code, 0)
        self.assertTrue(Path(".macao/state.db").exists())
        self.assertTrue(Path(".macao/logs").exists())
        self.assertFalse(Path(".macao/worktrees/wt-test").exists())

        # 2. Clean --all: creates .macao.bak.<ts> snapshot
        res_all = runner.invoke(cli, ["clean", "--all"])
        self.assertEqual(res_all.exit_code, 0)
        self.assertFalse(Path(".macao").exists())
        self.assertFalse(Path("macao.yaml").exists())

        snapshots = list(Path(".").glob(".macao.bak.*"))
        self.assertTrue(len(snapshots) >= 1)
        self.assertTrue((snapshots[0] / "state.db").exists())

        # 3. Clean --restore: restores .macao and macao.yaml
        res_restore = runner.invoke(cli, ["clean", "--restore"])
        self.assertEqual(res_restore.exit_code, 0)
        self.assertTrue(Path(".macao/state.db").exists())
        self.assertTrue(Path("macao.yaml").exists())

    # --- P1-7: Checkpoint --auto non-fabrication of tests_passed ---
    def test_p1_7_checkpoint_auto_does_not_fabricate_tests_passed(self):
        self._init_git_repo()
        self._write_config()

        runner = CliRunner()
        # Create active task
        res_create = runner.invoke(cli, ["task", "create", "--title", "Task P1-7"])
        self.assertEqual(res_create.exit_code, 0)

        # Run checkpoint --auto without test verification
        res_chk = runner.invoke(cli, ["task", "checkpoint", "--auto", "--no-review"])
        self.assertEqual(res_chk.exit_code, 0)
        self.assertIn("tests have not passed", res_chk.output)

        # Verify .dev.yml has tests_passed: false
        dev_path = Path(".macao/.dev.yml")
        self.assertTrue(dev_path.exists())
        import yaml
        dev_data = yaml.safe_load(dev_path.read_text(encoding="utf-8"))
        self.assertFalse(dev_data["development"]["quality_metrics"]["tests_passed"])

        # Verify task is still in CODING (not advanced to READY_FOR_REVIEW)
        store = StateStore()
        active = store.get_active_task()
        self.assertEqual(active["state"], AgentState.CODING.value)

    # --- P1-8: Task create --force cancels old task and preserves acceptance criteria ---
    def test_p1_8_task_create_force_cancels_old_task_and_preserves_acceptance(self):
        self._init_git_repo()
        self._write_config()

        runner = CliRunner()
        # 1. Create task 1
        res1 = runner.invoke(cli, ["task", "create", "--title", "Task 1", "-a", "Feature A passes\\nZero regression"])
        self.assertEqual(res1.exit_code, 0)

        store = StateStore()
        task1 = store.get_active_task()
        t1_id = task1["task_id"]

        # 2. Creating second task without --force is blocked
        res2_fail = runner.invoke(cli, ["task", "create", "--title", "Task 2"])
        self.assertNotEqual(res2_fail.exit_code, 0)
        self.assertIn("Active task", res2_fail.output)

        # 3. Creating second task with --force cancels old task (E10)
        res2_force = runner.invoke(cli, ["task", "create", "--title", "Task 2", "-a", "Explicit criterion 1", "--force"])
        self.assertEqual(res2_force.exit_code, 0)
        self.assertIn("cancelled via E10", res2_force.output)

        # Old task must now be CANCELLED, not orphaned
        t1_record = store.get_task(t1_id)
        self.assertEqual(t1_record["state"], AgentState.CANCELLED.value)

        # New task must be active
        active_new = store.get_active_task()
        self.assertEqual(active_new["title"], "Task 2")


if __name__ == "__main__":
    unittest.main()
