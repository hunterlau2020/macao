"""Unit tests for MACAO Centralized Logging, Reviewer Session Logs, and Audit CLI."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from click.testing import CliRunner

from macao.utils.logger import get_logger, setup_logger
from macao.storage.store import StateStore
from macao.cli.main import cli
from macao.cli.wizard import ensure_gitignore_isolation
from macao.workflow.live_dispatcher import LiveAgentDispatcher


class TestLoggerAndAudit(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="macao_test_log_")
        self.project_root = Path(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_logger_creates_file_and_writes_messages(self):
        """Verify get_logger writes formatted logs to .macao/logs/macao.log."""
        logger = get_logger("test.component", project_root=str(self.project_root))
        logger.info("Test info message 12345")
        logger.warning("Test warning message 67890")

        log_file = self.project_root / ".macao" / "logs" / "macao.log"
        self.assertTrue(log_file.exists(), "Expected .macao/logs/macao.log to be created")

        content = log_file.read_text(encoding="utf-8")
        self.assertIn("Test info message 12345", content)
        self.assertIn("Test warning message 67890", content)
        self.assertIn("[INFO]", content)
        self.assertIn("[WARNING]", content)

    def test_gitignore_isolation_includes_logs(self):
        """Verify ensure_gitignore_isolation includes .macao/logs/ and .macao/*.log."""
        gi = self.project_root / ".gitignore"
        gi.write_text("node_modules/\n", encoding="utf-8")

        added = ensure_gitignore_isolation(self.project_root)
        self.assertTrue(added)

        content = gi.read_text(encoding="utf-8")
        self.assertIn(".macao/logs/", content)
        self.assertIn(".macao/*.log", content)

    def test_audit_cli_command(self):
        """Verify 'macao audit' renders recorded audit events."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=self.tmpdir):
            os.makedirs(".macao", exist_ok=True)
            store = StateStore(".macao/state.db")
            store.create_task("task-audit-1", "Audit Demo Task", "feat/audit")
            store.log_audit_event("task-audit-1", "TEST_EVENT_ONE", {"metric": 42})
            store.log_audit_event("task-audit-1", "TEST_EVENT_TWO", {"status": "ok"})

            res = runner.invoke(cli, ["audit"])
            self.assertEqual(res.exit_code, 0, f"audit command failed: {res.output}")
            self.assertIn("MACAO Audit Events Log", res.output)
            self.assertIn("TEST_EVENT_ONE", res.output)
            self.assertIn("TEST_EVENT_TWO", res.output)

    def test_logs_cli_command(self):
        """Verify 'macao logs' prints log file content."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=self.tmpdir):
            log_dir = Path(".macao/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            (log_dir / "macao.log").write_text("Line 1: system started\nLine 2: task dispatched\n", encoding="utf-8")

            res = runner.invoke(cli, ["logs", "-n", "10"])
            self.assertEqual(res.exit_code, 0, f"logs command failed: {res.output}")
            self.assertIn("Line 1: system started", res.output)
            self.assertIn("Line 2: task dispatched", res.output)

    def test_logs_cli_reviewer_inspection(self):
        """Verify 'macao logs --reviewer' prints specific reviewer log."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=self.tmpdir):
            rev_dir = Path(".macao/logs/reviewers")
            rev_dir.mkdir(parents=True, exist_ok=True)
            (rev_dir / "codex-rev_r1.log").write_text("CODEX RAW OUTPUT: Looks good.\n", encoding="utf-8")

            res = runner.invoke(cli, ["logs", "--reviewer", "codex-rev"])
            self.assertEqual(res.exit_code, 0, f"logs reviewer command failed: {res.output}")
            self.assertIn("CODEX RAW OUTPUT: Looks good.", res.output)


if __name__ == "__main__":
    unittest.main()
