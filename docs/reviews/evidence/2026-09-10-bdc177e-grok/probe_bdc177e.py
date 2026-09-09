#!/usr/bin/env python3
"""Independent Round-5 probes for bdc177e.

issue_ids:
  grok/P2-1 (prior e06d44c): empty evidence_commit
  grok/P2-2 (prior e06d44c): sibling/prefix path escape
  grok/P2-untracked: blob check skipped for never-committed evidence
  grok/P2-unknown-exec: unknown executor CLI returns None; --no-probe still creates CODING
  grok/P2-reviewer-criteria: reviewer inject_task omits acceptance_criteria
  grok/L4-OPS: live_runner mock-cli + auto_signoff
commit: bdc177eaaff577e119093e686f2164bcc133f781
platform: Linux; no network; no vendor CLI required
last_executed: 2026-09-10

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
from unittest.mock import MagicMock, patch

sys.path.insert(0, "/home/debian/macao/src")
os.environ["PYTHONPATH"] = "/home/debian/macao/src" + os.pathsep + os.environ.get("PYTHONPATH", "")

import yaml
from click.testing import CliRunner

from macao.adapter.antigravity import AntigravityAdapter
from macao.adapter.claude import ClaudeCodeAdapter
from macao.adapter.codex import CodexAdapter
from macao.adapter.cursor import CursorAgentAdapter
from macao.adapter.kimi import KimiAdapter
from macao.adapter.opencode import OpenCodeAdapter
from macao.adapter.pi import PiAdapter
from macao.adapter.session_locator import SessionLocator
from macao.cli.main import DEFAULT_CONFIG_TEMPLATE, cli, get_orchestrator
from macao.core.schema import validate_dev_manifest
from macao.core.types import AgentState
from macao.storage.store import StateStore
from macao.workflow.live_dispatcher import LiveAgentDispatcher
from macao.workflow.orchestrator import Orchestrator
import macao.storage.db as db_mod


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def make_repo(prefix="bdc_"):
    tmp = Path(tempfile.mkdtemp(prefix=prefix))
    git(tmp, "init", "-b", "main")
    git(tmp, "config", "user.name", "t")
    git(tmp, "config", "user.email", "t@t.dev")
    (tmp / "README.md").write_text("x\n")
    git(tmp, "add", "README.md")
    git(tmp, "commit", "-m", "init")
    cfg = yaml.safe_load(DEFAULT_CONFIG_TEMPLATE)
    cfg["project"]["name"] = "bdc"
    cfg["team"]["executor"] = {"id": "dev-mock", "cli": "mock-cli", "adapter": "pty-wrapper"}
    cfg["team"]["reviewers"] = [
        {"id": "r1", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1},
        {"id": "r2", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1},
    ]
    (tmp / "macao.yaml").write_text(yaml.dump(cfg))
    req = tmp / "docs" / "reviews" / "req.md"
    req.parent.mkdir(parents=True)
    req.write_text("Official Review Request Content\n", encoding="utf-8")
    git(tmp, "add", "docs/reviews/req.md", "macao.yaml")
    git(tmp, "commit", "-m", "add tracked req")
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


def request_example_yaml():
    return {
        "version": "1.0",
        "timestamp": "2026-09-09T23:10:00Z",
        "task_id": "task-20260909-p1-closures-wire-executor-criteria-blob-check",
        "checkpoint_ref": "bdc177e",
        "review_round": 5,
        "status": "ready_for_review",
        "signal": "EXPLICIT",
        "executor": {"id": "opencode-dev", "role": "Lead Orchestrator Architect", "cli": "opencode"},
        "full_document": {
            "path": "docs/reviews/2026-09-09-disposition-e06d44c.md",
            "evidence_commit": "bdc177e",
            "sha256": "877f4bc28fd444cba43e67782ac1129486447e91ccb915e972b6f22c6d07d56c",
        },
        "development": {
            "phase": "Phase 3 Orchestrator Hardening & Multi-Agent Dispatch",
            "description": "Remediate all P1 blocking findings from Round 4 (e06d44c)",
            "artifacts": [
                {"type": "code", "path": "src/macao/workflow/orchestrator.py", "changed_lines": 36, "updated": True}
            ],
            "quality_metrics": {"tests_passed": True, "tests_total": 170},
            "git": {"latest_commit": "bdc177e", "branch": "main"},
        },
    }


def main():
    rows = []
    tmp, head, true_sha, cfg = make_repo()
    orig = os.getcwd()
    try:
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
            ("good_tracked", dict(), True),
        ]
        for name, kw, should_pass in cases:
            adv = run_ckpt(name, tmp, head, true_sha, **kw)
            rows.append((name, adv, should_pass))

        # Prior P2-2 sibling prefix escape
        sibling = tmp.parent / (tmp.name + "-evil")
        sibling.mkdir()
        secret = sibling / "secret.md"
        secret.write_text("outside-secret\n")
        secret_sha = hashlib.sha256(secret.read_bytes()).hexdigest()
        rel = f"../{tmp.name}-evil/secret.md"
        adv = run_ckpt("prefix_escape", tmp, head, true_sha, path=rel, sha=secret_sha)
        rows.append(("prefix_escape", adv, False))

        sibling2 = tmp.parent / (tmp.name + "_sibling")
        sibling2.mkdir()
        evil = sibling2 / "evil.md"
        evil.write_text("evil content", encoding="utf-8")
        evil_sha = hashlib.sha256(b"evil content").hexdigest()
        rel2 = os.path.relpath(evil, tmp)
        adv = run_ckpt("sibling_underscore", tmp, head, true_sha, path=rel2, sha=evil_sha)
        rows.append(("sibling_underscore", adv, False))

        # Tracked then mutated on disk: envelope uses disk hash, blob differs
        os.chdir(tmp)
        db_mod._db_manager = None
        orch = Orchestrator(".")
        task = orch.start_task(title="blob_tamper", task_description="d")
        t_id = task["task_id"]
        req = tmp / "docs" / "reviews" / "req.md"
        req.write_text("Uncommitted mutation v2\n")
        disk_sha = hashlib.sha256(req.read_bytes()).hexdigest()
        write_dev(tmp, t_id, head, disk_sha)
        ch = orch.check_development_checkpoint(t_id)
        st = orch.store.get_task(t_id)["state"]
        print(f"CKPT blob_tamper: advanced={st == AgentState.READY_FOR_REVIEW.value} trigger={getattr(ch, 'trigger', None)}")
        rows.append(("blob_tamper_tracked", st != AgentState.READY_FOR_REVIEW.value and ch is None, True))
        orch.cancel_task(t_id, reason="next")
        req.write_text("Official Review Request Content\n")
        os.chdir(orig)
        db_mod._db_manager = None

        # Untracked evidence file: disk hash matches, never in git
        os.chdir(tmp)
        db_mod._db_manager = None
        orch = Orchestrator(".")
        task = orch.start_task(title="untracked", task_description="d")
        t_id = task["task_id"]
        untracked = tmp / "docs" / "reviews" / "written-after-head.md"
        untracked.write_text("this document is not in the declared commit\n")
        u_sha = hashlib.sha256(untracked.read_bytes()).hexdigest()
        write_dev(tmp, t_id, head, u_sha, path="docs/reviews/written-after-head.md")
        in_commit = subprocess.run(
            ["git", "cat-file", "-e", f"{head}:docs/reviews/written-after-head.md"],
            cwd=tmp, capture_output=True,
        )
        ch = orch.check_development_checkpoint(t_id)
        st = orch.store.get_task(t_id)["state"]
        print(
            f"CKPT untracked: advanced={st == AgentState.READY_FOR_REVIEW.value} "
            f"git_cat_file_rc={in_commit.returncode} trigger={getattr(ch, 'trigger', None)}"
        )
        rows.append(("untracked_not_in_git", in_commit.returncode != 0, True))
        rows.append(("untracked_advances", st == AgentState.READY_FOR_REVIEW.value, True))
        orch.cancel_task(t_id, reason="next")
        os.chdir(orig)
        db_mod._db_manager = None

        # Composition root wires executor for mock-cli
        os.chdir(tmp)
        db_mod._db_manager = None
        orch = get_orchestrator(str(tmp))
        wired = orch.executor is not None and getattr(orch.executor, "agent_id", None) == "dev-mock"
        print(f"WIRE mock-cli executor type={type(orch.executor).__name__} id={getattr(orch.executor, 'agent_id', None)}")
        rows.append(("composition_root_wires_mock", wired, True))
        os.chdir(orig)
        db_mod._db_manager = None

        # Unknown executor CLI -> adapter None; --no-probe creates CODING; default --probe blocks
        utmp = Path(tempfile.mkdtemp(prefix="bdc_unk_"))
        try:
            git(utmp, "init", "-b", "main")
            git(utmp, "config", "user.name", "t")
            git(utmp, "config", "user.email", "t@t.dev")
            (utmp / "README.md").write_text("x\n")
            git(utmp, "add", "README.md")
            git(utmp, "commit", "-m", "init")
            cfg_txt = DEFAULT_CONFIG_TEMPLATE.replace('cli: "claude-code"', 'cli: "unknown-executor"', 1)
            (utmp / "macao.yaml").write_text(cfg_txt)
            os.chdir(utmp)
            db_mod._db_manager = None
            orch_u = get_orchestrator(str(utmp))
            print(f"UNKNOWN executor is None={orch_u.executor is None}")
            rows.append(("unknown_executor_adapter_none", orch_u.executor is None, True))
            # reviewer factory raises (instance method, fail-closed)
            raised = False
            try:
                LiveAgentDispatcher(str(utmp)).get_adapter_for_reviewer({"cli": "unknown-executor", "id": "r"})
            except ValueError:
                raised = True
            rows.append(("unknown_reviewer_raises", raised, True))
            exec_none = LiveAgentDispatcher.get_adapter_for_executor({"cli": "unknown-executor", "id": "e"})
            rows.append(("unknown_executor_returns_none", exec_none is None, True))

            runner = CliRunner()
            res_np = runner.invoke(cli, ["task", "create", "--no-probe", "--title", "lost executor", "--acceptance", "must-run"])
            active_np = StateStore(str(utmp / ".macao" / "state.db")).get_active_task() if (utmp / ".macao" / "state.db").exists() else None
            print(f"UNKNOWN --no-probe rc={res_np.exit_code} state={active_np and active_np.get('state')}")
            rows.append((
                "unknown_noprobe_creates_coding",
                res_np.exit_code == 0 and active_np is not None and active_np["state"] == AgentState.CODING.value,
                True,
            ))
            if active_np:
                orch_u.cancel_task(active_np["task_id"], reason="cleanup")

            db_mod._db_manager = None
            res_p = runner.invoke(cli, ["task", "create", "--title", "should block", "--acceptance", "must-run"])
            print(f"UNKNOWN default --probe rc={res_p.exit_code}")
            rows.append(("unknown_probe_blocks", res_p.exit_code != 0, True))
        finally:
            os.chdir(orig)
            db_mod._db_manager = None
            shutil.rmtree(utmp, ignore_errors=True)

        # Adapter criteria: executor path vs reviewer path
        adapters = [
            ClaudeCodeAdapter(agent_id="claude-dev"),
            CodexAdapter(agent_id="codex-dev"),
            OpenCodeAdapter(agent_id="opencode-dev"),
            AntigravityAdapter(agent_id="agy-dev"),
            KimiAdapter(agent_id="kimi-dev"),
            CursorAgentAdapter(agent_id="cursor-dev"),
            PiAdapter(agent_id="pi-dev"),
        ]
        exec_ok = True
        rev_ok = True
        for adapter in adapters:
            adapter.is_running = True
            mock_session = MagicMock()
            adapter.session = mock_session
            adapter.inject_task({
                "task_description": "Critical feature work",
                "acceptance_criteria": ["MUST_PASS_CRITERION_ALPHA"],
            })
            sent = mock_session.write_input.call_args[0][0]
            if "MUST_PASS_CRITERION_ALPHA" not in sent:
                exec_ok = False
                print(f"EXECUTOR criteria MISS {adapter.__class__.__name__}")
            mock_session.reset_mock()
            adapter.config["role"] = "reviewer"
            adapter.inject_task({
                "checkpoint_ref": "abc1234",
                "review_round": 1,
                "diff": "diff --git a/x b/x",
                "acceptance_criteria": ["MUST_PASS_CRITERION_ALPHA"],
            })
            sent = mock_session.write_input.call_args[0][0]
            if "MUST_PASS_CRITERION_ALPHA" not in sent:
                rev_ok = False
                print(f"REVIEWER criteria MISS {adapter.__class__.__name__} prompt_has_REVIEW={('REVIEW_REQUEST' in sent)}")
        print(f"CRITERIA executor_all={exec_ok} reviewer_all={rev_ok}")
        rows.append(("executor_criteria_in_prompt", exec_ok, True))
        # Observation: reviewer branch still omits criteria. expected False = hole confirmed.
        rows.append(("reviewer_criteria_omitted", (not rev_ok), True))

        # Request example envelope schema
        ok, err = validate_dev_manifest(request_example_yaml())
        print(f"EXAMPLE validate_dev_manifest ok={ok} err={err}")
        rows.append(("example_manifest_schema", ok is True, True))

        # L4 live_runner
        lr = Path("/home/debian/macao/src/macao/workflow/live_runner.py").read_text()
        mock_hardcoded = 'cli": "mock-cli"' in lr and "auto_signoff: bool = True" in lr
        print(f"L4 live_runner mock_cli+auto_signoff={mock_hardcoded}")
        rows.append(("l4_still_mock", mock_hardcoded, True))

        # F-26 Claude no cwd vs Pi no cwd
        fake_home = Path(tempfile.mkdtemp(prefix="bdc_home_"))
        try:
            proj = tmp.resolve()
            sanitized = "-" + __import__("re").sub(r"[^a-zA-Z0-9]", "-", str(proj).lstrip("/"))
            sdir = fake_home / ".claude" / "projects" / sanitized
            sdir.mkdir(parents=True)
            (sdir / "sess1.jsonl").write_text(
                json.dumps({"type": "user", "message": {"content": "hello no cwd"}}) + "\n"
            )
            with patch("macao.adapter.session_locator.Path.home", return_value=fake_home):
                found = SessionLocator._find_claude_sessions(proj)
            print(f"F26 claude no-cwd sessions={found}")
            rows.append(("f26_claude_no_cwd", found == [], True))
        finally:
            shutil.rmtree(fake_home, ignore_errors=True)

        src_sl = Path("/home/debian/macao/src/macao/adapter/session_locator.py").read_text()
        pi_fallback = 'workspace": str(session_cwd or resolved_proj)' in src_sl
        print(f"Pi cwd fallback still present={pi_fallback}")
        rows.append(("pi_cwd_fallback_present", pi_fallback, True))

        print("---- RESULTS ----")
        bad = []
        for name, actual, expected in rows:
            ok = actual == expected
            print(f"{'OK' if ok else 'FAIL'} {name}: actual={actual} expected={expected}")
            if not ok:
                bad.append(name)
        # reviewer_criteria_in_prompt expected True in the table means "we hoped it was fixed";
        # a FAIL here is the residual finding, not a script error.
        print("ALL_MATCH" if not bad else "MISMATCH")
        print("bad=" + ",".join(bad))
        return 0
    finally:
        os.chdir(orig)
        db_mod._db_manager = None
        shutil.rmtree(tmp, ignore_errors=True)
        try:
            shutil.rmtree(tmp.parent / (tmp.name + "-evil"), ignore_errors=True)
        except Exception:
            pass
        try:
            shutil.rmtree(tmp.parent / (tmp.name + "_sibling"), ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
