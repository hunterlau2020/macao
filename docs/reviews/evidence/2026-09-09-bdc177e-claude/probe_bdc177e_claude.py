"""Independent reproduction for claude's bdc177e (Round 5) review.
Covers: (1) sibling-directory escape now rejected, (2) tracked-file tamper-vs-blob
now rejected, (3) untracked-evidence bypass of the blob check (new P2),
(4) CLI composition root now wires a real executor adapter,
(5) acceptance_criteria reaches the executor prompt.
Every probe uses its own tempfile.mkdtemp() sandbox; host repo receives zero writes.
"""
import sys, yaml, hashlib, shutil, tempfile, subprocess, os
from pathlib import Path
sys.path.insert(0, "/home/debian/macao/src")


def base_cfg():
    return {
        "version": "2.5",
        "project": {"name": "t", "repository": {"workspace_path": ".", "remote_name": "origin", "default_branch": "main"}},
        "team": {"executor": {"id": "dev-claude", "cli": "claude-code", "adapter": "pty-wrapper"},
                 "reviewers": [{"id": "r1", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1},
                               {"id": "r2", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1}]},
        "policy": {"consensus_rule": "weighted_2/3_v1", "dictator_cap_enabled": True, "minimum_winning_seats": 2,
                   "seat_quorum_required": 2, "weight_quorum_required": 2, "max_rework_rounds": 3},
        "merge": {"strategy": "ff_only", "require_human_signoff": True},
        "timeouts": {"development": "2h", "checkpoint_validation": "1m", "review_request": "30m", "per_reviewer": "10m", "consensus_check": "1m"}
    }


def probe_sibling_escape():
    from macao.workflow.orchestrator import Orchestrator
    parent = tempfile.mkdtemp()
    try:
        proj = Path(parent, "proj")
        sibling = Path(parent, "proj-evil-secrets")
        proj.mkdir(); sibling.mkdir()
        secret_content = b"TOP-SECRET-NOT-PART-OF-THIS-PROJECT"
        secret_file = sibling / "secret.txt"
        secret_file.write_bytes(secret_content)
        secret_sha = hashlib.sha256(secret_content).hexdigest()

        subprocess.run(["git", "init", "-q", "."], cwd=proj, check=True)
        subprocess.run(["git", "config", "user.email", "t@t"], cwd=proj, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=proj, check=True)
        Path(proj, "README.md").write_text("x")
        subprocess.run(["git", "add", "."], cwd=proj, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=proj, check=True)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=proj, capture_output=True, text=True).stdout.strip()

        o = Orchestrator(project_root=str(proj), config=base_cfg())
        t = o.start_task("T", "sibling escape probe r5")
        tid = t["task_id"]
        rel = os.path.relpath(secret_file, proj)
        data = {
            "version": "1.0", "task_id": tid, "checkpoint_ref": head,
            "full_document": {"path": rel, "evidence_commit": head, "sha256": secret_sha},
            "status": "ready_for_review", "signal": "EXPLICIT", "review_round": 1,
            "executor": {"id": "dev-claude", "cli": "claude-code"},
            "development": {"quality_metrics": {"tests_passed": True}, "git": {"latest_commit": head}}
        }
        Path(proj, ".macao").mkdir(parents=True, exist_ok=True)
        Path(proj, ".macao", ".dev.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
        ch = o.check_development_checkpoint(tid)
        print(f"sibling_escape -> advanced={ch is not None!s:6s} (expect False; R3/R4 finding, now fixed)")
    finally:
        shutil.rmtree(parent, ignore_errors=True)


def probe_blob_tamper_control():
    from macao.workflow.orchestrator import Orchestrator
    d = tempfile.mkdtemp()
    try:
        subprocess.run(["git", "init", "-q", "."], cwd=d, check=True)
        subprocess.run(["git", "config", "user.email", "t@t"], cwd=d, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=d, check=True)
        Path(d, "README.md").write_text("x")
        Path(d, "docs").mkdir()
        evid = Path(d, "docs", "evidence.md")
        evid.write_text("Original committed content.")
        subprocess.run(["git", "add", "."], cwd=d, check=True)
        subprocess.run(["git", "commit", "-qm", "init with tracked evidence"], cwd=d, check=True)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()

        evid.write_text("TAMPERED CONTENT not matching the committed git blob.")
        tampered_sha = hashlib.sha256(evid.read_bytes()).hexdigest()

        o = Orchestrator(project_root=d, config=base_cfg())
        t = o.start_task("T", "tamper control probe")
        tid = t["task_id"]
        data = {
            "version": "1.0", "task_id": tid, "checkpoint_ref": head,
            "full_document": {"path": "docs/evidence.md", "evidence_commit": head, "sha256": tampered_sha},
            "status": "ready_for_review", "signal": "EXPLICIT", "review_round": 1,
            "executor": {"id": "dev-claude", "cli": "claude-code"},
            "development": {"quality_metrics": {"tests_passed": True}, "git": {"latest_commit": head}}
        }
        Path(d, ".macao").mkdir(parents=True, exist_ok=True)
        Path(d, ".macao", ".dev.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
        ch = o.check_development_checkpoint(tid)
        print(f"tampered_tracked_file (control) -> advanced={ch is not None!s:6s} (expect False; blob check catches this)")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def probe_untracked_evidence_bypass():
    from macao.workflow.orchestrator import Orchestrator
    d = tempfile.mkdtemp()
    try:
        subprocess.run(["git", "init", "-q", "."], cwd=d, check=True)
        subprocess.run(["git", "config", "user.email", "t@t"], cwd=d, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=d, check=True)
        Path(d, "README.md").write_text("x")
        subprocess.run(["git", "add", "."], cwd=d, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=d, check=True)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()

        Path(d, "docs").mkdir()
        untracked = Path(d, "docs", "uncommitted_evidence.md")
        untracked.write_text("This file was never `git add`-ed or committed at all.")
        untracked_sha = hashlib.sha256(untracked.read_bytes()).hexdigest()

        o = Orchestrator(project_root=d, config=base_cfg())
        t = o.start_task("T", "untracked evidence probe")
        tid = t["task_id"]
        data = {
            "version": "1.0", "task_id": tid, "checkpoint_ref": head,
            "full_document": {"path": "docs/uncommitted_evidence.md", "evidence_commit": head, "sha256": untracked_sha},
            "status": "ready_for_review", "signal": "EXPLICIT", "review_round": 1,
            "executor": {"id": "dev-claude", "cli": "claude-code"},
            "development": {"quality_metrics": {"tests_passed": True}, "git": {"latest_commit": head}}
        }
        Path(d, ".macao").mkdir(parents=True, exist_ok=True)
        Path(d, ".macao", ".dev.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
        ch = o.check_development_checkpoint(tid)
        print(f"untracked_evidence_bypass (new P2) -> advanced={ch is not None!s:6s} "
              f"(file is real, on-disk, inside project root, sha matches disk — but was never "
              f"committed at all, so the new git-blob anti-tamper check is silently skipped)")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def probe_executor_wiring():
    from macao.cli.main import DEFAULT_CONFIG_TEMPLATE, get_orchestrator
    from macao.storage.db import reset_db_manager
    from macao.adapter.claude import ClaudeCodeAdapter

    root = Path(tempfile.mkdtemp())
    try:
        (root / "macao.yaml").write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
        reset_db_manager()
        orch = get_orchestrator(str(root))
        print("get_orchestrator(...).executor is None ->", orch.executor is None,
              f"(type={type(orch.executor).__name__ if orch.executor else None})")
    finally:
        reset_db_manager()
        shutil.rmtree(root, ignore_errors=True)

    class CaptureSession:
        def __init__(self): self.prompts = []
        def write_input(self, p):
            self.prompts.append(p); return True

    adapter = ClaudeCodeAdapter("claude", {"role": "executor"})
    adapter.session = CaptureSession()
    adapter.is_running = True
    adapter.inject_task({
        "task_id": "t1", "task_description": "do the thing",
        "acceptance_criteria": ["MUST_REACH_EXECUTOR_XYZ"]
    })
    prompt = adapter.session.prompts[-1]
    print("acceptance criterion reaches prompt sent to executor ->",
          "MUST_REACH_EXECUTOR_XYZ" in prompt)


probe_sibling_escape()
probe_blob_tamper_control()
probe_untracked_evidence_bypass()
probe_executor_wiring()
