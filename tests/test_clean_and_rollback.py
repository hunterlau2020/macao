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
        self.old_agmsg = os.environ.get("AGMSG_DIR")
        self.test_agmsg = Path(self.tmpdir) / "agmsg"
        self.test_agmsg.mkdir(parents=True, exist_ok=True)
        os.environ["AGMSG_DIR"] = str(self.test_agmsg)

    def tearDown(self):
        if self.old_agmsg is not None:
            os.environ["AGMSG_DIR"] = self.old_agmsg
        else:
            os.environ.pop("AGMSG_DIR", None)
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

    def test_clean_safe_default_preserves_state_db_and_removes_worktrees(self):
        """Verify 'macao clean' (default) preserves .macao/state.db and only removes worktrees."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=self.tmpdir):
            os.makedirs(".macao/logs", exist_ok=True)
            os.makedirs(".macao/worktrees/rev-claude-wt", exist_ok=True)
            Path(".macao/state.db").touch()
            Path("macao.yaml").write_text("dummy", encoding="utf-8")

            res = runner.invoke(cli, ["clean"])
            self.assertEqual(res.exit_code, 0)
            self.assertTrue(Path(".macao").exists())
            self.assertTrue(Path(".macao/state.db").exists())  # Preserved
            self.assertTrue(Path(".macao/logs").exists())      # Preserved
            self.assertFalse(Path(".macao/worktrees/rev-claude-wt").exists())  # Cleaned
            self.assertTrue(Path("macao.yaml").exists())      # Kept without --all

    def test_clean_all_snapshots_and_removes_runtime_and_config(self):
        """Verify 'macao clean --all' creates snapshot backup before removing configuration and cleaning .gitignore."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=self.tmpdir):
            os.makedirs(".macao/logs", exist_ok=True)
            Path(".macao/state.db").write_text("test_data", encoding="utf-8")
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

            # Assert snapshot directory was created
            backups = list(Path(".").glob(".macao.bak.*"))
            self.assertTrue(len(backups) >= 1)
            self.assertTrue((backups[0] / "state.db").exists())

    def test_clean_restore_backup(self):
        """Verify 'macao clean --restore' restores both .macao.bak.* and macao.yaml.bak.* backups."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=self.tmpdir):
            # Create backups
            os.makedirs(".macao.bak.20260907_120000/logs", exist_ok=True)
            Path(".macao.bak.20260907_120000/state.db").write_text("saved_state", encoding="utf-8")
            Path("macao.yaml.bak.20260907_120000").write_text("version: backup", encoding="utf-8")

            res = runner.invoke(cli, ["clean", "--restore"])
            self.assertEqual(res.exit_code, 0)
            self.assertTrue(Path(".macao").exists())
            self.assertEqual(Path(".macao/state.db").read_text(encoding="utf-8"), "saved_state")
            self.assertEqual(Path("macao.yaml").read_text(encoding="utf-8"), "version: backup")

    def test_interactive_init_chinese_comments_and_canonical_naming(self):
        """Verify init uses current directory name, dev-/rev- naming, and Chinese comments."""
        import yaml
        from macao.core.schema import validate_config

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=self.tmpdir):
            proj_dir = Path("my_english_app")
            proj_dir.mkdir()
            
            # Run inside proj_dir
            old_cwd = os.getcwd()
            os.chdir(str(proj_dir))
            try:
                res = runner.invoke(cli, ["init", "--force", "--yes"])
                self.assertEqual(res.exit_code, 0, f"init failed: {res.output}")
                self.assertTrue(Path("macao.yaml").exists())

                content = Path("macao.yaml").read_text(encoding="utf-8")
                # 1. Project name must match directory name
                self.assertIn('name: "my_english_app"', content)
                self.assertNotIn('name: "macao-demo"', content)

                # 2. Chinese comments present
                self.assertIn("# 项目名称", content)
                self.assertIn("# 主开发执行者", content)
                self.assertIn("# 独立审查团", content)
                self.assertIn("# 3. 共识", content)

                # 3. Canonical naming
                cfg = yaml.safe_load(content)
                self.assertTrue(cfg["team"]["executor"]["id"].startswith("dev-"), f"Expected dev- prefix, got {cfg['team']['executor']['id']}")
                for rev in cfg["team"]["reviewers"]:
                    self.assertTrue(rev["id"].startswith("rev-"), f"Expected rev- prefix, got {rev['id']}")

                # 4. Valid Draft-07 Schema
                is_val, err = validate_config(cfg)
                self.assertTrue(is_val, f"Schema validation error: {err}")
            finally:
                os.chdir(old_cwd)

    def test_git_context_detection_and_logging_options(self):
        """Verify Git context detection handles null remote and logging flags work."""
        from macao.cli.wizard import detect_git_context

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=self.tmpdir):
            proj_dir = Path("pure_local_repo")
            proj_dir.mkdir()

            # Detect git context on non-git dir
            ctx = detect_git_context(proj_dir)
            self.assertEqual(ctx["branch"], "main")
            self.assertIsNone(ctx["remote"])

            # Test verbose and log-level flags
            from macao.cli.main import DEFAULT_CONFIG_TEMPLATE
            Path("macao.yaml").write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
            res = runner.invoke(cli, ["--log-level", "DEBUG", "doctor"])
            self.assertEqual(res.exit_code, 0)
            self.assertEqual(os.environ.get("MACAO_LOG_LEVEL"), "DEBUG")

            res_v = runner.invoke(cli, ["-v", "doctor"])
            self.assertEqual(res_v.exit_code, 0)
            self.assertEqual(os.environ.get("MACAO_LOG_CONSOLE"), "1")

            # Test macao logs -r list and -e list
            res_logs = runner.invoke(cli, ["logs", "-r", "list"])
            self.assertEqual(res_logs.exit_code, 0)
            self.assertIn("No reviewer session logs", res_logs.output)

            res_exec = runner.invoke(cli, ["logs", "-e", "list"])
            self.assertEqual(res_exec.exit_code, 0)
            self.assertIn("No executor session logs", res_exec.output)

    def test_reviewer_selection_parsing_and_4_reviewers_flow(self):
        """Verify parse_reviewer_selection handles various formats and interactive 4-reviewer selection."""
        from macao.cli.wizard import parse_reviewer_selection
        import yaml

        candidates = [
            {"id": "rev-opencode", "cli": "opencode"},
            {"id": "rev-agy", "cli": "agy"},
            {"id": "rev-cursor", "cli": "agent"},
            {"id": "rev-codex", "cli": "codex"},
            {"id": "rev-kimi", "cli": "kimi"},
        ]

        # 1. Shorthand count '4'
        self.assertEqual(len(parse_reviewer_selection("4", candidates)), 4)
        self.assertEqual(len(parse_reviewer_selection("前4位", candidates)), 4)

        # 2. Chinese comma and dunhao
        self.assertEqual(len(parse_reviewer_selection("1，2，3，4", candidates)), 4)
        self.assertEqual(len(parse_reviewer_selection("1、2、3、4", candidates)), 4)

        # 3. Ranges
        self.assertEqual(len(parse_reviewer_selection("1-4", candidates)), 4)
        self.assertEqual(len(parse_reviewer_selection("1~4", candidates)), 4)

        # 4. CLI names
        self.assertEqual(len(parse_reviewer_selection("opencode, agy, cursor, codex", candidates)), 4)

        # 5. Full interactive init selecting 4 reviewers
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=self.tmpdir):
            proj_dir = Path("my_app_4rev")
            proj_dir.mkdir()
            old_cwd = os.getcwd()
            os.chdir(str(proj_dir))
            try:
                # Provide inputs:
                # 1. Project name: enter (default)
                # 2. Team name: enter (default)
                # 3. AGMSG create choice: enter (default [1]) if agmsg present
                # 4. Executor: enter (default)
                # 5. Reviewers: "1,2,3,4"
                # 6. Git confirm: enter (default)
                res = runner.invoke(cli, ["init", "--force"], input="\n\n\n\n1,2,3,4\n\n")
                self.assertEqual(res.exit_code, 0, f"Init failed: {res.output}")

                content = Path("macao.yaml").read_text(encoding="utf-8")
                cfg = yaml.safe_load(content)
                self.assertEqual(len(cfg["team"]["reviewers"]), 4)
                self.assertEqual(cfg["policy"]["minimum_winning_seats"], 3)
                self.assertEqual(cfg["policy"]["seat_quorum_required"], 3)
                self.assertEqual(cfg["policy"]["weight_quorum_required"], 3)
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()

