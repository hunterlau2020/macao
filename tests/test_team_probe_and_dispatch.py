from macao.storage.store import StateStore
"""Unit and integration tests for TeamProber and task dynamic probing (PRD §12, §14)."""

import os
import shutil
import tempfile
import unittest
import yaml
from pathlib import Path
from click.testing import CliRunner

from macao.cli.main import cli, DEFAULT_CONFIG_TEMPLATE
from macao.workflow.prober import TeamProber


class TestTeamProbeAndDispatch(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        self.runner = CliRunner()

        # Init git repo
        os.system("git init -b main > /dev/null 2>&1")
        os.system("git config user.name 'Test' && git config user.email 'test@macao.org'")
        Path("README.md").write_text("Test", encoding="utf-8")
        os.system("git add . && git commit -m 'initial commit' > /dev/null 2>&1")

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_mock_config(self, project_name="mock-project"):
        cfg = yaml.safe_load(DEFAULT_CONFIG_TEMPLATE)
        cfg["project"]["name"] = project_name
        cfg["team"]["executor"] = {
            "id": "dev-mock",
            "cli": "mock-cli",
            "adapter": "pty-wrapper"
        }
        cfg["team"]["reviewers"] = [
            {"id": "rev-mock-1", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1},
            {"id": "rev-mock-2", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1},
            {"id": "rev-mock-3", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1},
        ]
        cfg["policy"]["minimum_winning_seats"] = 2
        cfg["policy"]["seat_quorum_required"] = 2
        cfg["policy"]["weight_quorum_required"] = 2
        Path("macao.yaml").write_text(yaml.dump(cfg), encoding="utf-8")

    def test_prober_missing_config(self):
        prober = TeamProber(".")
        res = prober.probe()
        self.assertFalse(res["valid_config"])
        self.assertFalse(res["can_dispatch"])
        self.assertIn("macao.yaml not found", res["error"])

    def test_prober_with_mock_team(self):
        self._create_mock_config("test-probe-proj")

        prober = TeamProber(".")
        res = prober.probe()
        self.assertTrue(res["valid_config"])
        self.assertEqual(res["project_name"], "test-probe-proj")
        self.assertEqual(res["executor"]["status"], "READY")
        self.assertEqual(len(res["reviewers"]), 3)
        self.assertTrue(res["quorum"]["achievable"])
        self.assertTrue(res["can_dispatch"])
        self.assertIsNone(res["active_task"])

    def test_task_probe_cli(self):
        self._create_mock_config("probe-cli-proj")
        result = self.runner.invoke(cli, ["task", "probe"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("MACAO Team & Environment Dynamic Probe", result.output)
        self.assertIn("dev-mock", result.output)
        self.assertIn("rev-mock-1", result.output)
        self.assertIn("Pre-execution Probing Passed", result.output)

    def test_probe_root_command_dry_run_zero_side_effects(self):
        self._create_mock_config("dry-run-test-proj")
        db_path = Path(".macao/state.db")
        self.assertFalse(db_path.exists())

        result = self.runner.invoke(cli, ["probe", "--dry-run"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("MACAO Team & Environment Dynamic Probe", result.output)
        self.assertIn("DRY-RUN", result.output)
        self.assertIn("Configured Executor", result.output)
        self.assertIn("Configured Reviewers", result.output)

        # STRICT ASSERTION: state.db must NOT exist after --dry-run
        self.assertFalse(db_path.exists(), "State database should NOT be created during --dry-run probe")

    def test_probe_json_output(self):
        self._create_mock_config("json-test-proj")
        import json
        result = self.runner.invoke(cli, ["probe", "--json"])
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertTrue(data["valid_config"])
        self.assertEqual(data["executor"]["id"], "dev-mock")
        self.assertEqual(len(data["reviewers"]), 3)
        self.assertIn("worktree", data["executor"])
        self.assertIn("progress", data["executor"])
        self.assertIn("worktree", data["reviewers"][0])
        self.assertIn("review", data["reviewers"][0])

    def test_probe_executor_and_reviewer_progress_and_worktree(self):
        self._create_mock_config("progress-test-proj")

        # 1. Create a task
        res_create = self.runner.invoke(cli, ["task", "create", "--title", "Feature Alpha"])
        self.assertEqual(res_create.exit_code, 0)

        prober = TeamProber(".")
        res = prober.probe()
        self.assertIsNotNone(res["active_task"])
        self.assertEqual(res["executor"]["progress"], "CODING_IN_PROGRESS")
        self.assertEqual(res["reviewers"][0]["review"]["progress"], "WAITING_DEV")
        self.assertEqual(res["reviewers"][0]["worktree"]["status"], "NOT_SPAWNED")

        # 2. Simulate dev checkpoint submission
        dev_path = Path(".macao/.dev.yml")
        dev_path.parent.mkdir(parents=True, exist_ok=True)
        dev_path.write_text(yaml.dump({
            "version": "1.0",
            "checkpoint_ref": "abc12345",
            "status": "ready_for_review"
        }), encoding="utf-8")

        res2 = prober.probe()
        self.assertEqual(res2["executor"]["progress"], "CHECKPOINT_SUBMITTED")

        # 3. Simulate reviewer worktree and manifest
        active_task_id = res["active_task"]["task_id"]
        rev_wt = Path(".macao/worktrees/rev-mock-1") / active_task_id / "r1"
        rev_wt.mkdir(parents=True, exist_ok=True)
        rev_manifest = Path(".macao/.reviews/rev-mock-1.review.yml")
        rev_manifest.parent.mkdir(parents=True, exist_ok=True)
        rev_manifest.write_text(yaml.dump({
            "version": "1.0",
            "vote": "YES_APPROVE",
            "opinion": {
                "status": "APPROVED",
                "vote": "YES_APPROVE",
                "summary": "Implementation looks solid"
            }
        }), encoding="utf-8")

        res3 = prober.probe()
        r1_probe = next(r for r in res3["reviewers"] if r["id"] == "rev-mock-1")
        self.assertEqual(r1_probe["worktree"]["status"], "ACTIVE")
        self.assertEqual(r1_probe["review"]["progress"], "COMPLETED")
        self.assertEqual(r1_probe["review"]["vote"], "YES_APPROVE")

    def test_task_create_dry_run(self):
        self._create_mock_config("dry-run-proj")
        result = self.runner.invoke(cli, ["task", "create", "--dry-run"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Dry-run probe passed", result.output)
        # Verify no task database was created
        db_path = Path(".macao/state.db")
        self.assertFalse(db_path.exists())

    def test_task_create_blocking_when_active_task_exists(self):
        self._create_mock_config("active-task-proj")

        # 1. First task creation
        res1 = self.runner.invoke(cli, ["task", "create", "--title", "Task 1"])
        self.assertEqual(res1.exit_code, 0)
        self.assertIn("successfully created", res1.output)
        self.assertIn("Assigned Executor", res1.output)

        # 2. Second task creation without force should fail
        res2 = self.runner.invoke(cli, ["task", "create", "--title", "Task 2"])
        self.assertNotEqual(res2.exit_code, 0)
        self.assertIn("Cannot create new task", res2.output)

        # 3. Second task creation with --force should succeed
        res3 = self.runner.invoke(cli, ["task", "create", "--title", "Task 2 Forced", "--force"])
        self.assertEqual(res3.exit_code, 0)
        self.assertIn("successfully created", res3.output)

    def test_session_locator_discovery(self):
        from macao.adapter.session_locator import SessionLocator
        import tempfile
        import json

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # 1. Test unknown cli returns None
            self.assertIsNone(SessionLocator.find_session("unknown-cli", tmp_path))

            # 2. Test agy mock session locator
            mock_home = tmp_path / "mock_home"
            mock_hist = mock_home / ".gemini" / "antigravity-cli" / "history.jsonl"
            mock_hist.parent.mkdir(parents=True, exist_ok=True)
            mock_hist.write_text(
                json.dumps({
                    "workspace": str(tmp_path),
                    "conversationId": "test-conv-12345",
                    "timestamp": 1788700000000,
                    "display": "Implement feature X"
                }) + "\n",
                encoding="utf-8"
            )

            import unittest.mock as mock
            with mock.patch("pathlib.Path.home", return_value=mock_home):
                found = SessionLocator.find_session("agy", tmp_path)
                self.assertIsNotNone(found)
                self.assertEqual(found["session_id"], "test-conv-12345")
                self.assertEqual(found["cli"], "agy")

            # 3. Test claude mock session locator
            claude_proj = mock_home / ".claude" / "projects" / f"-{tmp_path.name}"
            claude_proj.mkdir(parents=True, exist_ok=True)
            sess_file = claude_proj / "session-uuid-999.jsonl"
            sess_file.write_text('{"type": "message"}\n', encoding="utf-8")

            with mock.patch("pathlib.Path.home", return_value=mock_home):
                c_found = SessionLocator.find_session("claude", tmp_path)
                self.assertIsNotNone(c_found)
                self.assertEqual(c_found["session_id"], "session-uuid-999")
                self.assertEqual(c_found["cli"], "claude")

    def test_probe_physical_reviews_and_triplet(self):
        self._create_mock_config("physical-review-proj")
        prober = TeamProber(".")

        # Create docs/reviews with a review request
        rev_dir = Path("docs/reviews")
        rev_dir.mkdir(parents=True, exist_ok=True)
        req_file = rev_dir / "2026-09-07-review-request-test1234.md"
        req_file.write_text("# 评审申请 — 单元测试功能\n\nBaseline: test1234\n", encoding="utf-8")
        import subprocess
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(["git", "commit", "-m", "docs(review): review request test1234"], check=True)

        res = prober.probe()
        self.assertTrue(res["valid_config"])
        self.assertTrue(res["physical_reviews"]["has_pending_request"])
        self.assertEqual(res["physical_reviews"]["latest_request_baseline"], "test1234")
        self.assertEqual(res["executor"]["progress"], "REVIEW_PENDING")
        self.assertIn("last_completed", res["executor"]["progress_triplet"])
        self.assertIn("current_task", res["executor"]["progress_triplet"])
        self.assertIn("next_planned", res["executor"]["progress_triplet"])

        # Reviewers should be marked as AWAITING_REVIEW
        for r in res["reviewers"]:
            self.assertEqual(r["review"]["progress"], "AWAITING_REVIEW")

        # Verify probe log was written
        self.assertIsNotNone(res["log_file"])
        log_path = Path(res["log_file"])
        self.assertTrue(log_path.exists())

        # Test CLI logs --probe
        res_logs = self.runner.invoke(cli, ["logs", "--probe"])
        self.assertEqual(res_logs.exit_code, 0)
        self.assertIn("Probe Audit Log", res_logs.output)


if __name__ == "__main__":
    unittest.main()

