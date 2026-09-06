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
        self.assertIn("MACAO Team & Environment Pre-dispatch Probe", result.output)
        self.assertIn("dev-mock", result.output)
        self.assertIn("rev-mock-1", result.output)
        self.assertIn("Pre-execution Probing Passed", result.output)

    def test_task_create_dry_run(self):
        self._create_mock_config("dry-run-proj")
        result = self.runner.invoke(cli, ["task", "create", "--dry-run"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Dry-run probe passed", result.output)
        # Verify no task database was created
        store = StateStore(); self.assertIsNone(store.get_active_task())

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


if __name__ == "__main__":
    unittest.main()
