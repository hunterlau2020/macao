#!/usr/bin/env python3
"""Independent machine validation for MACAO commit 7bc8d70 (range 961bcfe..7bc8d70).

Do not trust STATUS.md, the review request, or disposition ALL CLOSED.
Run from any cwd; the script isolates all mutating cases in tempfile.mkdtemp().

issue_id coverage: grok/P1-1 (961bcfe Scenario C), grok/P1-2 (Claude basename),
P0-1, P1-2 WAL, P1-4 Claude cwd, P1-5 worktree, P1-6 single-task, P1-7 exits,
P1-9 E7, Codex P1-03 adopt, Codex P1-04 sha256 pierce, L4-OPS, F-26 fill.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ["PYTHONPATH"] = "/home/debian/macao/src" + os.pathsep + os.environ.get("PYTHONPATH", "")
sys.path.insert(0, "/home/debian/macao/src")

from click.testing import CliRunner
import yaml

from macao.cli.main import cli, DEFAULT_CONFIG_TEMPLATE
from macao.adapter.session_locator import SessionLocator
from macao.utils.secrets import mask_secrets
from macao.workflow.prober import TeamProber
from macao.workflow.orchestrator import Orchestrator
from macao.workflow.live_dispatcher import LiveAgentDispatcher
from macao.storage.store import StateStore
from macao.core.types import AgentState
import macao.storage.db as db_mod

RESULTS = []
REPO = Path("/home/debian/macao")


def rec(name, ok, detail):
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def git(cwd, *args, check=True):
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True)


def init_repo(root: Path):
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "MACAO Tester")
    git(root, "config", "user.email", "tester@macao.dev")
    (root / "README.md").write_text("# t\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-m", "chore: initial commit")


def write_cfg(root: Path, extra=None):
    cfg = yaml.safe_load(DEFAULT_CONFIG_TEMPLATE)
    cfg["project"]["name"] = "probe-7bc8d70"
    cfg["team"]["executor"] = {"id": "dev-mock", "cli": "mock-cli", "adapter": "pty-wrapper"}
    cfg["team"]["reviewers"] = [
        {"id": "rev-claude", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1.0},
        {"id": "rev-codex", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1.0},
        {"id": "rev-grok", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1.0},
    ]
    cfg["policy"]["minimum_winning_seats"] = 2
    cfg["policy"]["seat_quorum_required"] = 2
    cfg["policy"]["weight_quorum_required"] = 2.0
    if extra:
        for k, v in extra.items():
            if isinstance(v, dict) and k in cfg and isinstance(cfg[k], dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    (root / "macao.yaml").write_text(yaml.dump(cfg), encoding="utf-8")


def snapshot_tree(root: Path):
    files = set()
    for p in root.rglob("*"):
        if p.is_file() and ".git" not in p.parts:
            files.add(str(p.relative_to(root)))
    return files


def reset_db():
    db_mod._db_manager = None


def with_tmp(fn):
    tmp = Path(tempfile.mkdtemp(prefix="macao_probe_7bc8d70_"))
    orig = os.getcwd()
    try:
        os.chdir(tmp)
        reset_db()
        return fn(tmp)
    finally:
        os.chdir(orig)
        reset_db()
        shutil.rmtree(tmp, ignore_errors=True)


def test_p0_1_unknown_cli():
    def inner(tmp):
        init_repo(tmp)
        write_cfg(
            tmp,
            {
                "team": {
                    "executor": {"id": "dev-mock", "cli": "mock-cli", "adapter": "pty-wrapper"},
                    "reviewers": [
                        {"id": "ghost", "cli": "custom-claude", "adapter": "pty-wrapper", "vote_weight": 2.0},
                        {"id": "ok", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1.0},
                    ],
                }
            },
        )
        r = TeamProber(".", dry_run=True).probe()
        ghost = [x for x in r["reviewers"] if x["id"] == "ghost"][0]
        rec(
            "P0-1 custom-claude is MISSING not READY",
            ghost["status"] == "MISSING" and not ghost["installed"] and "ADAPTER_MAP" in (ghost.get("error") or ""),
            f"ghost={ghost} quorum={r['quorum']} can_dispatch={r['can_dispatch']}",
        )
        rec(
            "P0-1 substring CLI cannot dispatch",
            r["can_dispatch"] is False and r["quorum"]["achievable"] is False,
            f"q={r['quorum']} block={r.get('blocking_reasons')}",
        )

    with_tmp(inner)


def test_claude_isolation_and_f26():
    tmp = Path(tempfile.mkdtemp())
    try:
        home = tmp / "home"
        # Basename-only dir (previous grok P1-2)
        claude_proj = home / ".claude" / "projects" / "-macao"
        claude_proj.mkdir(parents=True)
        (claude_proj / "sess-foreign.jsonl").write_text(
            json.dumps({"type": "user", "message": {"content": "hello from other macao"}}) + "\n",
            encoding="utf-8",
        )

        # Canonical dir for /tmp/unrelated/macao with NO cwd in jsonl
        query = Path("/tmp/unrelated/macao")
        sanitized = "-" + __import__("re").sub(r"[^a-zA-Z0-9]", "-", str(query.resolve()).lstrip("/"))
        canon = home / ".claude" / "projects" / sanitized
        canon.mkdir(parents=True)
        (canon / "sess-nocwd.jsonl").write_text(
            json.dumps({"type": "user", "message": {"content": "no cwd field"}}) + "\n",
            encoding="utf-8",
        )

        # Canonical dir WITH foreign cwd
        (canon / "sess-foreigncwd.jsonl").write_text(
            json.dumps({"type": "user", "cwd": "/home/other/repo", "message": {"content": "foreign"}}) + "\n",
            encoding="utf-8",
        )

        with patch("pathlib.Path.home", return_value=home):
            leak = SessionLocator.list_sessions("claude", Path("/tmp/unrelated/macao"))
            # Query a different path that would only hit -macao basename
            other = SessionLocator.list_sessions("claude", Path("/home/debian/macao"))

        rec(
            "P1-4/grok-P1-2 basename -macao must not bind /home/debian/macao",
            other == [],
            f"other={other}",
        )
        rec(
            "P1-4 foreign cwd inside canonical dir discarded",
            all(s.get("session_id") != "sess-foreigncwd" for s in leak),
            f"leak={leak}",
        )
        nocwd = [s for s in leak if s.get("session_id") == "sess-nocwd"]
        rec(
            "F-26 no-cwd must not fill workspace with queried path (fail-closed empty)",
            nocwd == [],
            f"nocwd={nocwd}",
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_scenario_c_and_e7():
    def inner(tmp):
        init_repo(tmp)
        git(tmp, "commit", "--allow-empty", "-m", "feat: real work")
        write_cfg(tmp)
        rev = tmp / "docs" / "reviews"
        rev.mkdir(parents=True)
        (rev / "2026-09-08-review-request-b1234.md").write_text("# RR\nBaseline: b1234\n", encoding="utf-8")
        (rev / "2026-09-08-review-result-b1234-rev-claude.md").write_text("# R\n", encoding="utf-8")
        (tmp / "dirty.txt").write_text("x", encoding="utf-8")

        prober = TeamProber(".", dry_run=True)
        res = prober.probe()
        phys = res["physical_reviews"]
        rec(
            "P1-9 triplet pending over dirty",
            res["executor"]["progress"] == "REVIEW_PENDING"
            and "rev-codex" in phys.get("missing_reviewers", [])
            and "rev-grok" in phys.get("missing_reviewers", []),
            f"progress={res['executor']['progress']} missing={phys.get('missing_reviewers')}",
        )

        runner = CliRunner()
        out = runner.invoke(cli, ["probe", "--dry-run", "--allow-degraded"])
        text = out.output
        rec(
            "grok-P1-1 UI pending+dirty recommends adopt not task create",
            "task adopt" in text.lower()
            and "UNTRACKED DEV" not in text
            and "task create --title" not in text.lower(),
            f"rc={out.exit_code} has_adopt={'task adopt' in text.lower()} UNTRACKED={'UNTRACKED DEV' in text} snippet={text[-600:]!r}",
        )

        created = runner.invoke(cli, ["task", "create", "--title", "Should be blocked by E7"])
        rec(
            "P1-9/UC2-E7 task create refused when pending",
            created.exit_code != 0 and "UC-2 E7" in created.output,
            f"rc={created.exit_code} out={created.output[:400]!r}",
        )

        help_task = runner.invoke(cli, ["task", "--help"])
        rec(
            "Codex P1-03 task adopt registered",
            "adopt" in help_task.output.lower(),
            f"help={help_task.output}",
        )

        before = snapshot_tree(tmp)
        adopt_dry = runner.invoke(cli, ["task", "adopt", "--dry-run"])
        after = snapshot_tree(tmp)
        new = after - before
        rec(
            "Codex P1-03 adopt --dry-run zero new files",
            adopt_dry.exit_code == 0 and not new and not (tmp / ".macao" / "state.db").exists(),
            f"rc={adopt_dry.exit_code} new={sorted(new)} out={adopt_dry.output[:300]!r}",
        )

        adopt = runner.invoke(cli, ["task", "adopt", "--no-review"])
        store = StateStore(str(tmp / ".macao" / "state.db"))
        active = store.get_active_task()
        rec(
            "Codex P1-03 adopt pending -> WAITING_REVIEW",
            adopt.exit_code == 0 and active is not None and active["state"] == "WAITING_REVIEW",
            f"rc={adopt.exit_code} active={active} out={adopt.output[:400]!r}",
        )
        # FSM audit: adopt uses store.update_task_state, not fsm.transition
        events = store.list_audit_events(task_id=active["task_id"], limit=20) if active else []
        types = [e.get("type") or e.get("event_type") for e in events]
        rec(
            "adopt records TASK_ADOPTED (may bypass TransitionTable)",
            "TASK_ADOPTED" in json.dumps(events),
            f"events={events} types={types}",
        )

    with_tmp(inner)


def test_wal_immutable():
    def inner(tmp):
        init_repo(tmp)
        write_cfg(tmp)
        db_dir = tmp / ".macao"
        db_dir.mkdir(parents=True)
        db_file = db_dir / "state.db"
        conn = sqlite3.connect(str(db_file))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            "CREATE TABLE tasks (task_id TEXT PRIMARY KEY, title TEXT, state TEXT, created_at TEXT, updated_at TEXT)"
        )
        conn.commit()
        conn.close()
        for sidecar in db_dir.glob("state.db-*"):
            sidecar.unlink()
        before = set(os.listdir(".macao"))
        runner = CliRunner()
        res = runner.invoke(cli, ["probe", "--dry-run", "--allow-degraded"])
        after = set(os.listdir(".macao"))
        rec(
            "P1-2 WAL dry-run zero sidecars",
            res.exit_code in (0, 2) and before == after,
            f"rc={res.exit_code} before={before} after={after} delta={after-before}",
        )

    with_tmp(inner)


def test_checkpoint_sha256_pierce():
    def inner(tmp):
        init_repo(tmp)
        write_cfg(tmp)
        orch = Orchestrator(".")
        task = orch.start_task(title="Dev Task", task_description="Desc")
        t_id = task["task_id"]
        req = tmp / "docs" / "reviews" / "req.md"
        req.parent.mkdir(parents=True)
        req.write_text("Official Review Request Content", encoding="utf-8")
        true_sha = hashlib.sha256(req.read_bytes()).hexdigest()
        head = git(tmp, "rev-parse", "HEAD").stdout.strip()

        def write_dev(sha, exec_id="dev-mock", exec_cli="mock-cli", path="docs/reviews/req.md"):
            manifest = {
                "version": "1.0",
                "task_id": t_id,
                "checkpoint_ref": head,
                "full_document": {"path": path, "evidence_commit": head, "sha256": sha},
                "status": "ready_for_review",
                "signal": "EXPLICIT",
                "review_round": 1,
                "executor": {"id": exec_id, "cli": exec_cli},
                "development": {
                    "quality_metrics": {"tests_passed": True},
                    "git": {"latest_commit": head},
                },
            }
            p = tmp / ".macao" / ".dev.yml"
            p.write_text(yaml.safe_dump(manifest), encoding="utf-8")

        write_dev("0" * 64)
        z = orch.check_development_checkpoint(t_id)
        rec(
            "Codex P1-04 all-zero sha256 must FAIL closed",
            z is None,
            f"zero_hash_result={z}",
        )

        write_dev(true_sha, path="docs/reviews/missing-file.md")
        missing = orch.check_development_checkpoint(t_id)
        rec(
            "Codex P1-04 missing full_document.path must FAIL closed",
            missing is None,
            f"missing_file_result={missing}",
        )

        write_dev(true_sha, exec_id="imposter")
        bad_id = orch.check_development_checkpoint(t_id)
        rec(
            "Codex P1-04 wrong executor.id must FAIL closed",
            bad_id is None,
            f"bad_id_result={bad_id}",
        )

        write_dev(true_sha, exec_cli="claude-code")
        bad_cli = orch.check_development_checkpoint(t_id)
        rec(
            "Codex P1-04 wrong executor.cli must FAIL closed (claimed)",
            bad_cli is None,
            f"bad_cli_result={bad_cli}",
        )

        write_dev("tampered_fake_sha256" + "0" * 44)
        tampered = orch.check_development_checkpoint(t_id)
        rec(
            "Codex P1-04 tampered sha256 FAIL closed",
            tampered is None,
            f"tampered={tampered}",
        )

        write_dev(true_sha)
        ok = orch.check_development_checkpoint(t_id)
        rec(
            "Codex P1-04 matching sha256 + correct executor.id advances",
            ok is not None and ok.to_state == AgentState.READY_FOR_REVIEW,
            f"ok={ok}",
        )

    with_tmp(inner)


def test_p1_6_start_task_and_cli():
    def inner(tmp):
        init_repo(tmp)
        write_cfg(tmp)
        runner = CliRunner()
        r1 = runner.invoke(cli, ["task", "create", "--title", "A", "--no-probe"])
        r2 = runner.invoke(cli, ["task", "create", "--title", "B", "--no-probe"])
        rec(
            "P1-6 second create without --force blocked",
            r1.exit_code == 0 and r2.exit_code != 0,
            f"r1={r1.exit_code} r2={r2.exit_code} out2={r2.output[:300]!r}",
        )
        orch = Orchestrator(".")
        try:
            orch.start_task(title="Direct", task_description="x")
            raised = False
        except RuntimeError:
            raised = True
        rec("P1-6 Orchestrator.start_task raises without force", raised, "direct start_task")

    with_tmp(inner)


def test_p1_7_exits():
    def inner(tmp):
        init_repo(tmp)
        runner = CliRunner()
        r_probe = runner.invoke(cli, ["probe"])
        r_doctor = runner.invoke(cli, ["doctor"])
        rec(
            "P1-7 probe missing yaml nonzero",
            r_probe.exit_code != 0,
            f"probe_rc={r_probe.exit_code}",
        )
        rec(
            "P1-7 doctor missing yaml (claimed fatal -> nonzero)",
            r_doctor.exit_code != 0,
            f"doctor_rc={r_doctor.exit_code} out={r_doctor.output[:200]!r}",
        )
        (tmp / "macao.yaml").write_text("invalid: yaml: [syntax", encoding="utf-8")
        rec(
            "P1-7 probe malformed yaml nonzero",
            runner.invoke(cli, ["probe"]).exit_code != 0,
            "malformed probe",
        )
        rec(
            "P1-7 doctor malformed yaml nonzero",
            runner.invoke(cli, ["doctor"]).exit_code != 0,
            "malformed doctor",
        )

    with_tmp(inner)


def test_p1_5_clean_worktree():
    def inner(tmp):
        init_repo(tmp)
        write_cfg(tmp)
        from macao.utils.git_utils import GitManager

        gitm = GitManager(".")
        Path(".macao/worktrees/rev-codex/task-1").mkdir(parents=True)
        gitm.create_isolated_worktree("rev-codex", "task-1", 1, "main")
        runner = CliRunner()
        res = runner.invoke(cli, ["clean"])
        code, out_after, _ = gitm._run("worktree", "list", "--porcelain")
        rec(
            "P1-5 clean prunes git worktree ghost",
            res.exit_code == 0 and "rev-codex" not in out_after,
            f"rc={res.exit_code} porcelain={out_after!r}",
        )

    with_tmp(inner)


def test_secrets_and_dispatcher_l4():
    sample = (
        "API key: sk-ant-api03-abcdef12345678901234567890\n"
        "OpenAI: sk-proj-1234567890123456789012345678\n"
        "Auth: Bearer mySecretToken1234567890123456\n"
        "GitHub: ghp_1234567890abcdefghijklmnopqrstuv\n"
        "DB: postgres://admin:superSecretPass123@db.internal:5432/db\n"
        "AWS: AKIAIOSFODNN7EXAMPLE\n"
        "Google: AIzaSyD-0123456789abcdefghijklmnopqrs\n"
        "JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4ifQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c\n"
    )
    masked = mask_secrets(sample)
    leaks = [s for s in [
        "sk-ant-api03-abcdef12345678901234567890",
        "sk-proj-1234567890123456789012345678",
        "mySecretToken1234567890123456",
        "ghp_1234567890abcdefghijklmnopqrstuv",
        "superSecretPass123",
        "AKIAIOSFODNN7EXAMPLE",
    ] if s in masked]
    rec("P1-3 claimed secrets masked", not leaks, f"leaks={leaks} masked={masked!r}")

    src = (REPO / "src/macao/workflow/live_dispatcher.py").read_text(encoding="utf-8")
    rec(
        "Codex P1-02 reviewer payload contains acceptance_criteria",
        "acceptance_criteria" in src,
        f"live_dispatcher_has_acceptance={'acceptance_criteria' in src}",
    )
    d = LiveAgentDispatcher(project_root=str(REPO))
    pi = d.get_adapter_for_reviewer({"id": "pi-rev", "cli": "pi"})
    cur = d.get_adapter_for_reviewer({"id": "cursor-rev", "cli": "cursor"})
    rec("P1-10 Pi adapter constructable", pi.cli_name == "pi", f"pi={pi.cli_name}")
    rec("P1-10 Cursor adapter constructable", cur.cli_name == "cursor", f"cur={cur.cli_name}")

    lr = (REPO / "src/macao/workflow/live_runner.py").read_text(encoding="utf-8")
    rec(
        "L4 live_runner not hardcoded mock-cli / auto_signoff True",
        "mock-cli" not in lr and "auto_signoff: bool = True" not in lr,
        f"has_mock={'mock-cli' in lr} has_auto_true={'auto_signoff: bool = True' in lr}",
    )


def test_real_repo_probe_sidecars():
    root = REPO
    db_dir = root / ".macao"
    before = {p.name: p.stat().st_mtime for p in db_dir.glob("state.db*")}
    before_names = set(before)
    orig = os.getcwd()
    os.chdir(root)
    try:
        runner = CliRunner()
        r = runner.invoke(cli, ["probe", "--dry-run", "--allow-degraded"])
        after_names = {p.name for p in db_dir.glob("state.db*")}
        new = after_names - before_names
        rec(
            "P1-2 real-repo probe --dry-run no new state.db sidecars",
            r.exit_code in (0, 2) and not new,
            f"rc={r.exit_code} new={new} before={before_names} after={after_names}",
        )
        # Request claimed rc=0 without --allow-degraded
        r2 = runner.invoke(cli, ["probe", "--dry-run"])
        rec(
            "request cmd5 probe --dry-run rc==0 on this repo",
            r2.exit_code == 0,
            f"rc={r2.exit_code} can_dispatch_hint={'BLOCKED' in r2.output or 'Blocked' in r2.output}",
        )
    finally:
        os.chdir(orig)


def test_docs_known_simplifications():
    status = (REPO / "docs/reviews/STATUS.md").read_text(encoding="utf-8")
    rec(
        "Guidelines §5.2 known-simplification table lives in STATUS.md",
        "expiry" in status.lower() and ("已知简化" in status or "Known simplification" in status),
        "STATUS has no §5.2 table with expiry fields",
    )


if __name__ == "__main__":
    os.chdir(str(REPO))
    test_p0_1_unknown_cli()
    test_claude_isolation_and_f26()
    test_scenario_c_and_e7()
    test_wal_immutable()
    test_checkpoint_sha256_pierce()
    test_p1_6_start_task_and_cli()
    test_p1_7_exits()
    test_p1_5_clean_worktree()
    test_secrets_and_dispatcher_l4()
    test_real_repo_probe_sidecars()
    test_docs_known_simplifications()
    print("\n===== SUMMARY =====")
    fails = [x for x in RESULTS if not x[1]]
    print(f"total={len(RESULTS)} fail={len(fails)}")
    for name, ok, detail in RESULTS:
        if not ok:
            print(f"  FAIL {name}")
    sys.exit(1 if fails else 0)
