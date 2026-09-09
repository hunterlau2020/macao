#!/usr/bin/env python3
"""
Independent machine verification battery for Round-5 review of commit bdc177e.

Reviewer: pi-qwen (harness: pi coding agent; model: qwen3.8-max)
Review object: docs/reviews/2026-09-09-review-request-bdc177e.md
Guideline: docs/MACAO_REVIEW_GUIDELINES.md v1.1 (§3.4 / §3.5)

Checks (all against a PRISTINE `git archive bdc177e` extraction inside a
self-created tempfile.mkdtemp sandbox):

  H01  checkpoint gate: 12 forge variants incl. SIBLING ESCAPE and EMPTY
      evidence_commit -> all rejected; happy path advances; e2e
      `task checkpoint --auto --test-cmd` passes the strict gate
  H02  git-blob check: disk tampered after commit (disk sha == manifest sha)
      -> rejected; untracked evidence doc (not in commit) -> passes
      (documented "当文件在对应 commit 存在时" precondition; P2 w/ Claude)
  H03  acceptance_criteria reaches 7/7 executor adapters   (R4 P1-2 CLOSED)
  H04  composition root: get_orchestrator wires executor adapter; unknown
      CLI -> None (fail-closed); mock executor task create completes  (CLOSED)
  H05  request metadata: real full SHA; §3.3 command rc=0; envelope sha256
      three-way match (disk == bdc177e blob == manifest); envelope sample
      passes validate_dev_manifest                       (R4 P1-1 CLOSED)
  H06  change table: 25/25 rows exactly match git numstat, 0 omitted
  H07  immutable=1 stale read still present (R4 P2-1 carry-over, MUST be
      registered per §8.3-2)                             <- binding condition

External prerequisites: python3 (3.10+), git, checkout containing bdc177e.
No network; no vendor accounts; PTY spawn tests use mock-cli ONLY
(a real-CLI spawn was observed once during exploratory testing and killed;
it is NOT part of this script).

Usage: python3 docs/reviews/evidence/2026-09-09-bdc177e-pi-qwen/repro_bdc177e_pi_qwen.py
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
SHA = "bdc177e"
FULL = "bdc177eaaff577e119093e686f2164bcc133f781"
RESULTS = []


def sh(cmd, cwd, env=None, timeout=300):
    import os
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(cmd, cwd=str(cwd), env=e, timeout=timeout,
                          capture_output=True, text=True)


def check(hid, desc, ok, detail=""):
    RESULTS.append((hid, desc, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {hid}  {desc}" + (f"\n        {detail}" if detail else ""))


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
    sandbox = Path(tempfile.mkdtemp(prefix="macao_r5_evidence_"))
    tree = sandbox / "v5"
    tree.mkdir()
    try:
        arch = subprocess.run(["git", "archive", SHA], cwd=str(REPO), capture_output=True)
        if arch.returncode != 0:
            print("FATAL: git archive failed"); return 2
        subprocess.run(["tar", "-x", "-C", str(tree)], input=arch.stdout)
        print(f"# sandbox={sandbox}\n# pristine tree={tree} (git archive {SHA})\n")

        # ---------------- H01: gate battery (sibling + empty ec included) ----------------
        sib = sandbox / "repo_sibling"; sib.mkdir()
        (sib / "evil.md").write_text("evil sibling\n")
        d = sandbox / "h1"; git_repo(d, tree)
        cli(tree, d, "task", "create", "--title", "T1", "--no-probe")
        code = f'''
import sys, hashlib, pathlib, sqlite3, yaml, subprocess
sys.path.insert(0, "{tree}/src")
d = pathlib.Path("{d}")
c = sqlite3.connect(str(d/'.macao/state.db')); tid = c.execute("SELECT task_id FROM tasks LIMIT 1").fetchone()[0]
c.execute("UPDATE tasks SET state='CODING' WHERE task_id=?", (tid,)); c.commit(); c.close()
doc = d/'docs/reviews/req.md'; doc.parent.mkdir(parents=True, exist_ok=True); doc.write_text('COMMITTED\\n')
subprocess.run(['git','add','-A'],cwd=str(d)); subprocess.run(['git','commit','-qm','doc'],cwd=str(d))
head = subprocess.run(['git','rev-parse','HEAD'],cwd=str(d),capture_output=True,text=True).stdout.strip()
true_sha = hashlib.sha256(doc.read_bytes()).hexdigest()
sib_sha = hashlib.sha256(pathlib.Path("{sib}/evil.md").read_bytes()).hexdigest()
def m(**o):
    b = {{"version":"1.0","task_id":tid,"checkpoint_ref":head,
         "full_document":{{"path":"docs/reviews/req.md","evidence_commit":head,"sha256":true_sha}},
         "status":"ready_for_review","signal":"EXPLICIT","review_round":1,
         "executor":{{"id":"opencode-dev","cli":"opencode"}},
         "development":{{"quality_metrics":{{"tests_passed":True}},"git":{{"latest_commit":head}}}}}}
    for k,v in o.items():
        if k=="sha": b["full_document"]["sha256"]=v
        elif k=="path": b["full_document"]["path"]=v
        elif k=="ec": b["full_document"]["evidence_commit"]=v
        elif k=="exec_id": b["executor"]["id"]=v
        elif k=="exec_cli": b["executor"]["cli"]=v
        elif k=="quality": b["development"]["quality_metrics"]=v
        elif k=="round": b["review_round"]=v
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
att("zero_sha", m(sha="0"*64)); att("empty_sha", m(sha="")); att("tampered", m(sha=hashlib.sha256(b'other').hexdigest()))
att("missing_file", m(path="docs/reviews/nope.md"))
att("sibling_escape", m(path="../../repo_sibling/evil.md", sha=sib_sha))
att("empty_ec", m(ec="")); att("imposter_id", m(exec_id="IMPOSTER")); att("wrong_cli", m(exec_cli="zzz"))
att("tests_false", m(quality={{"tests_passed":False}})); att("round2", m(round=2)); att("other_task", m(task_id="task-OTHER"))
'''
        r = sh([sys.executable, "-c", code], cwd=d)
        kv = dict(re.findall(r"(\w+)=(True|False)", r.stdout))
        variants = ["zero_sha", "empty_sha", "tampered", "missing_file",
                    "sibling_escape", "empty_ec", "imposter_id", "wrong_cli",
                    "tests_false", "round2", "other_task"]
        rejects = all(kv.get(k) == "False" for k in variants)
        d2 = sandbox / "h1e"; git_repo(d2, tree)
        cli(tree, d2, "task", "create", "--title", "T1", "--no-probe")
        (d2 / "a.txt").write_text("wip\n")
        sh(["git", "add", "-A"], cwd=d2); sh(["git", "commit", "-qm", "feat"], cwd=d2)
        rc, _ = cli(tree, d2, "task", "checkpoint", "--auto", "--test-cmd", "true", "--no-review")
        c = sqlite3.connect(str(d2 / ".macao/state.db"))
        st = c.execute("SELECT state FROM tasks LIMIT 1").fetchone()[0]; c.close()
        check("H01", "11 forge variants rejected (incl sibling escape & empty ec); happy + e2e OK",
              rejects and kv.get("happy") == "True" and rc == 0 and st == "READY_FOR_REVIEW",
              f"kv={kv} e2e={st}")

        # ---------------- H02: blob check ----------------
        d = sandbox / "h2"; git_repo(d, tree)
        cli(tree, d, "task", "create", "--title", "T1", "--no-probe")
        doc = d / "docs/reviews/req.md"; doc.parent.mkdir(parents=True, exist_ok=True)
        doc.write_text("VERSION A\n")
        sh(["git", "add", "-A"], cwd=d); sh(["git", "commit", "-qm", "A"], cwd=d)
        head = sh(["git", "rev-parse", "HEAD"], cwd=d).stdout.strip()
        doc.write_text("VERSION B tampered\n")            # disk != committed blob
        shaB = hashlib.sha256(doc.read_bytes()).hexdigest()
        code = f'''
import sys, pathlib, sqlite3, yaml
sys.path.insert(0, "{tree}/src")
d = pathlib.Path("{d}")
c = sqlite3.connect(str(d/'.macao/state.db')); tid = c.execute("SELECT task_id FROM tasks LIMIT 1").fetchone()[0]
c.execute("UPDATE tasks SET state='CODING' WHERE task_id=?", (tid,)); c.commit(); c.close()
head = "{head}"
man = {{"version":"1.0","task_id":tid,"checkpoint_ref":head,
       "full_document":{{"path":"docs/reviews/req.md","evidence_commit":head,"sha256":"{shaB}"}},
       "status":"ready_for_review","signal":"EXPLICIT","review_round":1,
       "executor":{{"id":"opencode-dev","cli":"opencode"}},
       "development":{{"quality_metrics":{{"tests_passed":True}},"git":{{"latest_commit":head}}}}}}
(d/'.macao/.dev.yml').write_text(yaml.safe_dump(man))
from macao.workflow.orchestrator import Orchestrator
o = Orchestrator(project_root=str(d)); r = o.check_development_checkpoint(tid)
print("tamper_adv=", r is not None)
u = d/'docs/reviews/untracked.md'; u.write_text('NEVER COMMITTED\\n')
import hashlib
man["full_document"] = {{"path":"docs/reviews/untracked.md","evidence_commit":head,"sha256":hashlib.sha256(u.read_bytes()).hexdigest()}}
(d/'.macao/.dev.yml').write_text(yaml.safe_dump(man))
c = sqlite3.connect(str(d/'.macao/state.db')); c.execute("UPDATE tasks SET state='CODING' WHERE task_id=?", (tid,)); c.commit(); c.close()
r2 = o.check_development_checkpoint(tid)
print("untracked_adv=", r2 is not None)
'''
        r = sh([sys.executable, "-c", code], cwd=d)
        tamper_adv = re.search(r"tamper_adv= (\w+)", r.stdout)
        untracked_adv = re.search(r"untracked_adv= (\w+)", r.stdout)
        check("H02", "blob-vs-disk tamper rejected; uncommitted evidence doc passes (documented skip)",
              tamper_adv and tamper_adv.group(1) == "False" and untracked_adv and untracked_adv.group(1) == "True",
              f"tamper={tamper_adv and tamper_adv.group(1)} untracked={untracked_adv and untracked_adv.group(1)}")

        # ---------------- H03: acceptance 7/7 ----------------
        code = f'''
from macao.adapter.antigravity import AntigravityAdapter
from macao.adapter.claude import ClaudeCodeAdapter
from macao.adapter.codex import CodexAdapter
from macao.adapter.kimi import KimiAdapter
from macao.adapter.opencode import OpenCodeAdapter
from macao.adapter.pi import PiAdapter
from macao.adapter.cursor import CursorAgentAdapter
MARK="MUST_REACH_EXECUTOR"
class Cap:
    def __init__(self): self.prompts=[]
    def write_input(self,p): self.prompts.append(p); return True
drops=[]
for cls in (AntigravityAdapter,ClaudeCodeAdapter,CodexAdapter,KimiAdapter,OpenCodeAdapter,PiAdapter,CursorAgentAdapter):
    a=cls(agent_id="x",config={{"role":"executor"}}); a.session=Cap(); a.is_running=True
    a.inject_task({{"task_description":"build","acceptance_criteria":[MARK]}})
    if MARK not in a.session.prompts[-1]: drops.append(cls.__name__)
print("drops=", drops)
'''
        r = sh([sys.executable, "-c", code], cwd=sandbox, env={"PYTHONPATH": str(tree / "src")})
        drops = re.search(r"drops= (\[.*?\])", r.stdout)
        check("H03", "acceptance_criteria reaches all 7 executor adapters (R4 P1-2 CLOSED)",
              drops and drops.group(1) == "[]", f"drops={drops and drops.group(1)}")

        # ---------------- H04: composition root ----------------
        d = sandbox / "h4"; git_repo(d, tree)
        cfg = (d / "macao.yaml").read_text()
        (d / "macao.yaml").write_text(cfg.replace('cli: "opencode"', 'cli: "mock-cli"', 1))
        code = f'''
import sys; sys.path.insert(0, "{tree}/src")
from macao.cli.main import get_orchestrator
o = get_orchestrator(".")
print("mock_type=", type(o.executor).__name__ if o.executor else "None")
cfg2 = open("macao.yaml").read().replace('cli: "mock-cli"', 'cli: "no-such-cli-xyz"', 1)
open("macao.yaml", "w").write(cfg2)
o2 = get_orchestrator(".")
print("unknown_type=", type(o2.executor).__name__ if o2.executor else "None")
'''
        r = sh([sys.executable, "-c", code], cwd=d, env={"PYTHONPATH": str(tree / "src")})
        mt = re.search(r"mock_type= (\w+)", r.stdout)
        ut = re.search(r"unknown_type= (\w+)", r.stdout)
        # task create completes with mock executor (no hang)
        rc, _ = cli(tree, d, "task", "create", "--title", "T1", "--no-probe", timeout=180)
        check("H04", "get_orchestrator wires executor (mock); unknown CLI -> None; task create completes",
              mt and mt.group(1) == "MockAgentAdapter" and ut and ut.group(1) == "None" and rc == 0,
              f"mock={mt and mt.group(1)} unknown={ut and ut.group(1)} create_rc={rc}")

        # ---------------- H05: request metadata ----------------
        req = REPO / "docs/reviews/2026-09-09-review-request-bdc177e.md"
        txt = req.read_text(encoding="utf-8")
        full_ok = sh(["git", "cat-file", "-t", FULL], cwd=REPO).returncode == 0
        real = sh(["git", "rev-parse", SHA], cwd=REPO).stdout.strip()
        show_rc = sh(["git", "show", "--check", FULL], cwd=REPO).returncode
        env_sha = re.search(r"sha256:\s*\"([0-9a-f]{64})\"", txt).group(1)
        env_path = re.search(r"full_document:\n  path: \"([^\"]+)\"", txt).group(1)
        disk = hashlib.sha256((REPO / env_path).read_bytes()).hexdigest()
        blob = subprocess.run(["git", "show", f"{SHA}:{env_path}"], cwd=str(REPO), capture_output=True).stdout
        blob_sha = hashlib.sha256(blob).hexdigest()
        three_way = env_sha == disk == blob_sha
        import yaml as _y
        sample = _y.safe_load(re.search(r"```yaml\n(.*?)```", txt, re.S).group(1))
        sys.path.insert(0, str(tree / "src"))
        from macao.core.schema import validate_dev_manifest
        vok, verr = validate_dev_manifest(sample)
        sys.path.remove(str(tree / "src"))
        check("H05", "real full SHA; §3.3 rc=0; envelope 3-way sha binding; sample schema-valid",
              full_ok and real == FULL and show_rc == 0 and three_way and vok,
              f"full_ok={full_ok} real={real[:10]}… show_rc={show_rc} "
              f"3way={three_way} schema={vok}{'' if vok else ' err=' + str(verr)}")

        # ---------------- H06: change table ----------------
        rows = re.findall(r"^\|\s*`([^`]+)`\s*\|\s*[^|]*\|\s*\+(\d+)\s*/\s*-(\d+)\s*\|", txt, re.M)
        num = sh(["git", "diff", "--numstat", "e06d44c..bdc177e"], cwd=REPO).stdout
        actual = {}
        for line in num.strip().split("\n"):
            a, dl, p = line.split("\t"); actual[p] = (int(a), int(dl))
        bad = [p for p, a, dl in rows if actual.get(p) != (int(a), int(dl))]
        missing = sorted(set(actual) - {r[0] for r in rows})
        check("H06", "change table exact & complete (25/25)",
              rows and not bad and not missing, f"rows={len(rows)} bad={bad} omitted={missing}")

        # ---------------- H07: stale read carry-over ----------------
        d = sandbox / "h7"; d.mkdir()
        (d / ".macao").mkdir()
        w = sqlite3.connect(str(d / ".macao/state.db"))
        w.execute("PRAGMA journal_mode=WAL;")
        w.execute("CREATE TABLE tasks (task_id TEXT, title TEXT, source_branch TEXT, target_branch TEXT,"
                  " state TEXT, checkpoint_ref TEXT, review_round INTEGER, created_at TEXT, updated_at TEXT)")
        w.execute("INSERT INTO tasks VALUES ('task-OLD','Old','f','main','CODING',NULL,1,'2020','2020')")
        w.commit(); w.close()
        # valid config copied in (required: probe must reach DB read)
        shutil.copy(tree / "macao.yaml", d / "macao.yaml")
        sh(["git", "init", "-q", "."], cwd=d)
        wp = sandbox / "h7w.py"
        wp.write_text("import sqlite3,time,sys\nw=sqlite3.connect(sys.argv[1])\n"
                      "w.execute('PRAGMA journal_mode=WAL;');w.execute('PRAGMA wal_autocheckpoint=0;')\n"
                      "w.execute(\"INSERT INTO tasks VALUES ('task-NEW','N','f','main','CODING',NULL,1,'2021','2021')\")\n"
                      "w.commit();print('ok',flush=True);time.sleep(12);w.close()\n")
        proc = subprocess.Popen([sys.executable, str(wp), str(d / ".macao/state.db")],
                                stdout=subprocess.PIPE, text=True)
        proc.stdout.readline(); time.sleep(1)
        before = sorted(x.name for x in (d / ".macao").iterdir())
        rc, out = cli(tree, d, "probe", "--dry-run", "--json")
        j = json.loads(out)
        after = sorted(x.name for x in (d / ".macao").iterdir())
        rep = (j.get("active_task") or {}).get("task_id")
        stale = rep == "task-OLD"
        new_sidecars = set(after) - set(before)
        proc.kill(); proc.wait()
        check("H07", "stale read RESOLVED (expected FAIL = still present, must register §8.3-2)",
              not stale and not new_sidecars,
              f"valid_config={j.get('valid_config')} reported={rep} new_sidecars={new_sidecars or 'NONE'}")

        print("\n==== SUMMARY ====")
        for hid, desc, ok in RESULTS:
            print(f"  {'PASS' if ok else 'FAIL'}  {hid}")
        return 0
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
        print(f"# sandbox cleaned: {sandbox}")


if __name__ == "__main__":
    sys.exit(main())
