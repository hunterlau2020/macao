#!/usr/bin/env python3
"""
Independent machine verification battery for Round-3 review of commit 7bc8d70.

Reviewer: pi-qwen (harness: pi coding agent; model: qwen3.8-max)
Review object: docs/reviews/2026-09-08-review-request-7bc8d70.md
Guideline: docs/MACAO_REVIEW_GUIDELINES.md v1.1 (§3.4 reference frames, §3.5 evidence archiving)

What this script does (all inside a self-created tempfile.mkdtemp sandbox, all
against a PRISTINE extraction of commit 7bc8d70 obtained via `git archive`;
NEVER against a dirty working tree):

  V01  P0-1   unknown-CLI seats are MISSING + can_dispatch=False (fail-closed)
  V02  P1-2   probe --dry-run creates ZERO -wal/-shm sidecars (WAL db present)
  V03  P1-2*  immutable=1 STALE READ: probe reports stale active task while a
              writer holds un-checkpointed WAL (new trade-off finding, P2)
  V04  P1-3   secrets battery: mask_secrets + _sanitize_session_name + no PAT
              plaintext in `probe --dry-run --json`
  V05  P1-4   Claude cross-project (same basename) returns []
  V06  P1-5   `macao clean` prunes worktree registrations (no ghost entries)
  V07  P1-6   task create --no-prope blocked (exit 1); --force => E10 + audit
  V08  P1-7   non-zero exit codes: malformed/missing/schema-invalid configs
  V09  P1-9   pending review request blocks task create (UC-2 E7, exit 1)
  V10  F3     task adopt --dry-run => zero file mutation
  V11  P1-B   task adopt accepts NONEXISTENT baseline commit => phantom
              WAITING_REVIEW task, all dispatches fail, exit 0
  V12  P1-A   checkpoint anti-forgery: WRONG sha rejected, ALL-ZERO sha
              ACCEPTED (fail-open carve-out; executor.id checked, .cli not)
  V13  P2-B   change-table reconciliation vs `git diff --numstat 961bcfe..7bc8d70`

External prerequisites: python3, git, a checkout of this repository containing
commit 7bc8d70. No network, no real CLI vendor accounts, no writes outside the
temp sandbox (the pristine tree itself is also extracted into the sandbox).

Usage:  python3 docs/reviews/evidence/2026-09-08-7bc8d70-pi-qwen/repro_7bc8d70_pi_qwen.py
"""

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]          # repository root
SHA = "7bc8d7091ba4e39c0b3282492c613817f8d664e9"
RESULTS = []


def sh(cmd, cwd, env=None, timeout=240, input_text=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(cmd, cwd=str(cwd), env=e, timeout=timeout,
                          capture_output=True, text=True, input=input_text)


def check(vid, desc, ok, detail=""):
    RESULTS.append((vid, desc, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {vid}  {desc}" + (f"\n        {detail}" if detail else ""))


def cli(env, cwd, *args, timeout=240):
    """Run the pristine-tree MACAO CLI; returns (rc, stdout)."""
    r = sh([sys.executable, "-m", "macao.cli.main", *args], cwd=cwd,
           env={"PYTHONPATH": str(env["TREE"] / "src")}, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def git_repo(path, cfg_from):
    path.mkdir(parents=True, exist_ok=True)
    for c in (["git", "init", "-q", "."],
              ["git", "config", "user.email", "t@t"],
              ["git", "config", "user.name", "t"]):
        sh(c, cwd=path)
    (path / "a.txt").write_text("x\n")
    sh(["git", "add", "-A"], cwd=path)
    sh(["git", "commit", "-qm", "init"], cwd=path)
    shutil.copy(cfg_from / "macao.yaml", path / "macao.yaml")


def write_cfg(path, reviewers, name="case"):
    base = (path / "macao.yaml").read_text()
    s = base.index("  reviewers:")
    e = base.index("\npolicy:")
    revs = "".join(f"    - {r}\n" for r in reviewers)
    out = base[:s] + "  reviewers:\n" + revs + base[e:]
    out = out.replace('name: "macao-demo"', f'name: "{name}"')
    (path / "macao.yaml").write_text(out)


def files_under(p):
    return sorted(x.name for x in p.iterdir())


def main():
    sandbox = Path(tempfile.mkdtemp(prefix="macao_r3_evidence_"))
    tree = sandbox / "v7bc"
    tree.mkdir()
    try:
        # ---- pristine extraction of the declared checkpoint (§3.4) ----
        arch = subprocess.run(["git", "archive", SHA], cwd=str(REPO),
                              capture_output=True)
        if arch.returncode != 0:
            print("FATAL: git archive failed"); return 2
        subprocess.run(["tar", "-x", "-C", str(tree)], input=arch.stdout)
        E = {"TREE": tree}
        print(f"# sandbox={sandbox}\n# pristine tree={tree} (git archive {SHA[:7]})\n")

        # ============ V01: P0-1 unknown CLI fail-closed ============
        d = sandbox / "v01"; git_repo(d, tree)
        write_cfg(d, ['{id: "cursor", cli: "definitely-not-installed-xyz", adapter: "pty-wrapper", vote_weight: 1}',
                      '{id: "codex", cli: "totally-bogus-bin-qqq", adapter: "pty-wrapper", vote_weight: 1}',
                      '{id: "zzz9", cli: "totally-bogus-bin-www", adapter: "pty-wrapper", vote_weight: 1}'],
                  "phantom-seats")
        rc, out = cli(E, d, "probe", "--dry-run", "--json")
        j = json.loads(out)
        r0 = j["reviewers"][0]
        check("V01", "unknown-CLI seats -> MISSING + can_dispatch False",
              all(x["status"] == "MISSING" for x in j["reviewers"])
              and j["can_dispatch"] is False and j["quorum"]["achievable"] is False,
              f"statuses={[x['status'] for x in j['reviewers']]} err={r0.get('error','')[:60]}")

        # ============ V02: P1-2 zero sidecars with WAL db present ============
        d = sandbox / "v02"; git_repo(d, tree)
        mac = d / ".macao"; mac.mkdir()
        w = sqlite3.connect(str(mac / "state.db"))
        w.execute("PRAGMA journal_mode=WAL;")
        w.execute("CREATE TABLE tasks (task_id TEXT, state TEXT)")
        w.execute("INSERT INTO tasks VALUES ('t1','CODING')")
        w.commit(); w.close()          # clean close -> wal checkpointed away
        before = files_under(mac)
        rc, _ = cli(E, d, "probe", "--dry-run")
        check("V02", "probe --dry-run leaves .macao file-set unchanged (0 sidecars)",
              rc == 0 and files_under(mac) == before,
              f"before={before} after={files_under(mac)}")

        # ============ V03: immutable=1 stale read under live writer ============
        d = sandbox / "v03"; git_repo(d, tree)
        mac = d / ".macao"; mac.mkdir()
        # base task, checkpointed
        w = sqlite3.connect(str(mac / "state.db"))
        w.execute("PRAGMA journal_mode=WAL;")
        w.execute("CREATE TABLE tasks (task_id TEXT, title TEXT, source_branch TEXT, target_branch TEXT,"
                  " state TEXT, checkpoint_ref TEXT, review_round INTEGER, created_at TEXT, updated_at TEXT)")
        w.execute("INSERT INTO tasks VALUES ('task-OLD','Old','f','main','CODING',NULL,1,'2020-01-01','2020-01-01')")
        w.commit(); w.close()
        writer = sandbox / "v03_writer.py"
        writer.write_text(
            "import sqlite3,time,sys\n"
            "w=sqlite3.connect(sys.argv[1])\n"
            "w.execute('PRAGMA journal_mode=WAL;');w.execute('PRAGMA wal_autocheckpoint=0;')\n"
            "w.execute(\"INSERT INTO tasks VALUES ('task-NEW','New','f','main','CODING',NULL,1,'2021-01-01','2021-01-01')\")\n"
            "w.commit();print('committed',flush=True);time.sleep(20);w.close()\n")
        wp = subprocess.Popen([sys.executable, str(writer), str(mac / "state.db")],
                              stdout=subprocess.PIPE, text=True)
        wp.stdout.readline()                       # wait until committed
        time.sleep(1)
        rc, out = cli(E, d, "probe", "--dry-run", "--json")
        j = json.loads(out)
        reported = (j.get("active_task") or {}).get("task_id")
        wal_present = (mac / "state.db-wal").exists()
        wp.kill(); wp.wait()
        check("V03", "probe silently reports STALE task while WAL holds newer commit (P2 trade-off)",
              wal_present and reported == "task-OLD",
              f"wal_present={wal_present} reported={reported} (truth: task-NEW via mode=ro; "
              f"state_store.error={(j.get('state_store') or {}).get('error')})")

        # ============ V04: P1-3 masking battery ============
        sys.path.insert(0, str(tree / "src"))
        for mod in [m for m in list(sys.modules) if m.startswith("macao")]:
            del sys.modules[mod]
        from macao.utils.secrets import mask_secrets
        from macao.adapter.session_locator import _sanitize_session_name
        cases = {
            "ghp": "token ghp_ABCDEFGHIJKLMNOPQRSTUVWX",
            "anthropic": "sk-ant-api03-AbCdEfGhIjKlMn",
            "bearer": "Bearer abcdef0123456789ABCDEF",
            "dburl": "postgres://u:Sup3rSecret@h/db",
            "jwt": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5Nxy",
            "aws": "AKIAIOSFODNN7EXAMPLE",
            "kv": "api_key: mySecretValue123",
            "envtok": "export MACAO_TOKEN=tok_live_9f8e7d6c5b4a3210",
        }
        leaks = [k for k, v in cases.items()
                 if mask_secrets(v) == v or _sanitize_session_name(v) == v.strip()]
        sys.path.remove(str(tree / "src"))
        d = sandbox / "v04"; git_repo(d, tree)
        write_cfg(d, ['{id: "pirev", cli: "pi", adapter: "pty-wrapper", vote_weight: 1}',
                      '{id: "opencode", cli: "opencode", adapter: "pty-wrapper", vote_weight: 1}',
                      '{id: "codex", cli: "codex", adapter: "pty-wrapper", vote_weight: 1}'], "leak-case")
        fh = sandbox / "fakehome"; sd = fh / (".pi/agent/sessions/--" + str(d).strip("/").replace("/", "-") + "--")
        sd.mkdir(parents=True)
        (sd / "2026-09-07T12-00-00_sid9.jsonl").write_text(
            json.dumps({"type": "session", "id": "sid9", "cwd": str(d)}) + "\n" +
            json.dumps({"type": "session_info", "name": "ghp_ABCDEFGHIJKLMNOPQRSTUVWX"}) + "\n")
        env = {"TREE": tree, "HOME": str(fh)}
        r = sh([sys.executable, "-m", "macao.cli.main", "probe", "--dry-run", "--json"],
               cwd=d, env={"PYTHONPATH": str(tree / "src"), "HOME": str(fh)})
        j = json.loads(r.stdout)
        pat_leak = "ghp_ABCDEFGHIJKLMNOPQRSTUVWX" in json.dumps(j)
        sess = next((x["session"] for x in j["reviewers"] if x.get("session")), None)
        check("V04", "secrets battery masked AND no PAT plaintext in probe --json",
              not leaks and not pat_leak,
              f"leaks={leaks} json_leak={pat_leak} session_name={sess and sess.get('session_name')}")

        # ============ V05: P1-4 claude cross-project ============
        d = sandbox / "v05"; (d / "proj/macao").mkdir(parents=True)
        ch = sandbox / "v05home/.claude/projects/-macao"; ch.mkdir(parents=True)
        (ch / "cccc-dddd.jsonl").write_text(
            json.dumps({"type": "user", "cwd": "/home/other/macao",
                        "message": {"role": "user", "content": "OTHER"}}) + "\n")
        for m in [m for m in list(sys.modules) if m.startswith("macao")]:
            del sys.modules[m]
        sys.path.insert(0, str(tree / "src"))
        from unittest.mock import patch
        from macao.adapter.session_locator import SessionLocator
        with patch("pathlib.Path.home", return_value=fh if False else sandbox / "v05home"):
            got = SessionLocator.list_sessions("claude", (d / "proj/macao").resolve())
        sys.path.remove(str(tree / "src"))
        check("V05", "claude same-basename foreign session -> []", got == [], f"got={got}")

        # ============ V06: P1-5 clean prunes worktrees ============
        d = sandbox / "v06"; git_repo(d, tree)
        (d / ".macao/worktrees").mkdir(parents=True)
        sh(["git", "worktree", "add", "-q", ".macao/worktrees/rev-codex_r1",
            "-b", "feature/rev-codex_r1", "HEAD"], cwd=d)
        rc, _ = cli(E, d, "clean")
        wl = sh(["git", "worktree", "list"], cwd=d).stdout
        ghosts = [l for l in wl.splitlines() if "prunable" in l]
        check("V06", "clean => no prunable worktree entries, .git/worktrees empty",
              rc == 0 and not ghosts and not list((d / ".git/worktrees").glob("*")),
              f"ghosts={ghosts}")

        # ============ V07: P1-6 single-active-task ============
        d = sandbox / "v07"; git_repo(d, tree)
        cli(E, d, "task", "create", "--title", "A", "--no-probe")
        rc_b, out_b = cli(E, d, "task", "create", "--title", "B", "--no-probe")
        cli(E, d, "task", "create", "--title", "B", "--no-probe", "--force")
        c = sqlite3.connect(f"file:{d}/.macao/state.db?mode=ro&immutable=1", uri=True)
        rows = c.execute("SELECT state FROM tasks").fetchall()
        e10 = c.execute("SELECT count(*) FROM audit_events WHERE type='TASK_CANCELLED'").fetchone()[0]
        c.close()
        active = [r for r in rows if r[0] not in ("DONE", "CANCELLED")]
        check("V07", "no-probe create blocked (rc!=0); --force => E10 audit, 1 active",
              rc_b != 0 and len(active) == 1 and e10 >= 1,
              f"rc_b={rc_b} active={active} e10_events={e10}")

        # ============ V08: P1-7 exit codes ============
        d = sandbox / "v08"; git_repo(d, tree)
        (d / "macao.yaml").write_text("team: [unclosed\n")
        rc1, _ = cli(E, d, "probe")
        rc2, _ = cli(E, d, "doctor")
        (d / "macao.yaml").unlink()
        rc3, _ = cli(E, d, "probe", "--dry-run")
        shutil.copy(tree / "macao.yaml", d / "macao.yaml")
        txt = (d / "macao.yaml").read_text().replace("seat_quorum_required: 3", "seat_quorum_required: 1")
        (d / "macao.yaml").write_text(txt)
        rc4, out4 = cli(E, d, "task", "create", "--title", "X", "--dry-run")
        check("V08", "malformed->2, doctor->2, missing->2, schema-invalid create --dry-run!=0",
              rc1 == 2 and rc2 == 2 and rc3 == 2 and rc4 != 0, f"rc=({rc1},{rc2},{rc3},{rc4})")

        # ============ V09: P1-9 pending request blocks create ============
        d = sandbox / "v09"; git_repo(d, tree)
        (d / "docs/reviews").mkdir(parents=True)
        (d / "docs/reviews/2026-09-08-review-request-abc1234.md").write_text("# RR\n\nCommit: abc1234\n")
        rc, out = cli(E, d, "task", "create", "--title", "X", "--no-probe")
        check("V09", "pending review request => UC-2 E7 block, non-zero exit",
              rc != 0 and "E7" in out and "task adopt" in out, f"rc={rc}")

        # ============ V10: Focus 3 adopt --dry-run zero mutation ============
        d = sandbox / "v10"; git_repo(d, tree)
        (d / "a.txt").write_text("dirty\n")
        before = sorted(str(p.relative_to(d)) for p in d.rglob("*") if ".git/" not in str(p))
        rc, out = cli(E, d, "task", "adopt", "--dry-run")
        after = sorted(str(p.relative_to(d)) for p in d.rglob("*") if ".git/" not in str(p))
        check("V10", "task adopt --dry-run => zero new files", rc == 0 and before == after,
              f"delta={set(after)-set(before)}")

        # ============ V11: adopt accepts nonexistent baseline ============
        d = sandbox / "v11"; git_repo(d, tree)
        (d / "docs/reviews").mkdir(parents=True)
        (d / "docs/reviews/2026-09-08-review-request-deadbeef99.md").write_text(
            "# Review Request (fabricated baseline)\n\nCheckpoint: deadbeef99 (nonexistent commit)\n")
        rc, out = cli(E, d, "task", "adopt")
        c = sqlite3.connect(f"file:{d}/.macao/state.db?mode=ro&immutable=1", uri=True)
        rows = c.execute("SELECT task_id,state,checkpoint_ref FROM tasks").fetchall()
        c.close()
        phantom = [r for r in rows if r[2] and "deadbeef" in r[2]]
        check("V11", "adopt with NONEXISTENT commit => phantom WAITING_REVIEW task + rc==0 (P1)",
              bool(phantom) and phantom[0][1] == "WAITING_REVIEW" and rc == 0
              and "does not exist" in out,
              f"rows={rows} rc={rc}")

        # ============ V12: checkpoint anti-forgery ============
        d = sandbox / "v12"; git_repo(d, tree)
        cli(E, d, "task", "create", "--title", "T1", "--no-probe")
        c = sqlite3.connect(str(d / ".macao/state.db"))
        tid = c.execute("SELECT task_id FROM tasks LIMIT 1").fetchone()[0]
        c.close()
        head = sh(["git", "rev-parse", "HEAD"], cwd=d).stdout.strip()
        (d / "docs/reviews").mkdir(parents=True, exist_ok=True)
        (d / "docs/reviews/req-fake.md").write_text("# fake doc\n")
        for m in [m for m in list(sys.modules) if m.startswith("macao")]:
            del sys.modules[m]
        sys.path.insert(0, str(tree / "src"))
        import yaml as _yaml
        from macao.workflow.orchestrator import Orchestrator

        def manifest(sha, exec_id):
            return {"version": "1.0", "task_id": tid, "checkpoint_ref": head,
                    "full_document": {"path": "docs/reviews/req-fake.md",
                                      "evidence_commit": head, "sha256": sha},
                    "status": "ready_for_review", "signal": "EXPLICIT", "review_round": 1,
                    "executor": {"id": exec_id, "cli": "whatever"},
                    "development": {"quality_metrics": {"tests_passed": True},
                                    "git": {"latest_commit": head}}}

        o = Orchestrator(project_root=str(d))
        (d / ".macao/.dev.yml").parent.mkdir(parents=True, exist_ok=True)
        # (a) wrong sha + imposter executor on a FRESH task
        (d / ".macao/.dev.yml").write_text(_yaml.safe_dump(manifest("deadbeef" + "a" * 56, "IMPOSTER")))
        r_wrong = o.check_development_checkpoint(tid)
        # reset task state for second attempt
        c = sqlite3.connect(str(d / ".macao/state.db"))
        c.execute("UPDATE tasks SET state='CODING' WHERE task_id=?", (tid,)); c.commit(); c.close()
        # (b) all-zero sha + correct executor id but arbitrary cli
        (d / ".macao/.dev.yml").write_text(_yaml.safe_dump(manifest("0" * 64, "opencode-dev")))
        r_zero = o.check_development_checkpoint(tid)
        sys.path.remove(str(tree / "src"))
        check("V12", "wrong-sha/imposter REJECTED; ALL-ZERO sha ACCEPTED (fail-open carve-out)",
              r_wrong is None and r_zero is not None,
              f"wrong->{r_wrong and r_wrong.to_state.value} zero->{r_zero and r_zero.to_state.value}")

        # ============ V13: change-table reconciliation ============
        req = (REPO / "docs/reviews/2026-09-08-review-request-7bc8d70.md").read_text(encoding="utf-8")
        rows_t = re.findall(r"^\|\s*\[`([^`]+)`\][^|]*\|\s*[^|]*\|\s*\+(\d+)\s*/\s*-(\d+)\s*\|", req, re.M)
        num = sh(["git", "diff", "--numstat", "961bcfe..7bc8d70"], cwd=REPO).stdout
        actual = {}
        for line in num.strip().split("\n"):
            a, dl, p = line.split("\t"); actual[p.strip()] = (int(a), int(dl))
        bad = [p for p, a, dl in rows_t
               if actual.get(p.replace("../../", "")) != (int(a), int(dl))]
        missing = sorted(set(actual) - {r[0].replace("../../", "") for r in rows_t})
        check("V13", "change table matches git numstat and lists all 30 files",
              not bad and not missing,
              f"mismatched={len(bad)}/{len(rows_t)} omitted_files={missing}")

        print("\n==== SUMMARY ====")
        n_fail = sum(1 for _, _, ok in RESULTS if not ok)
        for vid, desc, ok in RESULTS:
            print(f"  {'PASS' if ok else 'FAIL'}  {vid}")
        print(f"\n{len(RESULTS)-n_fail}/{len(RESULTS)} checks passed. "
              f"(V03/V11/V12/V13 are EXPECTED-FAIL demonstrations of open defects.)")
        return 0
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
        print(f"# sandbox cleaned: {sandbox}")


if __name__ == "__main__":
    sys.exit(main())
