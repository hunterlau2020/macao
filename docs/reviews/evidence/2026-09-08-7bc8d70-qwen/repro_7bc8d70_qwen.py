"""
Evidence script — qwen review of 7bc8d70 (2026-09-08).
issue_ids covered:
  QW-7BC-P1-1  Codex P1-04 anti-forgery gate fail-open (zero-sha exemption / missing-doc exemption / executor.cli unchecked)
  QW-7BC-V-*   closure verifications (P1-2 sidecars, P1-6 single task, P1-7 exit codes, adopt --dry-run, unknown-CLI fail-closed)
Environment: Linux (Debian), Python 3.11, git >= 2.30; requires repo src at /home/debian/macao (override via MACAO_REPO).
Last executed: 2026-09-08 (see report §复现记录 for outputs).
Isolation: every probe creates its own tempfile.mkdtemp() project and removes it; zero writes to the host repo.
Run: python3 repro_7bc8d70_qwen.py
"""
import os, subprocess, sys, tempfile, shutil, hashlib, yaml
from pathlib import Path

REPO = Path(os.environ.get("MACAO_REPO", "/home/debian/macao"))
sys.path.insert(0, str(REPO / "src"))
ENV = dict(os.environ); ENV["PYTHONPATH"] = str(REPO / "src")
ROOT_CFG = yaml.safe_load((REPO / "macao.yaml").read_text())
RESULTS = []

def record(issue_id, name, cond, detail=""):
    RESULTS.append((issue_id, name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {issue_id} {name} {detail}")

def mkproj(prefix):
    td = Path(tempfile.mkdtemp(prefix=prefix))
    for c in [["git","init","-b","main"],["git","config","user.name","B"],["git","config","user.email","b@t.dev"]]:
        subprocess.run(c, cwd=td, check=True, capture_output=True)
    (td/"README.md").write_text("# r\n")
    subprocess.run(["git","add","README.md"], cwd=td, check=True)
    subprocess.run(["git","commit","-m","i"], cwd=td, check=True, capture_output=True)
    (td/"macao.yaml").write_text(yaml.safe_dump(yaml.safe_load(yaml.safe_dump(ROOT_CFG))))
    (td/"docs/reviews").mkdir(parents=True)
    (td/"docs/reviews/req.md").write_text("Official Review Request Content")
    return td

def checkpoint_probe(td, mutate_code):
    """Fresh task in td; write manifest per mutate_code; return 'ACCEPTED'/'REJECTED'."""
    code = f'''
import sys, yaml, hashlib; sys.path.insert(0, "{REPO}/src")
from pathlib import Path
from macao.workflow.orchestrator import Orchestrator
td = "{td}"; o = Orchestrator(project_root=td); t = o.start_task("T","d")["task_id"]
head = o.git.get_head_commit()
sha = hashlib.sha256((Path(td)/"docs/reviews/req.md").read_bytes()).hexdigest()
m = {{"version":"1.0","task_id":t,"checkpoint_ref":head,
 "full_document":{{"path":"docs/reviews/req.md","evidence_commit":head,"sha256":sha}},
 "status":"ready_for_review","signal":"EXPLICIT","review_round":1,
 "executor":{{"id":"opencode-dev","cli":"opencode"}},
 "development":{{"quality_metrics":{{"tests_passed":True}},"git":{{"latest_commit":head}}}}}}
{mutate_code}
(Path(td)/".macao").mkdir(exist_ok=True); (Path(td)/".macao"/".dev.yml").write_text(yaml.safe_dump(m))
print("RESULT:", "ACCEPTED" if o.check_development_checkpoint(t) is not None else "REJECTED")
'''
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=ENV, timeout=120)
    for line in r.stdout.splitlines():
        if line.startswith("RESULT:"):
            return line.split(":",1)[1].strip()
    return f"ERROR: {r.stderr.strip()[-120:]}"

# ---- QW-7BC-P1-1: anti-forgery gate fail-open probes ----
td = mkproj("qw_p1_zero_")
res = checkpoint_probe(td, 'm["full_document"]["sha256"] = "0"*64')
record("QW-7BC-P1-1a", "all-zero sha256 exemption", res == "ACCEPTED",
       f"zero-sha manifest -> {res} (request claims 'must match actual SHA-256'; envelope of the request itself uses 64 zeros)")
shutil.rmtree(td, ignore_errors=True)

td = mkproj("qw_p1_miss_")
res = checkpoint_probe(td, 'm["full_document"]["path"] = "docs/reviews/nonexistent.md"')
record("QW-7BC-P1-1b", "missing referenced document exemption", res == "ACCEPTED",
       f"missing doc -> {res} (existence not enforced)")
shutil.rmtree(td, ignore_errors=True)

td = mkproj("qw_p1_cli_")
res = checkpoint_probe(td, 'm["executor"]["cli"] = "WRONG-CLI"')
record("QW-7BC-P1-1c", "executor.cli not verified", res == "ACCEPTED",
       f"id-correct/cli-wrong manifest -> {res} (request claims id AND cli enforced)")
shutil.rmtree(td, ignore_errors=True)

td = mkproj("qw_p1_ctrl_")
res_true = checkpoint_probe(td, 'pass')
shutil.rmtree(td, ignore_errors=True)
td = mkproj("qw_p1_tamp_")
res_tamp = checkpoint_probe(td, 'm["full_document"]["sha256"] = "tampered" + "0"*55')
record("QW-7BC-P1-1d", "control: true sha accepted / tampered rejected",
       res_true == "ACCEPTED" and res_tamp == "REJECTED", f"true={res_true}, tampered={res_tamp}")
shutil.rmtree(td, ignore_errors=True)

# ---- QW-7BC-V-1: unknown CLI fail-closed (P0-1) ----
td = mkproj("qw_v1_")
cfg = yaml.safe_load((td/"macao.yaml").read_text())
cfg["team"]["reviewers"].append({"id":"r-x","cli":"custom-claude","adapter":"pty-wrapper","vote_weight":1})
(td/"macao.yaml").write_text(yaml.safe_dump(cfg))
r = subprocess.run([sys.executable,"-m","macao.cli.main","probe","--json","--allow-degraded"],
                   cwd=td, capture_output=True, text=True, env=ENV, timeout=120)
record("QW-7BC-V-1", "unknown CLI blocks dispatch (exit!=0)", r.returncode != 0, f"exit={r.returncode}")
record("QW-7BC-P2-1", "unknown CLI diagnostics silent (no MISSING/offender named)",
       "custom-claude" not in (r.stdout + r.stderr) and "MISSING" not in (r.stdout + r.stderr).upper(),
       "stdout/stderr contain neither the offending CLI name nor MISSING label; --allow-degraded ineffective on this path")
shutil.rmtree(td, ignore_errors=True)

# ---- QW-7BC-V-2: zero sidecars on read-only probe with existing state.db (P1-2) ----
td = mkproj("qw_v2_")
subprocess.run([sys.executable,"-c",
    f'import sys; sys.path.insert(0,"{REPO}/src")\nfrom macao.workflow.orchestrator import Orchestrator\nOrchestrator(project_root="{td}").start_task("T","d")'],
    capture_output=True, text=True, env=ENV, timeout=120)
before = sorted(p.name for p in (td/".macao").glob("state.db*"))
r = subprocess.run([sys.executable,"-m","macao.cli.main","probe","--dry-run"],
                   cwd=td, capture_output=True, text=True, env=ENV, timeout=120)
after = sorted(p.name for p in (td/".macao").glob("state.db*"))
record("QW-7BC-V-2", "probe read path creates no WAL/SHM sidecars",
       not [x for x in after if x not in before], f"before={before} after={after}")
shutil.rmtree(td, ignore_errors=True)

# ---- QW-7BC-V-3: single active task invariant (P1-6) ----
td = mkproj("qw_v3_")
r = subprocess.run([sys.executable,"-c",
    f'import sys; sys.path.insert(0,"{REPO}/src")\nfrom macao.workflow.orchestrator import Orchestrator\no=Orchestrator(project_root="{td}")\no.start_task("T1","d")\ntry:\n    o.start_task("T2","d"); print("RESULT: ACCEPTED")\nexcept Exception as e: print("RESULT: REJECTED", type(e).__name__)'],
    capture_output=True, text=True, env=ENV, timeout=120)
record("QW-7BC-V-3", "second concurrent start_task rejected", "REJECTED" in r.stdout, r.stdout.strip()[-60:])
shutil.rmtree(td, ignore_errors=True)

# ---- QW-7BC-V-4: invalid-config exit codes (P1-7) ----
td = mkproj("qw_v4_")
(td/"macao.yaml").write_text(yaml.safe_dump({"team": {"executor": {"id": "dev"}}}))
r1 = subprocess.run([sys.executable,"-m","macao.cli.main","doctor"], cwd=td, capture_output=True, text=True, env=ENV, timeout=120)
r2 = subprocess.run([sys.executable,"-m","macao.cli.main","probe"], cwd=td, capture_output=True, text=True, env=ENV, timeout=120)
record("QW-7BC-V-4", "invalid config -> non-zero exit (doctor/probe)",
       r1.returncode != 0 and r2.returncode != 0, f"doctor={r1.returncode} probe={r2.returncode}")
shutil.rmtree(td, ignore_errors=True)

# ---- QW-7BC-V-5: task adopt --dry-run zero mutation (Codex P1-03) ----
td = mkproj("qw_v5_")
(td/"feature.py").write_text("print('wip')\n")
r = subprocess.run([sys.executable,"-m","macao.cli.main","task","adopt","--dry-run"],
                   cwd=td, capture_output=True, text=True, env=ENV, timeout=120)
record("QW-7BC-V-5", "adopt --dry-run exits 0 and creates no state.db",
       r.returncode == 0 and not (td/".macao"/"state.db").exists(), f"exit={r.returncode}")
r2 = subprocess.run([sys.executable,"-m","macao.cli.main","task","adopt","Adopted Name"],
                    cwd=td, capture_output=True, text=True, env=ENV, timeout=120)
record("QW-7BC-P3-1", "claimed positional [TASK_NAME] unsupported",
       r2.returncode != 0 and "unexpected extra argument" in (r2.stdout + r2.stderr).lower(),
       "request §1.12 claims 'macao task adopt [TASK_NAME]'; CLI rejects positional arg")
shutil.rmtree(td, ignore_errors=True)

print("\n==== SUMMARY ====")
for issue_id, name, cond, _ in RESULTS:
    print(f"{'CONFIRMED' if cond else 'not-reproduced'}  {issue_id}  {name}")
