#!/usr/bin/env python3
"""Independent Round-6 probes for 51fa456.

issue_ids:
  Codex P1-bdc177e-01 / grok P2-1: untracked evidence must NOT advance
  Codex P1-bdc177e-02 / grok P2-2: unknown executor CLI must fail-closed
  grok P2-3: reviewer inject_task must include acceptance_criteria
  prior grok P2-1/P2-2 (e06d44c): empty evidence_commit / sibling escape stay blocked
  grok/L4-OPS: live_runner still mock-cli + auto_signoff
  grok/P2-schema: sha256/evidence_commit still lack pattern/minLength
  grok/P2-pi-cwd: Pi still falls back to resolved_proj without cwd
commit: 51fa456ada474818a1107f1a11b061661dab1063
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


def make_repo(prefix="r6_"):
    tmp = Path(tempfile.mkdtemp(prefix=prefix))
    git(tmp, "init", "-b", "main")
    git(tmp, "config", "user.name", "t")
    git(tmp, "config", "user.email", "t@t.dev")
    (tmp / "README.md").write_text("x\n")
    git(tmp, "add", "README.md")
    git(tmp, "commit", "-m", "init")
    cfg = yaml.safe_load(DEFAULT_CONFIG_TEMPLATE)
    cfg["project"]["name"] = "r6"
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
        "timestamp": "2026-09-10T01:30:00Z",
        "task_id": "task-20260910-p1-closures-evidence-commit-binding-failclosed-executor",
        "checkpoint_ref": "51fa456",
        "review_round": 6,
        "status": "ready_for_review",
        "signal": "EXPLICIT",
        "executor": {"id": "opencode-dev", "role": "Lead Orchestrator Architect", "cli": "opencode"},
        "full_document": {
            "path": "docs/reviews/2026-09-10-disposition-bdc177e.md",
            "evidence_commit": "51fa456",
            "sha256": "a78035b8786d7a59c9379af169427d7ea0643eebb2ba12fa1c5e6c4ba04ac451",
        },
        "development": {
            "phase": "Phase 3 Orchestrator Hardening & Multi-Agent Dispatch",
            "description": "Remediate all P1 blocking findings from Round 5 (bdc177e)",
            "artifacts": [
                {"type": "code", "path": "src/macao/workflow/orchestrator.py", "changed_lines": 16, "updated": True}
            ],
            "quality_metrics": {"tests_passed": True, "tests_total": 173},
            "git": {"latest_commit": "51fa456", "branch": "main"},
        },
    }


def main():
    rows = []
    tmp, head, true_sha, cfg = make_repo()
    orig = os.getcwd()
    dtmp = None
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

        # Untracked evidence: disk hash matches, never in git — MUST stay CODING
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
        rows.append(("untracked_blocked", st == AgentState.CODING.value and ch is None, True))
        orch.cancel_task(t_id, reason="next")
        os.chdir(orig)
        db_mod._db_manager = None

        # File committed later (HEAD2) but envelope still declares HEAD1
        os.chdir(tmp)
        db_mod._db_manager = None
        orch = Orchestrator(".")
        task = orch.start_task(title="later_commit", task_description="d")
        t_id = task["task_id"]
        later = tmp / "docs" / "reviews" / "later.md"
        later.write_text("committed after head1\n")
        git(tmp, "add", "docs/reviews/later.md")
        git(tmp, "commit", "-m", "later evidence")
        head2 = git(tmp, "rev-parse", "HEAD").stdout.strip()
        later_sha = hashlib.sha256(later.read_bytes()).hexdigest()
        write_dev(
            tmp, t_id, head, later_sha,
            path="docs/reviews/later.md",
            evidence_commit=head,
            checkpoint_ref=head,
            latest_commit=head,
        )
        ch = orch.check_development_checkpoint(t_id)
        st = orch.store.get_task(t_id)["state"]
        print(f"CKPT later_file_vs_head1: advanced={st == AgentState.READY_FOR_REVIEW.value} head2={head2[:8]}")
        rows.append(("later_file_declared_head1_blocked", ch is None and st == AgentState.CODING.value, True))
        write_dev(
            tmp, t_id, head2, later_sha,
            path="docs/reviews/later.md",
            evidence_commit=head2,
            checkpoint_ref=head2,
            latest_commit=head2,
        )
        ch = orch.check_development_checkpoint(t_id)
        st = orch.store.get_task(t_id)["state"]
        print(f"CKPT later_file_vs_head2: advanced={st == AgentState.READY_FOR_REVIEW.value}")
        rows.append(("later_file_declared_head2_ok", st == AgentState.READY_FOR_REVIEW.value, True))
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

        # Unknown executor CLI: factory ValueError; composition root sys.exit(1); --no-probe no task
        utmp = Path(tempfile.mkdtemp(prefix="r6_unk_"))
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

            factory_raises = False
            factory_msg = ""
            try:
                LiveAgentDispatcher.get_adapter_for_executor({"cli": "unknown-executor", "id": "e"})
            except ValueError as e:
                factory_raises = True
                factory_msg = str(e)
            print(f"UNKNOWN factory raises={factory_raises} msg={factory_msg!r}")
            rows.append(("unknown_executor_factory_raises", factory_raises and "unknown-executor" in factory_msg, True))

            reviewer_raises = False
            try:
                LiveAgentDispatcher(str(utmp)).get_adapter_for_reviewer({"cli": "unknown-executor", "id": "r"})
            except ValueError:
                reviewer_raises = True
            rows.append(("unknown_reviewer_raises", reviewer_raises, True))

            orch_exit = False
            orch_code = None
            try:
                get_orchestrator(str(utmp))
            except SystemExit as e:
                orch_exit = True
                orch_code = e.code
            print(f"UNKNOWN get_orchestrator SystemExit={orch_exit} code={orch_code}")
            rows.append(("unknown_get_orchestrator_exits", orch_exit and orch_code == 1, True))

            init_raises = False
            try:
                Orchestrator(str(utmp), config=yaml.safe_load(cfg_txt))
            except ValueError:
                init_raises = True
            print(f"UNKNOWN Orchestrator.__init__ ValueError={init_raises}")
            rows.append(("unknown_orchestrator_init_raises", init_raises, True))

            runner = CliRunner()
            res_np = runner.invoke(cli, ["task", "create", "--no-probe", "--title", "lost executor", "--acceptance", "must-run"])
            db_exists = (utmp / ".macao" / "state.db").exists()
            active_np = StateStore(str(utmp / ".macao" / "state.db")).get_active_task() if db_exists else None
            print(f"UNKNOWN --no-probe rc={res_np.exit_code} active={active_np} out_has_cli={'unknown-executor' in (res_np.output or '')}")
            rows.append(("unknown_noprobe_nonzero", res_np.exit_code != 0, True))
            rows.append(("unknown_noprobe_no_active_task", active_np is None, True))
            rows.append(("unknown_noprobe_mentions_cli", "unknown-executor" in (res_np.output or ""), True))

            db_mod._db_manager = None
            res_p = runner.invoke(cli, ["task", "create", "--title", "should block", "--acceptance", "must-run"])
            print(f"UNKNOWN default --probe rc={res_p.exit_code}")
            rows.append(("unknown_probe_blocks", res_p.exit_code != 0, True))
        finally:
            os.chdir(orig)
            db_mod._db_manager = None
            shutil.rmtree(utmp, ignore_errors=True)

        # Missing executor key: team dict present, executor_adapter None
        os.chdir(tmp)
        db_mod._db_manager = None
        missing_exec_attr = False
        try:
            o = Orchestrator(".", config={"version": "2.5", "team": {"reviewers": []}})
            missing_exec_attr = not hasattr(o, "executor")
            print(f"MISSING executor attr={missing_exec_attr} hasattr={hasattr(o, 'executor')} val={getattr(o, 'executor', 'NOATTR')!r}")
        except Exception as e:
            print(f"MISSING executor exception={type(e).__name__}: {e}")
            missing_exec_attr = True
        rows.append(("missing_executor_leaves_attr_unset", missing_exec_attr, True))
        os.chdir(orig)
        db_mod._db_manager = None

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
            if "MUST_PASS_CRITERION_ALPHA" not in sent or "REVIEW_REQUEST:" not in sent:
                rev_ok = False
                print(f"REVIEWER criteria MISS {adapter.__class__.__name__} prompt={sent[:180]!r}")
        print(f"CRITERIA executor_all={exec_ok} reviewer_all={rev_ok}")
        rows.append(("executor_criteria_in_prompt", exec_ok, True))
        rows.append(("reviewer_criteria_in_prompt", rev_ok, True))

        ok, err = validate_dev_manifest(request_example_yaml())
        print(f"EXAMPLE validate_dev_manifest ok={ok} err={err}")
        rows.append(("example_manifest_schema", ok is True, True))

        lr = Path("/home/debian/macao/src/macao/workflow/live_runner.py").read_text()
        mock_hardcoded = 'cli": "mock-cli"' in lr and "auto_signoff: bool = True" in lr
        print(f"L4 live_runner mock_cli+auto_signoff={mock_hardcoded}")
        rows.append(("l4_still_mock", mock_hardcoded, True))

        fake_home = Path(tempfile.mkdtemp(prefix="r6_home_"))
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

        schema = json.loads(Path("/home/debian/macao/src/macao/schemas/dev_manifest.schema.json").read_text())
        sha_schema = schema["properties"]["full_document"]["properties"]["sha256"]
        ev_schema = schema["properties"]["full_document"]["properties"]["evidence_commit"]
        sha_loose = sha_schema == {"type": "string"} and "pattern" not in sha_schema and "minLength" not in sha_schema
        ev_loose = ev_schema == {"type": "string"} and "pattern" not in ev_schema and "minLength" not in ev_schema
        print(f"SCHEMA sha256={sha_schema} evidence_commit={ev_schema}")
        rows.append(("schema_sha256_still_unpatterned", sha_loose, True))
        rows.append(("schema_evidence_commit_still_unpatterned", ev_loose, True))

        # UC-11 E1 ghost baseline
        os.chdir(tmp)
        db_mod._db_manager = None
        (tmp / "docs" / "reviews" / "ghost-req.md").write_text("# ghost\n")
        git(tmp, "add", "docs/reviews/ghost-req.md")
        git(tmp, "commit", "-m", "ghost req")
        runner = CliRunner()
        res_adopt = runner.invoke(cli, ["task", "adopt", "--from-request", "docs/reviews/ghost-req.md", "--dry-run"])
        # dry-run may not hit E1; hit live adopt with fake baseline by writing request that claims deadbeef
        print(f"ADOPT dry-run rc={res_adopt.exit_code}")
        os.chdir(orig)
        db_mod._db_manager = None

        atmp = Path(tempfile.mkdtemp(prefix="r6_adopt_"))
        try:
            git(atmp, "init", "-b", "main")
            git(atmp, "config", "user.name", "t")
            git(atmp, "config", "user.email", "t@t.dev")
            (atmp / "README.md").write_text("x\n")
            git(atmp, "add", "README.md")
            git(atmp, "commit", "-m", "init")
            cfg2 = yaml.safe_load(DEFAULT_CONFIG_TEMPLATE)
            cfg2["team"]["executor"] = {"id": "dev-mock", "cli": "mock-cli", "adapter": "pty-wrapper"}
            cfg2["team"]["reviewers"] = [{"id": "r1", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1}]
            (atmp / "macao.yaml").write_text(yaml.dump(cfg2))
            reqp = atmp / "docs" / "reviews" / "2026-09-10-review-request-deadbeef.md"
            reqp.parent.mkdir(parents=True)
            reqp.write_text("# Request\n\ncheckpoint_ref: deadbeefdeadbeefdeadbeefdeadbeefdeadbeef\n", encoding="utf-8")
            os.chdir(atmp)
            db_mod._db_manager = None
            res_e1 = runner.invoke(cli, ["task", "adopt", "--from-request", str(reqp), "--no-review"])
            print(f"UC11 adopt ghost rc={res_e1.exit_code} out={res_e1.output[-400:]!r}")
            rows.append(("uc11_e1_ghost_nonzero", res_e1.exit_code != 0, True))
        finally:
            os.chdir(orig)
            db_mod._db_manager = None
            shutil.rmtree(atmp, ignore_errors=True)

        dtmp = Path(tempfile.mkdtemp(prefix="r6_doc_"))
        try:
            os.chdir(dtmp)
            res_doc = runner.invoke(cli, ["doctor"])
            print(f"DOCTOR missing yaml rc={res_doc.exit_code}")
            rows.append(("doctor_missing_yaml_rc2", res_doc.exit_code == 2, True))
        finally:
            os.chdir(orig)

        print("---- RESULTS ----")
        bad = []
        for name, actual, expected in rows:
            ok = actual == expected
            print(f"{'OK' if ok else 'FAIL'} {name}: actual={actual} expected={expected}")
            if not ok:
                bad.append(name)
        print("ALL_MATCH" if not bad else "MISMATCH")
        print("bad=" + ",".join(bad))
        return 0 if not bad else 1
    finally:
        os.chdir(orig)
        db_mod._db_manager = None
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(tmp.parent / (tmp.name + "-evil"), ignore_errors=True)
        shutil.rmtree(tmp.parent / (tmp.name + "_sibling"), ignore_errors=True)
        if dtmp is not None:
            shutil.rmtree(dtmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
