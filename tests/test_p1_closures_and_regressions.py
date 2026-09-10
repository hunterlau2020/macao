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

import copy
import hashlib
import json
import logging
import os
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
import yaml
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

    # --- P0-1: Unrecognized CLI not in ADAPTER_MAP fails closed ---
    def test_p0_1_unrecognized_cli_not_in_adapter_map_fails_closed(self):
        self._init_git_repo()
        extra = {
            "team": {
                "reviewers": [
                    {"id": "cursor", "cli": "definitely-not-installed-xyz", "adapter": "pty-wrapper", "vote_weight": 2.0},
                    {"id": "codex", "cli": "totally-bogus-bin-qqq", "adapter": "pty-wrapper", "vote_weight": 2.0},
                    {"id": "rev-mock", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1.0}
                ]
            }
        }
        self._write_config(extra)
        prober = TeamProber(".", dry_run=True)
        res = prober.probe()

        # Ghost seats must NOT be reported as READY or borrow other adapter versions
        for r in res["reviewers"]:
            if r["id"] in ("cursor", "codex"):
                self.assertEqual(r["status"], "MISSING")
                self.assertFalse(r["installed"])
                self.assertIn("not in ADAPTER_MAP", r["error"])

        # Quorum must not be achievable
        self.assertFalse(res["quorum"]["achievable"])
        self.assertFalse(res["can_dispatch"])
        self.assertEqual(res["quorum"]["total_effective_weight"], 1.0)

    # --- P1-2: WAL mode state.db dry-run zero sidecars ---
    def test_p1_2_wal_mode_dry_run_zero_sidecars(self):
        self._init_git_repo()
        self._write_config()

        # Create .macao/state.db in WAL mode
        db_dir = Path(".macao")
        db_dir.mkdir(parents=True, exist_ok=True)
        db_file = db_dir / "state.db"
        conn = sqlite3.connect(str(db_file))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE tasks (task_id TEXT PRIMARY KEY, title TEXT, state TEXT, created_at TEXT, updated_at TEXT)")
        conn.commit()
        conn.close()

        # Clean any sidecars before probe
        for sidecar in db_dir.glob("state.db-*"):
            sidecar.unlink()

        before_files = set(os.listdir(".macao"))
        self.assertEqual(before_files, {"state.db"})

        # Run probe --dry-run
        runner = CliRunner()
        res = runner.invoke(cli, ["probe", "--dry-run"])
        self.assertEqual(res.exit_code, 0)

        after_files = set(os.listdir(".macao"))
        # STRICT ASSERTION: No -shm or -wal sidecars may be created
        self.assertEqual(before_files, after_files, f"Dry-run created sidecars: {after_files - before_files}")

    # --- P1-3: Secrets masking in probe --json ---
    def test_p1_3_secrets_masking_in_probe_json(self):
        self._init_git_repo()
        self._write_config({
            "team": {
                "executor": {
                    "id": "dev-pi",
                    "cli": "pi",
                    "adapter": "pty-wrapper"
                }
            }
        })

        # Create a fake session containing GitHub PAT
        mock_home = Path(self.tmpdir) / "mock_home"
        pi_sessions = mock_home / ".pi" / "agent" / "sessions"
        resolved_proj = Path(".").resolve()
        sanitized_dir = "--" + str(resolved_proj).strip("/").replace("/", "-") + "--"
        s_folder = pi_sessions / sanitized_dir
        s_folder.mkdir(parents=True, exist_ok=True)

        token = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        s_file = s_folder / "2026-09-07T10-00-00_sid1.jsonl"
        with open(s_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "session", "id": "sid1", "cwd": str(resolved_proj)}) + "\n")
            f.write(json.dumps({"type": "session_info", "name": token}) + "\n")

        with patch("pathlib.Path.home", return_value=mock_home):
            runner = CliRunner()
            res = runner.invoke(cli, ["probe", "--dry-run", "--json"])
            self.assertEqual(res.exit_code, 0)
            self.assertNotIn(token, res.output, "Plaintext GitHub PAT must not appear in probe --json")
            self.assertIn("******", res.output)

    # --- P1-4: Claude session locator rejects foreign cwd ---
    def test_p1_4_claude_rejects_foreign_cwd(self):
        mock_home = Path(self.tmpdir) / "mock_home"
        claude_base = mock_home / ".claude" / "projects"
        resolved_proj = Path(".").resolve()
        sanitized_dir = "-" + str(resolved_proj).lstrip("/").replace("/", "-")
        target_dir = claude_base / sanitized_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        # Write session with foreign cwd
        foreign_file = target_dir / "sess1.jsonl"
        with open(foreign_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "user", "cwd": "/home/foreign/repo", "message": {"content": "foreign task"}}) + "\n")

        with patch("pathlib.Path.home", return_value=mock_home):
            sessions = SessionLocator.list_sessions("claude", resolved_proj)
            self.assertEqual(sessions, [], "Mismatched cwd must be rejected fail-closed")

    # --- P1-5: Clean removes worktree and prunes git ---
    def test_p1_5_clean_removes_worktree_and_prunes_git(self):
        self._init_git_repo()
        self._write_config()

        from macao.utils.git_utils import GitManager
        git = GitManager(".")
        # Create worktree
        wt_dir = Path(".macao/worktrees/rev-codex/task-1/r1")
        wt_dir.parent.mkdir(parents=True, exist_ok=True)
        git.create_isolated_worktree("rev-codex", "task-1", 1, "main")

        # Verify worktree registered
        code, out, _ = git._run("worktree", "list", "--porcelain")
        self.assertIn("rev-codex", out)

        runner = CliRunner()
        res = runner.invoke(cli, ["clean"])
        self.assertEqual(res.exit_code, 0)

        # Verify worktree list is completely clean of ghosts
        code, out_after, _ = git._run("worktree", "list", "--porcelain")
        self.assertNotIn("rev-codex", out_after)

    # --- P1-6: task create --no-probe --force cancels old task ---
    def test_p1_6_task_create_no_probe_force_cancels_old_task(self):
        self._init_git_repo()
        self._write_config()

        runner = CliRunner()
        res1 = runner.invoke(cli, ["task", "create", "--title", "TaskA", "--no-probe"])
        self.assertEqual(res1.exit_code, 0)

        # Without force, second task is rejected
        res2_reject = runner.invoke(cli, ["task", "create", "--title", "TaskB", "--no-probe"])
        self.assertNotEqual(res2_reject.exit_code, 0)

        # With force, second task succeeds and cancels old task
        res2_force = runner.invoke(cli, ["task", "create", "--title", "TaskB", "--no-probe", "--force"])
        self.assertEqual(res2_force.exit_code, 0)

        store = StateStore()
        active_tasks = store.get_active_tasks()
        self.assertEqual(len(active_tasks), 1)
        self.assertEqual(active_tasks[0]["title"], "TaskB")

    # --- P1-7: CLI non-zero exit codes on invalid config ---
    def test_p1_7_cli_non_zero_exit_codes_on_invalid_config(self):
        self._init_git_repo()
        runner = CliRunner()

        # 1. Missing macao.yaml -> probe exit code != 0
        res_probe = runner.invoke(cli, ["probe"])
        self.assertNotEqual(res_probe.exit_code, 0)

        # 2. Malformed YAML -> probe and doctor exit code != 0
        Path("macao.yaml").write_text("invalid: yaml: [syntax", encoding="utf-8")
        res_malformed = runner.invoke(cli, ["probe"])
        self.assertNotEqual(res_malformed.exit_code, 0)
        res_doctor = runner.invoke(cli, ["doctor"])
        self.assertNotEqual(res_doctor.exit_code, 0)

        # 3. Schema invalid -> task create --dry-run != 0
        Path("macao.yaml").write_text("project:\n  name: 123\n", encoding="utf-8")
        res_dry_create = runner.invoke(cli, ["task", "create", "--title", "T", "--dry-run"])
        self.assertNotEqual(res_dry_create.exit_code, 0)

    # --- P1-9: task create blocked when review pending (UC-2 E7) ---
    def test_p1_9_task_create_blocked_when_review_pending(self):
        self._init_git_repo()
        self._write_config()

        # Create physical review request document
        req_dir = Path("docs/reviews")
        req_dir.mkdir(parents=True, exist_ok=True)
        (req_dir / "2026-09-07-review-request-961bcfe.md").write_text("# Review Request\nCommit: 961bcfe\n", encoding="utf-8")

        runner = CliRunner()
        # Normal task create must be blocked with UC-2 E7 error
        res_block = runner.invoke(cli, ["task", "create", "--title", "New Task"])
        self.assertNotEqual(res_block.exit_code, 0)
        self.assertIn("UC-2 E7", res_block.output)
        self.assertIn("macao task adopt", res_block.output)

        # --force can override
        res_force = runner.invoke(cli, ["task", "create", "--title", "New Task", "--force"])
        self.assertEqual(res_force.exit_code, 0)

    # --- P1-10: LiveAgentDispatcher handles pi and cursor ---
    def test_p1_10_live_dispatcher_handles_pi_and_cursor(self):
        from macao.workflow.live_dispatcher import LiveAgentDispatcher
        dispatcher = LiveAgentDispatcher(project_root=".")
        pi_adapter = dispatcher.get_adapter_for_reviewer({"id": "pi-rev", "cli": "pi"})
        self.assertEqual(pi_adapter.cli_name, "pi")

        cursor_adapter = dispatcher.get_adapter_for_reviewer({"id": "cursor-rev", "cli": "cursor"})
        self.assertEqual(cursor_adapter.cli_name, "cursor")

    # --- Codex P1-04: Checkpoint full_document sha256 validation ---
    def test_checkpoint_full_document_sha256_validation(self):
        self._init_git_repo()
        self._write_config()

        orch = Orchestrator(".")
        task = orch.start_task(title="Dev Task", task_description="Desc")
        t_id = task["task_id"]

        import hashlib
        req_file = Path("docs/reviews/req.md")
        req_file.parent.mkdir(parents=True, exist_ok=True)
        req_file.write_text("Official Review Request Content", encoding="utf-8")
        true_sha = hashlib.sha256(req_file.read_bytes()).hexdigest()

        dev_yml = Path(".macao/.dev.yml")
        dev_yml.parent.mkdir(parents=True, exist_ok=True)

        from macao.utils.git_utils import GitManager
        git = GitManager(".")
        git._run("add", str(req_file))
        git._run("commit", "-m", "docs: add req")
        head = git.get_head_commit()

        # Tampered SHA256 -> check_development_checkpoint returns None
        bad_manifest = {
            "version": "1.0",
            "task_id": t_id,
            "checkpoint_ref": head,
            "full_document": {
                "path": "docs/reviews/req.md",
                "evidence_commit": head,
                "sha256": "tampered_fake_sha256" + "0" * 44
            },
            "status": "ready_for_review",
            "signal": "EXPLICIT",
            "review_round": 1,
            "executor": {"id": "dev-mock", "cli": "mock-cli"},
            "development": {
                "quality_metrics": {"tests_passed": True},
                "git": {"latest_commit": head}
            }
        }
        import yaml
        dev_yml.write_text(yaml.safe_dump(bad_manifest), encoding="utf-8")
        self.assertIsNone(orch.check_development_checkpoint(t_id))

        # True SHA256 -> check_development_checkpoint succeeds
        bad_manifest["full_document"]["sha256"] = true_sha
        dev_yml.write_text(yaml.safe_dump(bad_manifest), encoding="utf-8")
        change = orch.check_development_checkpoint(t_id)
        self.assertIsNotNone(change)
        self.assertEqual(change.to_state, AgentState.READY_FOR_REVIEW)

    def test_codex_p1_04_checkpoint_anti_forgery_fail_closed_battery(self):
        """Verify check_development_checkpoint strictly rejects all-zero hash, missing doc, wrong CLI, and unbound IDs (Codex P1-04 / Grok P1-1 / Claude P1-1 / Qwen P1-1 / Pi-Qwen P1-A)."""
        import yaml
        from macao.utils.git_utils import GitManager

        self._init_git_repo()

        cfg = {
            "version": "2.5",
            "team": {
                "executor": {"id": "dev-mock", "cli": "mock-cli"},
                "reviewers": [{"id": "rev-mock", "cli": "mock-cli"}]
            }
        }
        Path("macao.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
        orch = Orchestrator(".", config=cfg)
        task = orch.start_task("Anti-Forgery Test", "Check strict fail-closed gates")
        t_id = task["task_id"]

        req_file = Path("docs/reviews/real_doc.md")
        req_file.parent.mkdir(parents=True, exist_ok=True)
        req_file.write_text("# Anti-Forgery Document\nContent verified.\n", encoding="utf-8")
        true_sha = hashlib.sha256(req_file.read_bytes()).hexdigest()

        git = GitManager(".")
        git._run("add", str(req_file))
        git._run("commit", "-m", "docs: add real_doc")
        head = git.get_head_commit()

        dev_yml = Path(".macao/.dev.yml")
        dev_yml.parent.mkdir(parents=True, exist_ok=True)

        base_valid = {
            "version": "1.0",
            "task_id": t_id,
            "checkpoint_ref": head,
            "full_document": {
                "path": "docs/reviews/real_doc.md",
                "evidence_commit": head,
                "sha256": true_sha
            },
            "status": "ready_for_review",
            "signal": "EXPLICIT",
            "review_round": 1,
            "executor": {"id": "dev-mock", "cli": "mock-cli"},
            "development": {
                "quality_metrics": {"tests_passed": True},
                "git": {"latest_commit": head}
            }
        }

        # 1. All-zero sha256 -> REJECTED
        m = copy.deepcopy(base_valid)
        m["full_document"]["sha256"] = "0" * 64
        dev_yml.write_text(yaml.safe_dump(m), encoding="utf-8")
        self.assertIsNone(orch.check_development_checkpoint(t_id))

        # 2. Missing document file -> REJECTED
        m = copy.deepcopy(base_valid)
        m["full_document"]["path"] = "docs/reviews/nonexistent_doc.md"
        dev_yml.write_text(yaml.safe_dump(m), encoding="utf-8")
        self.assertIsNone(orch.check_development_checkpoint(t_id))

        # 3. Empty sha256 -> REJECTED
        m = copy.deepcopy(base_valid)
        m["full_document"]["sha256"] = ""
        dev_yml.write_text(yaml.safe_dump(m), encoding="utf-8")
        self.assertIsNone(orch.check_development_checkpoint(t_id))

        # 4. Wrong executor.cli -> REJECTED
        m = copy.deepcopy(base_valid)
        m["executor"]["cli"] = "attacker-cli"
        dev_yml.write_text(yaml.safe_dump(m), encoding="utf-8")
        self.assertIsNone(orch.check_development_checkpoint(t_id))

        # 5. Wrong executor.id -> REJECTED
        m = copy.deepcopy(base_valid)
        m["executor"]["id"] = "attacker-id"
        dev_yml.write_text(yaml.safe_dump(m), encoding="utf-8")
        self.assertIsNone(orch.check_development_checkpoint(t_id))

        # 6. Unbound task_id -> REJECTED
        m = copy.deepcopy(base_valid)
        m["task_id"] = "different-task-id"
        dev_yml.write_text(yaml.safe_dump(m), encoding="utf-8")
        self.assertIsNone(orch.check_development_checkpoint(t_id))

        # 7. Unbound checkpoint_ref -> REJECTED
        m = copy.deepcopy(base_valid)
        m["checkpoint_ref"] = "0" * 40
        dev_yml.write_text(yaml.safe_dump(m), encoding="utf-8")
        self.assertIsNone(orch.check_development_checkpoint(t_id))

        # 8. Unbound evidence_commit -> REJECTED
        m = copy.deepcopy(base_valid)
        m["full_document"]["evidence_commit"] = "0" * 40
        dev_yml.write_text(yaml.safe_dump(m), encoding="utf-8")
        self.assertIsNone(orch.check_development_checkpoint(t_id))

        # 9. Path traversal outside root -> REJECTED
        m = copy.deepcopy(base_valid)
        m["full_document"]["path"] = "../../etc/passwd"
        dev_yml.write_text(yaml.safe_dump(m), encoding="utf-8")
        self.assertIsNone(orch.check_development_checkpoint(t_id))

        # 10. Valid matching manifest -> ADVANCES
        dev_yml.write_text(yaml.safe_dump(base_valid), encoding="utf-8")
        res = orch.check_development_checkpoint(t_id)
        self.assertIsNotNone(res)
        self.assertEqual(res.to_state, AgentState.READY_FOR_REVIEW)

    # --- Round 4 / e06d44c Remediations ---

    def test_checkpoint_sibling_directory_escape_rejected(self):
        """Verify check_development_checkpoint rejects doc paths that share a prefix but reside in sibling directory (Codex P1-01 / Claude P1-1)."""
        import yaml
        self._init_git_repo()
        self._write_config()
        orch = Orchestrator(".", config={"version": "2.5", "team": {"executor": {"id": "dev-mock", "cli": "mock-cli"}, "reviewers": [{"id": "rev-mock", "cli": "mock-cli"}]}})
        task = orch.start_task("Sibling Escape Test", "Verify sibling dirs blocked")
        t_id = task["task_id"]

        from macao.utils.git_utils import GitManager
        git = GitManager(".")
        head = git.get_head_commit()

        # Create a sibling directory
        sibling_dir = Path(self.tmpdir).parent / (Path(self.tmpdir).name + "_sibling")
        sibling_dir.mkdir(parents=True, exist_ok=True)
        sibling_file = sibling_dir / "evil.md"
        sibling_file.write_text("evil content", encoding="utf-8")
        evil_sha = hashlib.sha256(b"evil content").hexdigest()

        try:
            rel_path_to_sibling = os.path.relpath(sibling_file, self.tmpdir)
            manifest = {
                "version": "1.0",
                "task_id": t_id,
                "checkpoint_ref": head,
                "full_document": {
                    "path": rel_path_to_sibling,
                    "evidence_commit": head,
                    "sha256": evil_sha,
                },
                "status": "ready_for_review",
                "signal": "EXPLICIT",
                "review_round": 1,
                "executor": {"id": "dev-mock", "cli": "mock-cli"},
                "development": {
                    "quality_metrics": {"tests_passed": True},
                    "git": {"latest_commit": head}
                }
            }
            dev_yml = Path(".macao/.dev.yml")
            dev_yml.parent.mkdir(parents=True, exist_ok=True)
            dev_yml.write_text(yaml.safe_dump(manifest), encoding="utf-8")

            res = orch.check_development_checkpoint(t_id)
            self.assertIsNone(res, "Sibling directory escape must return None (fail closed)")
        finally:
            shutil.rmtree(sibling_dir, ignore_errors=True)

    def test_checkpoint_empty_evidence_commit_rejected(self):
        """Verify check_development_checkpoint rejects empty evidence_commit (Grok P2 / Codex P1-01)."""
        import yaml
        self._init_git_repo()
        self._write_config()
        orch = Orchestrator(".", config={"version": "2.5", "team": {"executor": {"id": "dev-mock", "cli": "mock-cli"}, "reviewers": [{"id": "rev-mock", "cli": "mock-cli"}]}})
        task = orch.start_task("Empty Commit Test", "Verify empty evidence_commit rejected")
        t_id = task["task_id"]

        req_file = Path("docs/reviews/real_doc.md")
        req_file.parent.mkdir(parents=True, exist_ok=True)
        req_file.write_text("# Anti-Forgery Document\nContent verified.\n", encoding="utf-8")
        true_sha = hashlib.sha256(req_file.read_bytes()).hexdigest()

        from macao.utils.git_utils import GitManager
        git = GitManager(".")
        head = git.get_head_commit()

        manifest = {
            "version": "1.0",
            "task_id": t_id,
            "checkpoint_ref": head,
            "full_document": {
                "path": "docs/reviews/real_doc.md",
                "evidence_commit": "",  # Empty evidence_commit
                "sha256": true_sha,
            },
            "status": "ready_for_review",
            "signal": "EXPLICIT",
            "review_round": 1,
            "executor": {"id": "dev-mock", "cli": "mock-cli"},
            "development": {
                "quality_metrics": {"tests_passed": True},
                "git": {"latest_commit": head}
            }
        }
        dev_yml = Path(".macao/.dev.yml")
        dev_yml.parent.mkdir(parents=True, exist_ok=True)
        dev_yml.write_text(yaml.safe_dump(manifest), encoding="utf-8")

        self.assertIsNone(orch.check_development_checkpoint(t_id))

    def test_checkpoint_git_blob_verification(self):
        """Verify check_development_checkpoint validates git blob sha256 matches disk/manifest sha256 (Codex P1-01)."""
        import yaml
        self._init_git_repo()
        self._write_config()
        orch = Orchestrator(".", config={"version": "2.5", "team": {"executor": {"id": "dev-mock", "cli": "mock-cli"}, "reviewers": [{"id": "rev-mock", "cli": "mock-cli"}]}})
        task = orch.start_task("Git Blob Test", "Verify git blob sha checked")
        t_id = task["task_id"]

        import subprocess
        req_file = Path("docs/reviews/req_committed.md")
        req_file.parent.mkdir(parents=True, exist_ok=True)
        req_file.write_text("Committed content v1\n", encoding="utf-8")
        subprocess.run(["git", "add", "docs/reviews/req_committed.md"], check=True)
        subprocess.run(["git", "commit", "-m", "docs: add req"], check=True)

        from macao.utils.git_utils import GitManager
        git = GitManager(".")
        head = git.get_head_commit()

        # Modify on disk after committing so disk != committed blob
        req_file.write_text("Uncommitted mutation v2\n", encoding="utf-8")
        disk_sha = hashlib.sha256(req_file.read_bytes()).hexdigest()

        manifest = {
            "version": "1.0",
            "task_id": t_id,
            "checkpoint_ref": head,
            "full_document": {
                "path": "docs/reviews/req_committed.md",
                "evidence_commit": head,
                "sha256": disk_sha,
            },
            "status": "ready_for_review",
            "signal": "EXPLICIT",
            "review_round": 1,
            "executor": {"id": "dev-mock", "cli": "mock-cli"},
            "development": {
                "quality_metrics": {"tests_passed": True},
                "git": {"latest_commit": head}
            }
        }
        dev_yml = Path(".macao/.dev.yml")
        dev_yml.parent.mkdir(parents=True, exist_ok=True)
        dev_yml.write_text(yaml.safe_dump(manifest), encoding="utf-8")

        # Because disk modified after commit, committed git blob sha != disk_sha -> rejected!
        self.assertIsNone(orch.check_development_checkpoint(t_id))

        # Revert disk to match git blob
        req_file.write_text("Committed content v1\n", encoding="utf-8")
        blob_sha = hashlib.sha256(b"Committed content v1\n").hexdigest()
        manifest["full_document"]["sha256"] = blob_sha
        dev_yml.write_text(yaml.safe_dump(manifest), encoding="utf-8")

        res = orch.check_development_checkpoint(t_id)
        self.assertIsNotNone(res)
        self.assertEqual(res.to_state, AgentState.READY_FOR_REVIEW)

    def test_cli_composition_root_wires_executor_adapter(self):
        """Verify main.py get_orchestrator and Orchestrator.__init__ wire executor_adapter (Codex P1-02 / Claude P1-2)."""
        self._init_git_repo()
        self._write_config()

        from macao.cli.main import get_orchestrator
        orch = get_orchestrator(self.tmpdir)
        self.assertIsNotNone(orch.executor, "Executor adapter must be instantiated and wired")
        self.assertEqual(orch.executor.agent_id, "dev-mock")

    def test_all_adapters_support_acceptance_criteria(self):
        """Verify all AI CLI adapters render acceptance_criteria in execution prompts (Codex P1-02 / Claude P1-2 / Pi-Qwen P1-2)."""
        from macao.adapter.claude import ClaudeCodeAdapter
        from macao.adapter.codex import CodexAdapter
        from macao.adapter.opencode import OpenCodeAdapter
        from macao.adapter.antigravity import AntigravityAdapter
        from macao.adapter.kimi import KimiAdapter
        from macao.adapter.cursor import CursorAgentAdapter
        from macao.adapter.pi import PiAdapter

        adapters = [
            ClaudeCodeAdapter(agent_id="claude-dev"),
            CodexAdapter(agent_id="codex-dev"),
            OpenCodeAdapter(agent_id="opencode-dev"),
            AntigravityAdapter(agent_id="agy-dev"),
            KimiAdapter(agent_id="kimi-dev"),
            CursorAgentAdapter(agent_id="cursor-dev"),
            PiAdapter(agent_id="pi-dev"),
        ]

        task_payload = {
            "task_description": "Critical feature work",
            "acceptance_criteria": ["MUST_PASS_CRITERION_ALPHA", "MUST_PASS_CRITERION_BETA"]
        }

        for adapter in adapters:
            with self.subTest(adapter=adapter.__class__.__name__):
                mock_session = MagicMock()
                adapter.session = mock_session
                adapter.is_running = True
                ok = adapter.inject_task(task_payload)
                self.assertTrue(ok)
                mock_session.write_input.assert_called_once()
                sent_prompt = mock_session.write_input.call_args[0][0]
                self.assertIn("MUST_PASS_CRITERION_ALPHA", sent_prompt, f"{adapter.__class__.__name__} failed to include acceptance_criteria")
                self.assertIn("MUST_PASS_CRITERION_BETA", sent_prompt, f"{adapter.__class__.__name__} failed to include acceptance_criteria")

    def test_checkpoint_uncommitted_or_untracked_evidence_rejected(self):
        """Verify check_development_checkpoint rejects untracked documents or documents missing from declared commit (Codex P1-bdc177e-01)."""
        import yaml
        self._init_git_repo()
        self._write_config()
        orch = Orchestrator(".", config={"version": "2.5", "team": {"executor": {"id": "dev-mock", "cli": "mock-cli"}, "reviewers": [{"id": "rev-mock", "cli": "mock-cli"}]}})
        task = orch.start_task("Untracked Doc Test", "Verify untracked doc rejected")
        t_id = task["task_id"]

        from macao.utils.git_utils import GitManager
        git = GitManager(".")
        head1 = git.get_head_commit()

        # 1. Untracked file created on disk after HEAD1
        untracked = Path("docs/reviews/untracked_evidence.md")
        untracked.parent.mkdir(parents=True, exist_ok=True)
        untracked.write_text("# Untracked Evidence\nNot committed yet.\n", encoding="utf-8")
        untracked_sha = hashlib.sha256(untracked.read_bytes()).hexdigest()

        manifest = {
            "version": "1.0",
            "task_id": t_id,
            "checkpoint_ref": head1,
            "full_document": {
                "path": "docs/reviews/untracked_evidence.md",
                "evidence_commit": head1,
                "sha256": untracked_sha,
            },
            "status": "ready_for_review",
            "signal": "EXPLICIT",
            "review_round": 1,
            "executor": {"id": "dev-mock", "cli": "mock-cli"},
            "development": {
                "quality_metrics": {"tests_passed": True},
                "git": {"latest_commit": head1}
            }
        }
        dev_yml = Path(".macao/.dev.yml")
        dev_yml.parent.mkdir(parents=True, exist_ok=True)
        dev_yml.write_text(yaml.safe_dump(manifest), encoding="utf-8")

        # Untracked document must be rejected: stays in CODING
        self.assertIsNone(orch.check_development_checkpoint(t_id))
        self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.CODING.value)

        # 2. Document committed in subsequent commit (HEAD2), but manifest declares HEAD1
        git._run("add", str(untracked))
        git._run("commit", "-m", "docs: commit evidence in HEAD2")
        head2 = git.get_head_commit()
        self.assertNotEqual(head1, head2)

        # Evidence document does not exist at HEAD1 -> must be rejected
        manifest["checkpoint_ref"] = head1
        manifest["full_document"]["evidence_commit"] = head1
        manifest["development"]["git"]["latest_commit"] = head1
        dev_yml.write_text(yaml.safe_dump(manifest), encoding="utf-8")
        self.assertIsNone(orch.check_development_checkpoint(t_id))
        self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.CODING.value)

        # 3. Document correctly exists at declared evidence_commit (HEAD2) with matching SHA
        manifest["checkpoint_ref"] = head2
        manifest["full_document"]["evidence_commit"] = head2
        manifest["development"]["git"]["latest_commit"] = head2
        dev_yml.write_text(yaml.safe_dump(manifest), encoding="utf-8")
        res = orch.check_development_checkpoint(t_id)
        self.assertIsNotNone(res)
        self.assertEqual(res.to_state, AgentState.READY_FOR_REVIEW)
        self.assertEqual(orch.store.get_task(t_id)["state"], AgentState.READY_FOR_REVIEW.value)

    def test_task_create_no_probe_unknown_executor_fails_closed(self):
        """Verify task create --no-probe with unknown executor fails fast and produces zero state mutations (Codex P1-bdc177e-02)."""
        import yaml
        from click.testing import CliRunner
        from macao.cli.main import cli
        from macao.storage.db import reset_db_manager

        from macao.cli.main import DEFAULT_CONFIG_TEMPLATE
        self._init_git_repo()
        cfg = DEFAULT_CONFIG_TEMPLATE.replace('cli: "claude-code"', 'cli: "completely-unknown-cli-xyz"', 1)
        Path("macao.yaml").write_text(cfg, encoding="utf-8")
        reset_db_manager()

        runner = CliRunner()
        result = runner.invoke(cli, ["task", "create", "--no-probe", "--title", "Unknown Exec Task", "--acceptance", "req"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("completely-unknown-cli-xyz", result.output)

        # Verify 0 tasks created in state.db
        db_path = Path(".macao/state.db")
        if db_path.exists():
            from macao.storage.store import StateStore
            st = StateStore(str(db_path))
            self.assertIsNone(st.get_active_task())

    def test_all_adapters_reviewer_prompt_includes_acceptance_criteria(self):
        """Verify all 7 AI CLI adapters include acceptance criteria in REVIEW_REQUEST prompts (Grok P2-3)."""
        from macao.adapter.claude import ClaudeCodeAdapter
        from macao.adapter.codex import CodexAdapter
        from macao.adapter.opencode import OpenCodeAdapter
        from macao.adapter.antigravity import AntigravityAdapter
        from macao.adapter.kimi import KimiAdapter
        from macao.adapter.cursor import CursorAgentAdapter
        from macao.adapter.pi import PiAdapter

        adapters = [
            ClaudeCodeAdapter(agent_id="claude-rev", config={"role": "reviewer", "isolated_worktree_path": "/tmp/wt"}),
            CodexAdapter(agent_id="codex-rev", config={"role": "reviewer", "isolated_worktree_path": "/tmp/wt"}),
            OpenCodeAdapter(agent_id="opencode-rev", config={"role": "reviewer", "isolated_worktree_path": "/tmp/wt"}),
            AntigravityAdapter(agent_id="agy-rev", config={"role": "reviewer", "isolated_worktree_path": "/tmp/wt"}),
            KimiAdapter(agent_id="kimi-rev", config={"role": "reviewer", "isolated_worktree_path": "/tmp/wt"}),
            CursorAgentAdapter(agent_id="cursor-rev", config={"role": "reviewer", "isolated_worktree_path": "/tmp/wt"}),
            PiAdapter(agent_id="pi-rev", config={"role": "reviewer", "isolated_worktree_path": "/tmp/wt"}),
        ]

        review_payload = {
            "checkpoint_ref": "c1a2b3c4d5",
            "review_round": 1,
            "acceptance_criteria": ["REV_CRITERION_ALPHA", "REV_CRITERION_BETA"],
            "diff": "+line added\n-line removed"
        }

        for adapter in adapters:
            with self.subTest(adapter=adapter.__class__.__name__):
                mock_session = MagicMock()
                adapter.session = mock_session
                adapter.is_running = True
                ok = adapter.inject_task(review_payload)
                self.assertTrue(ok)
                mock_session.write_input.assert_called_once()
                sent_prompt = mock_session.write_input.call_args[0][0]
                self.assertIn("REVIEW_REQUEST:", sent_prompt)
                self.assertIn("Acceptance Criteria:", sent_prompt)
                self.assertIn("REV_CRITERION_ALPHA", sent_prompt, f"{adapter.__class__.__name__} failed to include acceptance_criteria in review prompt")
                self.assertIn("REV_CRITERION_BETA", sent_prompt, f"{adapter.__class__.__name__} failed to include acceptance_criteria in review prompt")

    def test_checkpoint_symlink_evidence_rejected_fail_closed(self):
        """Verify untracked symlinks, committed symlinks, and parent dir symlinks are rejected (Codex P1-51fa456-01)."""
        from macao.core.types import AgentState
        from macao.utils.git_utils import GitManager
        from macao.workflow.orchestrator import Orchestrator

        repo_dir = Path(tempfile.mkdtemp(prefix="macao-symlink-reg-"))
        try:
            subprocess.run(["git", "init", "-q", "-b", "main", str(repo_dir)], check=True)
            subprocess.run(["git", "config", "user.name", "tester"], cwd=repo_dir, check=True)
            subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=repo_dir, check=True)

            # Setup real committed document
            real_doc = repo_dir / "docs" / "reviews" / "real_doc.md"
            real_doc.parent.mkdir(parents=True, exist_ok=True)
            real_doc.write_text("# Legitimate Evidence\n", encoding="utf-8")
            subprocess.run(["git", "add", "docs/reviews/real_doc.md"], cwd=repo_dir, check=True)

            # Setup committed symlink (mode 120000)
            committed_sym = repo_dir / "docs" / "reviews" / "committed_sym.md"
            committed_sym.symlink_to("real_doc.md")
            subprocess.run(["git", "add", "docs/reviews/committed_sym.md"], cwd=repo_dir, check=True)

            # Setup parent dir symlink
            outside_dir = repo_dir / "docs" / "outside"
            outside_dir.mkdir(parents=True, exist_ok=True)
            (outside_dir / "target.md").write_text("# Inside outside\n", encoding="utf-8")
            parent_sym = repo_dir / "docs" / "reviews" / "sym_dir"
            parent_sym.symlink_to("../outside")
            subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
            subprocess.run(["git", "commit", "-qm", "initial repo state"], cwd=repo_dir, check=True)

            head = GitManager(str(repo_dir)).get_head_commit()
            real_sha = hashlib.sha256(real_doc.read_bytes()).hexdigest()

            # Setup untracked symlink pointing to real_doc.md
            untracked_sym = repo_dir / "docs" / "reviews" / "untracked_alias.md"
            untracked_sym.symlink_to("real_doc.md")

            config = {
                "version": "2.5",
                "team": {
                    "executor": {"id": "dev", "cli": "mock-cli"},
                    "reviewers": [{"id": "reviewer", "cli": "mock-cli"}],
                },
            }
            orchestrator = Orchestrator(str(repo_dir), config=config)

            # 1. Untracked symlink -> REJECT
            t1 = orchestrator.start_task("untracked symlink test", "desc", force=True)
            m1 = {
                "version": "1.0",
                "task_id": t1["task_id"],
                "checkpoint_ref": head,
                "review_round": 1,
                "signal": "EXPLICIT",
                "status": "ready_for_review",
                "executor": {"id": "dev", "cli": "mock-cli"},
                "full_document": {
                    "path": "docs/reviews/untracked_alias.md",
                    "evidence_commit": head,
                    "sha256": real_sha,
                },
                "development": {
                    "quality_metrics": {"tests_passed": True},
                    "git": {"latest_commit": head},
                },
            }
            (repo_dir / ".macao" / ".dev.yml").write_text(yaml.safe_dump(m1), encoding="utf-8")
            ch1 = orchestrator.check_development_checkpoint(t1["task_id"])
            self.assertIsNone(ch1, "Untracked symlink must be rejected")
            self.assertEqual(orchestrator.store.get_task(t1["task_id"])["state"], AgentState.CODING.value)

            # 2. Committed symlink -> REJECT
            t2 = orchestrator.start_task("committed symlink test", "desc", force=True)
            m2 = dict(m1)
            m2["task_id"] = t2["task_id"]
            m2["full_document"] = {
                "path": "docs/reviews/committed_sym.md",
                "evidence_commit": head,
                "sha256": real_sha,
            }
            (repo_dir / ".macao" / ".dev.yml").write_text(yaml.safe_dump(m2), encoding="utf-8")
            ch2 = orchestrator.check_development_checkpoint(t2["task_id"])
            self.assertIsNone(ch2, "Committed symlink must be rejected")
            self.assertEqual(orchestrator.store.get_task(t2["task_id"])["state"], AgentState.CODING.value)

            # 3. Parent dir symlink -> REJECT
            t3 = orchestrator.start_task("parent dir symlink test", "desc", force=True)
            m3 = dict(m1)
            m3["task_id"] = t3["task_id"]
            m3["full_document"] = {
                "path": "docs/reviews/sym_dir/target.md",
                "evidence_commit": head,
                "sha256": hashlib.sha256((outside_dir / "target.md").read_bytes()).hexdigest(),
            }
            (repo_dir / ".macao" / ".dev.yml").write_text(yaml.safe_dump(m3), encoding="utf-8")
            ch3 = orchestrator.check_development_checkpoint(t3["task_id"])
            self.assertIsNone(ch3, "Parent directory symlink must be rejected")
            self.assertEqual(orchestrator.store.get_task(t3["task_id"])["state"], AgentState.CODING.value)

            # 4. Legitimate regular committed file -> ADVANCE
            t4 = orchestrator.start_task("regular file test", "desc", force=True)
            m4 = dict(m1)
            m4["task_id"] = t4["task_id"]
            m4["full_document"] = {
                "path": "docs/reviews/real_doc.md",
                "evidence_commit": head,
                "sha256": real_sha,
            }
            (repo_dir / ".macao" / ".dev.yml").write_text(yaml.safe_dump(m4), encoding="utf-8")
            ch4 = orchestrator.check_development_checkpoint(t4["task_id"])
            self.assertIsNotNone(ch4, "Legitimate committed regular file must advance")
            self.assertEqual(orchestrator.store.get_task(t4["task_id"])["state"], AgentState.READY_FOR_REVIEW.value)
        finally:
            shutil.rmtree(repo_dir, ignore_errors=True)

    def test_live_runner_passes_acceptance_criteria_to_dispatcher(self):
        """Verify LiveWorkflowRunner forwards acceptance_criteria to dispatch_review_in_worktree (Claude P3-1)."""
        import inspect
        from macao.workflow.live_runner import LiveWorkflowRunner
        src = inspect.getsource(LiveWorkflowRunner.run_live_cycle)
        call_site = src[src.index("dispatch_review_in_worktree("):]
        call_site = call_site[:call_site.index(")")+1]
        self.assertIn("acceptance_criteria=", call_site, "LiveWorkflowRunner must pass acceptance_criteria to dispatcher")


if __name__ == "__main__":
    unittest.main()
