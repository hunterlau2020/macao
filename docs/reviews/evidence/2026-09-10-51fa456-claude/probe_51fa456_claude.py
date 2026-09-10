"""
Independent falsifying reproduction for Round 6 (commit 51fa456) claims.
Claude's own probe — isolated tempfile.mkdtemp() sandbox per test to avoid
task-state pollution (lesson from Round 3 / 7bc8d70).
"""
import sys, os, tempfile, subprocess, hashlib, shutil, yaml
sys.path.insert(0, "/home/debian/macao/src")

from macao.workflow.orchestrator import Orchestrator
from macao.core.types import AgentState


def make_repo():
    d = tempfile.mkdtemp(prefix="macao_probe_")
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=d, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=d, check=True)
    (os_path := os.path.join(d, "README.md"))
    with open(os_path, "w") as f:
        f.write("init\n")
    subprocess.run(["git", "add", "."], cwd=d, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=d, check=True)
    return d


def probe_untracked_evidence_now_rejected():
    """Round 5 P2-1 (Claude): untracked-but-real evidence file used to bypass blob check.
    Expect: NOW REJECTED (advanced is None) -- this is the claimed fix."""
    d = make_repo()
    try:
        orch = Orchestrator(project_root=d)
        task = orch.start_task(title="t", task_description="d", source_branch="feature/x",
                                target_branch="main", acceptance_criteria=["ac1"])
        task_id = task["task_id"]

        os.makedirs(os.path.join(d, "docs", "reviews"), exist_ok=True)
        doc_path = os.path.join(d, "docs", "reviews", "evidence.md")
        with open(doc_path, "w") as f:
            f.write("# real evidence, never committed\n")
        doc_sha = hashlib.sha256(open(doc_path, "rb").read()).hexdigest()

        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()

        os.makedirs(os.path.join(d, ".macao"), exist_ok=True)
        manifest = {
            "version": "1.0", "task_id": task_id, "checkpoint_ref": head,
            "review_round": 1, "status": "ready_for_review", "signal": "EXPLICIT",
            "executor": {"id": "dev", "cli": "claude"},
            "full_document": {"path": "docs/reviews/evidence.md", "evidence_commit": head, "sha256": doc_sha},
            "development": {"quality_metrics": {"tests_passed": True}, "git": {"latest_commit": head}},
        }
        with open(os.path.join(d, ".macao", ".dev.yml"), "w") as f:
            yaml.safe_dump(manifest, f)

        change = orch.check_development_checkpoint(task_id)
        advanced = change is not None
        print(f"untracked_evidence_bypass (Round5 P2-1) -> advanced={advanced}  (expect False)")
        assert advanced is False, "REGRESSION: untracked evidence file still bypasses blob anti-tamper check!"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def probe_tampered_tracked_control():
    """Control: a genuinely committed file, then locally tampered on disk after commit.
    Both disk-hash and manifest sha256 are recomputed to match the TAMPERED content,
    so only the git-blob comparison (tampered content vs original committed blob) can catch it.
    Expect: REJECTED."""
    d = make_repo()
    try:
        orch = Orchestrator(project_root=d)
        task = orch.start_task(title="t", task_description="d", source_branch="feature/x",
                                target_branch="main", acceptance_criteria=["ac1"])
        task_id = task["task_id"]

        os.makedirs(os.path.join(d, "docs", "reviews"), exist_ok=True)
        doc_path = os.path.join(d, "docs", "reviews", "evidence.md")
        with open(doc_path, "w") as f:
            f.write("# original committed content\n")
        subprocess.run(["git", "add", "docs/reviews/evidence.md"], cwd=d, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "add evidence"], cwd=d, check=True)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()

        # tamper AFTER commit, without re-committing
        with open(doc_path, "w") as f:
            f.write("# TAMPERED content claiming to still be the reviewed evidence\n")
        doc_sha = hashlib.sha256(open(doc_path, "rb").read()).hexdigest()  # matches tampered disk content

        manifest = {
            "version": "1.0", "task_id": task_id, "checkpoint_ref": head,
            "review_round": 1, "status": "ready_for_review", "signal": "EXPLICIT",
            "executor": {"id": "dev", "cli": "claude"},
            "full_document": {"path": "docs/reviews/evidence.md", "evidence_commit": head, "sha256": doc_sha},
            "development": {"quality_metrics": {"tests_passed": True}, "git": {"latest_commit": head}},
        }
        os.makedirs(os.path.join(d, ".macao"), exist_ok=True)
        with open(os.path.join(d, ".macao", ".dev.yml"), "w") as f:
            yaml.safe_dump(manifest, f)

        change = orch.check_development_checkpoint(task_id)
        advanced = change is not None
        print(f"tampered_tracked_file (control) -> advanced={advanced}  (expect False)")
        assert advanced is False
    finally:
        shutil.rmtree(d, ignore_errors=True)


def probe_unknown_executor_cli_failclosed():
    """Codex P1-bdc177e-02: macao.yaml declares an unknown executor CLI.
    get_orchestrator() (composition root) must raise/exit before any task write.
    We call get_adapter_for_executor directly + verify ValueError, then verify
    main.get_orchestrator() catches it via sys.exit(1) and no task row appears."""
    d = make_repo()
    try:
        from macao.workflow.live_dispatcher import LiveAgentDispatcher
        try:
            LiveAgentDispatcher.get_adapter_for_executor({"id": "bogus-dev", "cli": "totally-bogus-cli-xyz"}, d)
            raised = False
        except ValueError:
            raised = True
        print(f"unknown_cli get_adapter_for_executor raises ValueError -> {raised}  (expect True)")
        assert raised

        macao_yaml = os.path.join(d, "macao.yaml")
        with open("/home/debian/macao/macao.yaml", "r") as f:
            full_cfg = yaml.safe_load(f)
        full_cfg["team"]["executor"]["cli"] = "totally-bogus-cli-xyz"
        with open(macao_yaml, "w") as f:
            yaml.safe_dump(full_cfg, f)

        # subprocess: invoke get_orchestrator via main.py CLI entry point directly (task create --no-probe)
        env = dict(os.environ)
        env["PYTHONPATH"] = "/home/debian/macao/src"
        cmd = [sys.executable, "-m", "macao.cli.main", "task", "create",
               "--no-probe", "--title", "x", "--description", "y", "--acceptance", "z", "-f"]
        res = subprocess.run(cmd, cwd=d, env=env, capture_output=True, text=True, timeout=30)
        print(f"macao task create --no-probe with bogus executor cli -> exit_code={res.returncode}  (expect 1)")
        print(f"  stderr/stdout tail: {(res.stdout + res.stderr)[-300:]!r}")
        assert res.returncode == 1

        db_path = os.path.join(d, ".macao", "state.db")
        db_has_task = False
        if os.path.exists(db_path):
            import sqlite3
            con = sqlite3.connect(db_path)
            try:
                cur = con.execute("SELECT COUNT(*) FROM tasks")
                db_has_task = cur.fetchone()[0] > 0
            except Exception:
                db_has_task = False
            con.close()
        print(f"state.db contains any task row after failed create -> {db_has_task}  (expect False)")
        assert db_has_task is False
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    probe_untracked_evidence_now_rejected()
    probe_tampered_tracked_control()
    probe_unknown_executor_cli_failclosed()
    print("\nALL PROBES PASSED (all fixes independently confirmed)")

def probe_live_run_demo_drops_acceptance_criteria():
    """Advisory: `macao live-run` demo path declares acceptance_criteria at start_task()
    but its dispatch_review_in_worktree() call site (live_runner.py:154) omits the
    acceptance_criteria= kwarg, so the reviewer prompt never receives it in this one flow."""
    import inspect
    from macao.workflow import live_runner
    src = inspect.getsource(live_runner.LiveWorkflowRunner.run_live_cycle)
    call_site = src[src.index("dispatch_review_in_worktree("):]
    call_site = call_site[:call_site.index(")")+1]
    has_kwarg = "acceptance_criteria=" in call_site
    print(f"live_runner.py dispatch_review_in_worktree() call passes acceptance_criteria= -> {has_kwarg}  (expect False; known gap)")
    assert has_kwarg is False, "unexpected: live_runner now forwards acceptance_criteria (gap closed?)"


probe_live_run_demo_drops_acceptance_criteria()
