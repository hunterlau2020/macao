#!/usr/bin/env python3
"""Independent Round-4 probes for e06d44c.

issue_ids:
  grok/P1-1 (prior): checkpoint anti-forgery residual
  grok/P1-2 (prior): task adopt UC-11 E1
  grok/P2: empty evidence_commit, path-prefix sandbox, F-26 Pi, doctor rc, L4 mock
commit: e06d44cb31a0dbcbe199e6bb124430e9701e087f
platform: Linux; no network; no vendor CLI required
last_executed: 2026-09-09T00:44:04+08:00

Each checkpoint case uses a fresh CODING task. Host repo is not written.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/home/debian/macao/src")
os.environ["PYTHONPATH"] = "/home/debian/macao/src" + os.pathsep + os.environ.get("PYTHONPATH", "")

import yaml
from click.testing import CliRunner
from macao.cli.main import cli, DEFAULT_CONFIG_TEMPLATE
from macao.core.types import AgentState
from macao.workflow.orchestrator import Orchestrator
from macao.workflow.live_dispatcher import LiveAgentDispatcher
from macao.adapter.session_locator import SessionLocator
import macao.storage.db as db_mod


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def make_repo():
    tmp = Path(tempfile.mkdtemp(prefix="e06_"))
    git(tmp, "init", "-b", "main")
    git(tmp, "config", "user.name", "t")
    git(tmp, "config", "user.email", "t@t.dev")
    (tmp / "README.md").write_text("x\n")
    git(tmp, "add", "README.md")
    git(tmp, "commit", "-m", "init")
    cfg = yaml.safe_load(DEFAULT_CONFIG_TEMPLATE)
    cfg["project"]["name"] = "e06"
    cfg["team"]["executor"] = {"id": "dev-mock", "cli": "mock-cli", "adapter": "pty-wrapper"}
    cfg["team"]["reviewers"] = [
        {"id": "r1", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1},
        {"id": "r2", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1},
    ]
    (tmp / "macao.yaml").write_text(yaml.dump(cfg))
    req = tmp / "docs" / "reviews" / "req.md"
    req.parent.mkdir(parents=True)
    req.write_text("Official Review Request Content\n", encoding="utf-8")
    head = git(tmp, "rev-parse", "HEAD").stdout.strip()
    true_sha = hashlib.sha256(req.read_bytes()).hexdigest()
    return tmp, head, true_sha, cfg


def write_dev(root: Path, t_id: str, head: str, sha: str, **fd_extra):
    exec_id = fd_extra.pop("exec_id", "dev-mock")
    exec_cli = fd_extra.pop("exec_cli", "mock-cli")
    path = fd_extra.pop("path", "docs/reviews/req.md")
    evidence = fd_extra.pop("evidence_commit", head)
    chk = fd_extra.pop("checkpoint_ref", head)
    latest = fd_extra.pop("latest_commit", head)
    drop_evidence = fd_extra.pop("drop_evidence", False)
    full_document = {"path": path, "sha256": sha}
    if not drop_evidence:
        full_document["evidence_commit"] = evidence
    manifest = {
        "version": "1.0",
        "task_id": t_id,
        "checkpoint_ref": chk,
        "full_document": full_document,
        "status": "ready_for_review",
        "signal": "EXPLICIT",
        "review_round": 1,
        "executor": {"id": exec_id, "cli": exec_cli},
        "development": {
            "quality_metrics": {"tests_passed": True},
            "git": {"latest_commit": latest},
        },
    }
    p = root / ".macao" / ".dev.yml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(manifest))


def run_ckpt(name, tmp, head, true_sha, **kwargs):
    orig = os.getcwd()
    os.chdir(tmp)
    try:
        db_mod._db_manager = None
        orch = Orchestrator(".")
        task = orch.start_task(title=name, task_description="d")
        t_id = task["task_id"]
        write_dev(tmp, t_id, head, kwargs.pop("sha", true_sha), **kwargs)
        ch = orch.check_development_checkpoint(t_id)
        st = orch.store.get_task(t_id)["state"]
        advanced = st == AgentState.READY_FOR_REVIEW.value
        print(f"CKPT {name}: advanced={advanced} trigger={getattr(ch, 'trigger', None)} state={st}")
        orch.cancel_task(t_id, reason="next")
        return advanced
    finally:
        os.chdir(orig)
        db_mod._db_manager = None


def main():
    rows = []
    tmp, head, true_sha, cfg = make_repo()
    try:
        expect_block = []
        expect_pass = []

        cases = [
            ("zero_hash", dict(sha="0" * 64), False),
            ("missing_path", dict(path="docs/reviews/does-not-exist.md"), False),
            ("empty_sha", dict(sha=""), False),
            ("wrong_id", dict(exec_id="imposter"), False),
            ("wrong_cli", dict(exec_cli="claude-code"), False),
            ("tampered", dict(sha="ab" * 32), False),
            ("outside_path", dict(path="/etc/passwd"), False),
            ("empty_evidence", dict(evidence_commit=""), False),
            ("missing_evidence", dict(drop_evidence=True), False),
            ("unbound_evidence", dict(evidence_commit="0" * 40), False),
            ("good", dict(), True),
        ]
        for name, kw, should_pass in cases:
            adv = run_ckpt(name, tmp, head, true_sha, **kw)
            rows.append((name, adv, should_pass))

        # Path-prefix sibling sandbox: ../<reponame>-evil/secret.md
        sibling = tmp.parent / (tmp.name + "-evil")
        sibling.mkdir()
        secret = sibling / "secret.md"
        secret.write_text("outside-secret\n")
        secret_sha = hashlib.sha256(secret.read_bytes()).hexdigest()
        rel = f"../{tmp.name}-evil/secret.md"
        adv = run_ckpt("prefix_escape", tmp, head, true_sha, path=rel, sha=secret_sha)
        rows.append(("prefix_escape", adv, False))

        # UC-11 E1 adopt deadbeef
        orig = os.getcwd()
        os.chdir(tmp)
        try:
            db_mod._db_manager = None
            req = tmp / "docs" / "reviews" / "2026-09-08-review-request-deadbeef.md"
            req.write_text("# Review Request\n\nBaseline: deadbeef\n")
            runner = CliRunner()
            res = runner.invoke(cli, ["task", "adopt", "--no-review"])
            print(f"ADOPT deadbeef: rc={res.exit_code} e1={'UC-11 E1' in (res.output or '')} success={'Successfully adopted' in (res.output or '')}")
            rows.append(("adopt_deadbeef_blocked", res.exit_code == 1 and "UC-11 E1" in (res.output or "") and "Successfully adopted" not in (res.output or ""), True))
            state_db = tmp / ".macao" / "state.db"
            if state_db.exists():
                from macao.storage.store import StateStore
                st = StateStore(str(state_db))
                active = st.get_active_task()
                rows.append(("adopt_deadbeef_no_active", active is None, True))
                print(f"ADOPT deadbeef active={active}")
            else:
                rows.append(("adopt_deadbeef_no_active", True, True))
                print("ADOPT deadbeef no state.db")
        finally:
            os.chdir(orig)

        # Happy-path adopt FSM audit
        os.chdir(tmp)
        try:
            db_mod._db_manager = None
            req2 = tmp / "docs" / "reviews" / f"2026-09-09-review-request-{head[:8]}.md"
            req2.write_text(f"# Real Request\n\nBaseline: {head}\n")
            # remove deadbeef so prober picks the real one (latest mtime)
            (tmp / "docs" / "reviews" / "2026-09-08-review-request-deadbeef.md").unlink()
            runner = CliRunner()
            res = runner.invoke(cli, ["task", "adopt", "--no-review"])
            print(f"ADOPT real: rc={res.exit_code} out_ok={'WAITING_REVIEW' in (res.output or '')}")
            from macao.storage.store import StateStore
            st = StateStore(str(tmp / ".macao" / "state.db"))
            active = st.get_active_task()
            types = [e.get("type") for e in st.list_audit_events(task_id=active["task_id"])] if active else []
            print(f"ADOPT real state={active and active['state']} audit={types}")
            rows.append(("adopt_real_waiting", bool(active) and active["state"] == "WAITING_REVIEW" and res.exit_code == 0, True))
            rows.append(("adopt_fsm_e2", "STATE_TRANSITION_E2_ADOPT" in types and "TASK_ADOPTED" in types, True))
        finally:
            os.chdir(orig)

        # doctor missing yaml
        dtmp = Path(tempfile.mkdtemp(prefix="e06doc_"))
        try:
            os.chdir(dtmp)
            runner = CliRunner()
            res = runner.invoke(cli, ["doctor"])
            print(f"DOCTOR missing yaml: rc={res.exit_code}")
            rows.append(("doctor_missing_yaml_nonzero", res.exit_code != 0, True))
        finally:
            os.chdir(orig)
            shutil.rmtree(dtmp, ignore_errors=True)

        # acceptance_criteria in dispatcher signature / payload construction
        src = Path("/home/debian/macao/src/macao/workflow/live_dispatcher.py").read_text()
        rows.append(("dispatcher_acceptance_in_payload", '"acceptance_criteria": crit_list' in src, True))
        print(f"DISPATCHER acceptance_criteria wired={'"acceptance_criteria": crit_list' in src}")

        # L4 live_runner
        lr = Path("/home/debian/macao/src/macao/workflow/live_runner.py").read_text()
        mock_hardcoded = 'cli": "mock-cli"' in lr and "auto_signoff: bool = True" in lr
        print(f"L4 live_runner mock_cli+auto_signoff={mock_hardcoded}")
        rows.append(("l4_still_mock", mock_hardcoded, True))  # True = observation holds (not a pass of L4)

        # F-26 Claude: no cwd in jsonl -> empty
        fake_home = Path(tempfile.mkdtemp(prefix="e06home_"))
        try:
            proj = tmp.resolve()
            sanitized = "-" + __import__("re").sub(r"[^a-zA-Z0-9]", "-", str(proj).lstrip("/"))
            sdir = fake_home / ".claude" / "projects" / sanitized
            sdir.mkdir(parents=True)
            (sdir / "sess1.jsonl").write_text(
                json.dumps({"type": "user", "message": {"content": "hello no cwd"}}) + "\n"
            )
            from unittest.mock import patch
            with patch("macao.adapter.session_locator.Path.home", return_value=fake_home):
                found = SessionLocator._find_claude_sessions(proj)
            print(f"F26 claude no-cwd sessions={found}")
            rows.append(("f26_claude_no_cwd", found == [], True))
        finally:
            shutil.rmtree(fake_home, ignore_errors=True)

        print("---- RESULTS ----")
        bad = []
        for name, actual, expected in rows:
            ok = actual == expected
            print(f"{'OK' if ok else 'FAIL'} {name}: actual={actual} expected={expected}")
            if not ok:
                bad.append(name)
        print("ALL_MATCH" if not bad else "MISMATCH")
        print("bad=" + ",".join(bad))
        return 1 if bad else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        try:
            shutil.rmtree(tmp.parent / (tmp.name + "-evil"), ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
