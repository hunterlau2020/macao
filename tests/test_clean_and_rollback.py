"""Unit tests for MACAO init, clean, rollback, and gitignore cleanup."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from click.testing import CliRunner

from macao.cli.main import cli
from macao.cli.wizard import ensure_gitignore_isolation, remove_gitignore_isolation


class TestCleanAndRollback(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="macao_test_clean_")
        self.project_root = Path(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_and_init_flag_alias(self):
        """Verify both 'macao init' and 'macao --init' create a valid macao.yaml."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=self.tmpdir):
            res = runner.invoke(cli, ["--init"])
            self.assertEqual(res.exit_code, 0)
            self.assertTrue(Path("macao.yaml").exists())

            # Second invoke should report already exists
            res2 = runner.invoke(cli, ["init"])
            self.assertEqual(res2.exit_code, 0)
            self.assertIn("already exists", res2.output)

    def test_clean_removes_macao_runtime_dir(self):
        """Verify 'macao clean' removes .macao directory."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=self.tmpdir):
            os.makedirs(".macao/logs", exist_ok=True)
            Path(".macao/state.db").touch()
            Path("macao.yaml").write_text("dummy", encoding="utf-8")

            res = runner.invoke(cli, ["clean"])
            self.assertEqual(res.exit_code, 0)
            self.assertFalse(Path(".macao").exists())
            self.assertTrue(Path("macao.yaml").exists())  # Kept without --all

    def test_clean_all_removes_config_and_restores_gitignore(self):
        """Verify 'macao clean --all' removes configuration and cleans .gitignore."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=self.tmpdir):
            os.makedirs(".macao", exist_ok=True)
            Path("macao.yaml").write_text("config: 1", encoding="utf-8")
            gi = Path(".gitignore")
            gi.write_text("dist/\n", encoding="utf-8")
            ensure_gitignore_isolation(Path("."))
            self.assertIn(".macao/worktrees/", gi.read_text(encoding="utf-8"))

            res = runner.invoke(cli, ["clean", "--all"])
            self.assertEqual(res.exit_code, 0)
            self.assertFalse(Path(".macao").exists())
            self.assertFalse(Path("macao.yaml").exists())
            gi_content = gi.read_text(encoding="utf-8")
            self.assertNotIn(".macao/worktrees/", gi_content)
            self.assertIn("dist/", gi_content)

    def test_clean_restore_backup(self):
        """Verify 'macao clean --restore' restores recent macao.yaml.bak file."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=self.tmpdir):
            Path("macao.yaml.bak.123456").write_text("version: backup", encoding="utf-8")
            Path("macao.yaml").write_text("version: broken", encoding="utf-8")

            res = runner.invoke(cli, ["clean", "--restore"])
            self.assertEqual(res.exit_code, 0)
            self.assertEqual(Path("macao.yaml").read_text(encoding="utf-8"), "version: backup")


if __name__ == "__main__":
    unittest.main()
