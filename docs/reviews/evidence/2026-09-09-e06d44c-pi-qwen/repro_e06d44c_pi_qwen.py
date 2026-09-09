#!/usr/bin/env python3
"""
Independent machine verification battery for Round-4 review of commit e06d44c.

Reviewer: pi-qwen (harness: pi coding agent; model: qwen3.8-max)
Review object: docs/reviews/2026-09-09-review-request-e06d44c.md
Guideline: docs/MACAO_REVIEW_GUIDELINES.md v1.1 (§3.4 reference frames, §3.5 archiving)

Checks (all against a PRISTINE `git archive e06d44c` extraction inside a
self-created tempfile.mkdtemp sandbox; never a dirty working tree):

  G01  checkpoint gate: 14 counter-examples rejected, happy path advances,
      e2e `task checkpoint --auto --test-cmd` passes the strict gate
  G02  adopt: nonexistent baseline -> exit 1 + state.db NOT created;
      valid dirty-dev adopt -> CODING via audited E1_ADOPT
  G03  EXECUTOR acceptance drop: 5 of 7 adapters drop acceptance_criteria
      (antigravity/claude/codex/kimi/opencode); pi/cursor fixed  <- P1-2
  G04  immutable=1 stale read still present (R3 P2-A carry-over)   <- P2-1
  G05  request metadata: claimed full SHA resolves? envelope sha vs actual?
      request doc present inside evidence_commit?                 <- P1-1
  G06  change table: 21/21 rows match git numstat exactly (R3 P2-B closed)

External prerequisites: python3 (3.10+), git, checkout containing e06d44c.
No network, no vendor CLI accounts, no writes outside the sandbox.

Usage: python3 docs/reviews/evidence/2026-09-09-e06d44c-pi-qwen/repro_e06d44c_pi_qwen.py
"""

import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SHA = "e06d44c"          # short SHA (the request's 40-char "full SHA" is tested in G05)
RESULTS = []


def sh(cmd, cwd, env=None, timeout=300):
    e = dict(os_environ())
    if env:
        e.update(env)
    return subprocess.run(cmd, cwd=str(cwd), env=e, timeout=timeout,
                          capture_output=True, text=True)


def os_environ():
    import os
    return os.environ


def check(gid, desc, ok, detail=""):
    RESULTS.append((gid, desc, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {gid}  {desc}" + (f"\n        {detail}" if detail else ""))


def cli(tree, cwd, *args, timeout=300):
    r = sh([sys.executable, "-m", "macao.cli.main", *args], cwd,
           env={"PYTHONPATH": str(tree / "src")}, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def git_repo(path, cfg_from):
    path.mkdir(parents=True, exist_ok=True)
    for c in (["git", "init", "-q", "."], ["git", "config", "user.email", "t@t"],
              ["git", "config", "user.name", "t"]):
        sh(c, cwd=path)
    (path / "a.txt").write_text("x\n")
    sh(["git", "add", "-A"], cwd=path)
    sh(["git", "commit", "-qm", "init"], cwd=path)
    shutil.copy(cfg_from / "macao.yaml", path / "macao.yaml")


def main():
    sandbox = Path(tempfile.mkdtemp(prefix="macao_r4_evidence_"))
    tree = sandbox / "v4"
    tree.mkdir()
    try:
        arch = subprocess.run(["git", "archive", SHA], cwd=str(REPO), capture_output=True)
        if arch.returncode != 0:
            print("FATAL: git archive failed")
            return 2
        subprocess.run(["tar", "-x", "-C", str(tree)], input=arch.stdout)
        print(f"# sandbox={sandbox}\n# pristine tree={tree} (git archive {SHA})\n")

        # ---------------- G01: checkpoint gate battery ----------------
        d = sandbox / "g1"; git_repo(d, tree)
        cli(tree, d, "task", "create", "--title", "T1", "--no-probe")
        code = f'''
import sys, hashlib, pathlib, sqlite3, yaml, subprocess
sys.path.insert(0, "{tree}/src")
d = pathlib.Path("{d}")
c = sqlite3.connect(str(d/'.macao/state.db')); tid = c.execute("SELECT task_id FROM tasks LIMIT 1").fetchone()[0]
c.execute("UPDATE tasks SET state='CODING' WHERE task_id=?", (tid,)); c.commit(); c.close()
head = subprocess.run(['git','rev-parse','HEAD'], cwd=str(d), capture_output=True, text=True).stdout.strip()
doc = d/'docs/reviews/req.md'; doc.parent.mkdir(parents=True, exist_ok=True); doc.write_text('# doc\\n')
true_sha = hashlib.sha256(doc.read_bytes()).hexdigest()
def m(**o):
    b = {{"version":"1.0","task_id":tid,"checkpoint_ref":head,
         "full_document":{{"path":"docs/reviews/req.md","evidence_commit":head,"sha256":true_sha}},
         "status":"ready_for_review","signal":"EXPLICIT","review_round":1,
         "executor":{{"id":"opencode-dev","cli":"opencode"}},
         "development":{{"quality_metrics":{{"tests_passed":True}},"git":{{"latest_commit":head}}}}}}
    for k,v in o.items():
        if k=="sha": b["full_document"]["sha256"]=v
        elif k=="exec_id": b["executor"]["id"]=v
        elif k=="exec_cli": b["executor"]["cli"]=v
        elif k=="path": b["full_document"]["path"]=v
        elif k=="quality": b["development"]["quality_metrics"]=v
        elif k=="round": b["review_round"]=v
        elif k=="ec": b["full_document"]["evidence_commit"]=v
        else: b[k]=v
    return b
from macao.workflow.orchestrator import Orchestrator
def att(name, mm):
    (d/'.macao/.dev.yml').write_text(yaml.safe_dump(mm))
    o = Orchestrator(project_root=str(d)); r = o.check_development_checkpoint(tid)
    adv = r is not None
    if adv:
        cc=sqlite3.connect(str(d/'.macao/state.db')); cc.execute("UPDATE tasks SET state='CODING' WHERE task_id=?", (tid,)); cc.commit(); cc.close()
    print(f"{{name}}={{adv}}")
att("happy", m())
att("zero_sha", m(sha="0"*64)); att("empty_sha", m(sha="")); att("nonhex", m(sha="z"*64)); att("len63", m(sha="a"*63))
att("tampered", m(sha=hashlib.sha256(b'other').hexdigest())); att("missing_file", m(path="docs/reviews/nope.md"))
att("escape", m(path="../../../../etc/hosts")); att("imposter_id", m(exec_id="IMPOSTER"))
att("wrong_cli", m(exec_cli="not-opencode")); att("tests_false", m(quality={{"tests_passed":False}}))
att("round2", m(round=2)); att("other_task", m(task_id="task-OTHER")); att("ec_mismatch", m(ec="0"*40))
'''
        r = sh([sys.executable, "-c", code], cwd=d)
        kv = dict(re.findall(r"(\w+)=(True|False)", r.stdout))
        rejects = all(kv.get(k) == "False" for k in
                      ["zero_sha", "empty_sha", "nonhex", "len63", "tampered",
                       "missing_file", "escape", "imposter_id", "wrong_cli",
                       "tests_false", "round2", "other_task", "ec_mismatch"])
        # e2e checkpoint --auto through the strict gate
        d2 = sandbox / "g1e"; git_repo(d2, tree)
        cli(tree, d2, "task", "create", "--title", "T1", "--no-probe")
        (d2 / "a.txt").write_text("wip\n")
        sh(["git", "add", "-A"], cwd=d2); sh(["git", "commit", "-qm", "feat"], cwd=d2)
        rc, _ = cli(tree, d2, "task", "checkpoint", "--auto", "--test-cmd", "true", "--no-review")
        c = sqlite3.connect(str(d2 / ".macao/state.db"))
        st = c.execute("SELECT state FROM tasks LIMIT 1").fetchone()[0]; c.close()
        check("G01", "13 forge variants rejected; happy advances; checkpoint --auto e2e OK",
              rejects and kv.get("happy") == "True" and rc == 0 and st == "READY_FOR_REVIEW",
              f"kv={kv} e2e_state={st} rc={rc}")

        # ---------------- G02: adopt guard ----------------
        d = sandbox / "g2"; git_repo(d, tree)
        (d / "docs/reviews").mkdir(parents=True)
        (d / "docs/reviews/2026-09-09-review-request-deadbeef99.md").write_text(
            "# RR\n\nCheckpoint: deadbeef99\n")
        rc, out = cli(tree, d, "task", "adopt")
        no_db = not (d / ".macao/state.db").exists()
        check("G02a", "adopt nonexistent baseline -> rc!=0 and NO state.db written",
              rc != 0 and no_db and "does not exist" in out, f"rc={rc} state.db_absent={no_db}")
        d = sandbox / "g2b"; git_repo(d, tree)
        (d / "a.txt").write_text("wip\n")
        rc, out = cli(tree, d, "task", "adopt", "--no-review")
        c = sqlite3.connect(str(d / ".macao/state.db")); c.row_factory = sqlite3.Row
        t = c.execute("SELECT state FROM tasks LIMIT 1").fetchone()["state"]
        aud = [r[0] for r in c.execute("SELECT type FROM audit_events")]; c.close()
        check("G02b", "valid adopt -> CODING via audited E1_ADOPT",
              rc == 0 and t == "CODING" and any("E1_ADOPT" in a for a in aud),
              f"state={t} audit={aud[-3:]}")

        # ---------------- G03: executor acceptance drop ----------------
        code = f'''
from macao.adapter.antigravity import AntigravityAdapter
from macao.adapter.claude import ClaudeCodeAdapter
from macao.adapter.codex import CodexAdapter
from macao.adapter.kimi import KimiAdapter
from macao.adapter.opencode import OpenCodeAdapter
from macao.adapter.pi import PiAdapter
from macao.adapter.cursor import CursorAgentAdapter
MARK = "MUST_REACH_EXECUTOR"
class Cap:
    def __init__(self): self.prompts=[]
    def write_input(self, p): self.prompts.append(p); return True
for cls in (AntigravityAdapter, ClaudeCodeAdapter, CodexAdapter, KimiAdapter, OpenCodeAdapter, PiAdapter, CursorAgentAdapter):
    a = cls(agent_id="x", config={{"role":"executor"}}); a.session = Cap(); a.is_running = True
    a.inject_task({{"task_description":"build", "acceptance_criteria":[MARK]}})
    print(cls.__name__, MARK in a.session.prompts[-1])
'''
        r = sh([sys.executable, "-c", code], cwd=sandbox, env={"PYTHONPATH": str(tree / "src")})
        kv = dict(re.findall(r"(\w+) (True|False)", r.stdout))
        droppers = [k for k, v in kv.items() if v == "False"]
        check("G03", "executor acceptance_criteria reaches prompts (P1-2 when FAIL)",
              not droppers, f"dropping_adapters={droppers}")

        # ---------------- G04: immutable stale read ----------------
        d = sandbox / "g4"; git_repo(d, tree)
        (d / ".macao").mkdir(exist_ok=True)
        w = sqlite3.connect(str(d / ".macao/state.db"))
        w.execute("PRAGMA journal_mode=WAL;")
        w.execute("CREATE TABLE tasks (task_id TEXT, title TEXT, source_branch TEXT, target_branch TEXT,"
                  " state TEXT, checkpoint_ref TEXT, review_round INTEGER, created_at TEXT, updated_at TEXT)")
        w.execute("INSERT INTO tasks VALUES ('task-OLD','Old','f','main','CODING',NULL,1,'2020-01-01','2020-01-01')")
        w.commit(); w.close()
        wp = sandbox / "g4w.py"
        wp.write_text("import sqlite3,time,sys\nw=sqlite3.connect(sys.argv[1])\n"
                      "w.execute('PRAGMA journal_mode=WAL;');w.execute('PRAGMA wal_autocheckpoint=0;')\n"
                      "w.execute(\"INSERT INTO tasks VALUES ('task-NEW','N','f','main','CODING',NULL,1,'2021-01-01','2021-01-01')\")\n"
                      "w.commit();print('ok',flush=True);time.sleep(15);w.close()\n")
        proc = subprocess.Popen([sys.executable, str(wp), str(d / ".macao/state.db")],
                                stdout=subprocess.PIPE, text=True)
        proc.stdout.readline(); time.sleep(1)
        rc, out = cli(tree, d, "probe", "--dry-run", "--json")
        j = json.loads(out)
        rep = (j.get("active_task") or {}).get("task_id")
        wal = (d / ".macao/state.db-wal").exists()
        proc.kill(); proc.wait()
        check("G04", "no stale read under live WAL writer (P2-1 carry-over when FAIL)",
              not (wal and rep == "task-OLD"), f"wal={wal} reported={rep}")

        # ---------------- G05: request metadata integrity ----------------
        req = REPO / "docs/reviews/2026-09-09-review-request-e06d44c.md"
        txt = req.read_text(encoding="utf-8")
        claimed_full = re.search(r"完整 SHA：`([0-9a-f]{40})`", txt).group(1)
        # NOTE: `git rev-parse --verify` only checks SYNTAX for full hex; `cat-file -t`
        # is the existence proof (verified: claimed SHA -> fatal: could not get object info).
        resolves = subprocess.run(["git", "cat-file", "-t", claimed_full],
                                  cwd=str(REPO), capture_output=True).returncode == 0
        real_full = sh(["git", "rev-parse", SHA], cwd=REPO).stdout.strip()
        claimed_sha = re.search(r"sha256:\s*\"([0-9a-f]{64})\"", txt).group(1)
        actual_sha = hashlib.sha256(req.read_bytes()).hexdigest()
        in_commit = sh(["git", "cat-file", "-e", f"{SHA}:docs/reviews/2026-09-09-review-request-e06d44c.md"],
                       cwd=REPO).returncode == 0
        check("G05", "claimed full SHA resolves; envelope sha == actual; doc in evidence_commit (P1-1 when FAIL)",
              resolves and claimed_sha == actual_sha and in_commit,
              f"claimed_full={claimed_full[:12]}… resolves={resolves} real={real_full[:12]}… "
              f"envelope_sha={claimed_sha[:12]}… actual={actual_sha[:12]}… doc_in_{SHA}={in_commit}")

        # ---------------- G06: change table reconciliation ----------------
        rows = re.findall(r"^\|\s*`([^`]+)`\s*\|[^|]*\|\s*\+(\d+)\s*/\s*-(\d+)\s*\|", txt, re.M)
        num = sh(["git", "diff", "--numstat", "7bc8d70..e06d44c"], cwd=REPO).stdout
        actual = {}
        for line in num.strip().split("\n"):
            a, dl, p = line.split("\t"); actual[p] = (int(a), int(dl))
        bad = [p for p, a, dl in rows if actual.get(p) != (int(a), int(dl))]
        check("G06", "change-table rows exactly match git numstat (R3 P2-B closed)",
              rows and not bad, f"rows={len(rows)} mismatched={bad}")

        print("\n==== SUMMARY ====")
        for gid, desc, ok in RESULTS:
            print(f"  {'PASS' if ok else 'FAIL'}  {gid}")
        return 0
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
        print(f"# sandbox cleaned: {sandbox}")


if __name__ == "__main__":
    sys.exit(main())
