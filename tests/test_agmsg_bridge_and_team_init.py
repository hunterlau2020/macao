"""Unit and integration tests for agmsg bridge, team init, reviewer candidate tokens, and vote extraction."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from click.testing import CliRunner

from macao.cli.main import cli
from macao.utils.agmsg_bridge import (
    get_agmsg_dir,
    get_agmsg_teams,
    load_agmsg_team,
    find_team_for_project,
    resolve_agmsg_type,
    map_team_members_by_cli,
    register_agmsg_member,
)
from macao.workflow.prober import TeamProber


class TestAgmsgBridgeAndTeamInit(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="macao_test_agmsg_")
        self.project_root = Path(self.tmpdir) / "project"
        self.project_root.mkdir(parents=True)

        self.old_agmsg = os.environ.get("AGMSG_DIR")
        self.agmsg_dir = Path(self.tmpdir) / "agmsg"
        self.agmsg_dir.mkdir(parents=True)
        os.environ["AGMSG_DIR"] = str(self.agmsg_dir)

    def tearDown(self):
        if self.old_agmsg is not None:
            os.environ["AGMSG_DIR"] = self.old_agmsg
        else:
            os.environ.pop("AGMSG_DIR", None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_agmsg_type_resolution(self):
        """Verify CLI names correctly map to agmsg agent types."""
        self.assertEqual(resolve_agmsg_type("claude-code"), "claude-code")
        self.assertEqual(resolve_agmsg_type("claude"), "claude-code")
        self.assertEqual(resolve_agmsg_type("codex"), "codex")
        self.assertEqual(resolve_agmsg_type("agent"), "cursor")
        self.assertEqual(resolve_agmsg_type("cursor"), "cursor")
        self.assertEqual(resolve_agmsg_type("opencode"), "opencode")
        self.assertEqual(resolve_agmsg_type("pi"), "opencode")
        self.assertEqual(resolve_agmsg_type("agy"), "antigravity")

    def test_team_discovery_and_member_mapping(self):
        """Verify existing agmsg team config is discovered and mapped to CLI members."""
        teams_dir = self.agmsg_dir / "teams" / "demo_team"
        teams_dir.mkdir(parents=True)
        config_json = teams_dir / "config.json"
        team_content = {
            "name": "demo_team",
            "agents": {
                "demo-cc": {
                    "registrations": [
                        {"type": "claude-code", "project": str(self.project_root.resolve())}
                    ]
                },
                "demo-codex": {
                    "registrations": [
                        {"type": "codex", "project": str(self.project_root.resolve())}
                    ]
                }
            }
        }
        config_json.write_text(json.dumps(team_content), encoding="utf-8")

        self.assertEqual(get_agmsg_teams(), ["demo_team"])
        self.assertEqual(find_team_for_project(self.project_root), "demo_team")

        team_data = load_agmsg_team("demo_team")
        self.assertIsNotNone(team_data)
        members_map = map_team_members_by_cli(team_data, self.project_root)
        self.assertEqual(members_map.get("claude-code"), "demo-cc")
        self.assertEqual(members_map.get("codex"), "demo-codex")

    def test_init_with_existing_agmsg_team_replaces_member_ids(self):
        """Verify 'macao init -t <existing>' loads agmsg team and replaces member IDs."""
        teams_dir = self.agmsg_dir / "teams" / "alpha"
        teams_dir.mkdir(parents=True)
        (teams_dir / "config.json").write_text(json.dumps({
            "name": "alpha",
            "agents": {
                "alpha-cc": {"registrations": [{"type": "claude-code", "project": str(self.project_root.resolve())}]},
                "alpha-codex": {"registrations": [{"type": "codex", "project": str(self.project_root.resolve())}]}
            }
        }), encoding="utf-8")

        runner = CliRunner()
        old = os.getcwd()
        os.chdir(str(self.project_root))
        try:
            res = runner.invoke(cli, ["init", "-y", "-t", "alpha"])
            self.assertEqual(res.exit_code, 0, res.output)
            import yaml
            cfg = yaml.safe_load(Path("macao.yaml").read_text(encoding="utf-8"))
            self.assertEqual(cfg["team"]["name"], "alpha")
            self.assertEqual(cfg["team"]["executor"]["id"], "alpha-cc")
            self.assertEqual(cfg["team"]["executor"]["agmsg_member_id"], "alpha-cc")

            rev_ids = [r["id"] for r in cfg["team"]["reviewers"]]
            self.assertIn("alpha-codex", rev_ids)
        finally:
            os.chdir(old)

    def test_init_with_non_existent_team_prompt_exit(self):
        """Verify user choosing [2] when team doesn't exist exits cleanly."""
        runner = CliRunner()
        old = os.getcwd()
        os.chdir(str(self.project_root))
        try:
            res = runner.invoke(cli, ["init"], input="\nnon_existent_team\n2\n")
            self.assertEqual(res.exit_code, 0, res.output)
            self.assertIn("已取消初始化", res.output)
            self.assertFalse(Path("macao.yaml").exists())
        finally:
            os.chdir(old)

    def test_reviewer_candidate_tokens_and_matching(self):
        """Verify candidate tokens extraction and physical review file matching."""
        # rev-cursor running grok
        r_cursor = {"id": "rev-cursor", "cli": "agent", "model": "cursor-grok-3"}
        tokens_cursor = TeamProber._get_reviewer_candidate_tokens(r_cursor)
        self.assertIn("cursor", tokens_cursor)
        self.assertIn("agent", tokens_cursor)
        self.assertIn("grok", tokens_cursor)
        self.assertTrue(TeamProber._matches_reviewer_tokens("2026-09-10-review-result-7040492-grok.md", tokens_cursor))

        # rev-claude running sonnet
        r_claude = {"id": "rev-claude", "cli": "claude-code", "model": "claude-3-5-sonnet"}
        tokens_claude = TeamProber._get_reviewer_candidate_tokens(r_claude)
        self.assertIn("claude", tokens_claude)
        self.assertTrue(TeamProber._matches_reviewer_tokens("2026-09-10-review-result-7040492-claude.md", tokens_claude))

        # rev-codex running gpt
        r_codex = {"id": "rev-codex", "cli": "codex", "model": "gpt-4o"}
        tokens_codex = TeamProber._get_reviewer_candidate_tokens(r_codex)
        self.assertIn("codex", tokens_codex)
        self.assertIn("gpt", tokens_codex)
        self.assertTrue(TeamProber._matches_reviewer_tokens("2026-09-11-review-result-7040492-gpt.md", tokens_codex))

        # rev-pi running qwen
        r_pi = {"id": "rev-pi", "cli": "pi", "model": "zai/glm-5.3:max"}
        tokens_pi = TeamProber._get_reviewer_candidate_tokens(r_pi)
        self.assertIn("pi", tokens_pi)
        self.assertIn("qwen", tokens_pi)
        self.assertIn("glm", tokens_pi)
        self.assertTrue(TeamProber._matches_reviewer_tokens("2026-09-10-review-result-7040492-qwen.md", tokens_pi))

    def test_extract_vote_from_file_english_and_chinese(self):
        """Verify vote extraction from English and Chinese review files."""
        # 1. English approval
        f_en_yes = Path(self.tmpdir) / "res_en_yes.md"
        f_en_yes.write_text("# Review Result\n\nVerdict: YES_APPROVE\nLGTM\n", encoding="utf-8")
        vote, _ = TeamProber._extract_vote_from_file(f_en_yes)
        self.assertEqual(vote, "YES_APPROVE")

        # 2. English rejection
        f_en_no = Path(self.tmpdir) / "res_en_no.md"
        f_en_no.write_text("# Review Result\n\nVerdict: CHANGES_REQUESTED\nPlease fix tests\n", encoding="utf-8")
        vote, _ = TeamProber._extract_vote_from_file(f_en_no)
        self.assertEqual(vote, "NO_APPROVE")

        # 3. Chinese approval
        f_zh_yes = Path(self.tmpdir) / "res_zh_yes.md"
        f_zh_yes.write_text("# 评审结果\n\n> 结论：**通过**（阻断 0 / 应修 0）\n", encoding="utf-8")
        vote, _ = TeamProber._extract_vote_from_file(f_zh_yes)
        self.assertEqual(vote, "YES_APPROVE")

        # 4. Chinese rejection
        f_zh_no = Path(self.tmpdir) / "res_zh_no.md"
        f_zh_no.write_text("# 评审结果\n\n## 结论\n\n**不通过（无 P0/P1；2 项阻断/P3）**。\n", encoding="utf-8")
        vote, _ = TeamProber._extract_vote_from_file(f_zh_no)
        self.assertEqual(vote, "NO_APPROVE")


if __name__ == "__main__":
    unittest.main()
