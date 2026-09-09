"""Independent reproduction for claude's e06d44c review.
Covers: (1) checkpoint sibling-directory path-traversal escape,
        (2) CLI composition root never wires an executor adapter,
        (3) acceptance_criteria/success_criteria field-name mismatch across 5 executor adapters,
        (4) application front-matter self-referential integrity (claimed full SHA / envelope sha256).
Every probe uses its own tempfile.mkdtemp() sandbox; host repo receives zero writes except
where explicitly noted (git introspection of the already-committed e06d44c/HEAD is read-only).
"""
import sys, yaml, hashlib, shutil, tempfile, subprocess, os
from pathlib import Path
sys.path.insert(0, "/home/debian/macao/src")


def probe_sibling_escape():
    parent = tempfile.mkdtemp()
    try:
        proj = Path(parent, "proj")
        sibling = Path(parent, "proj-evil-secrets")
        proj.mkdir(); sibling.mkdir()
        secret_content = b"TOP-SECRET-CREDENTIALS-NOT-PART-OF-THIS-PROJECT"
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

        from macao.workflow.orchestrator import Orchestrator
        cfg = {
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
        o = Orchestrator(project_root=str(proj), config=cfg)
        t = o.start_task("T", "sibling escape probe")
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
        st = o.store.get_task(tid)["state"]
        print(f"sibling_escape -> advanced={ch is not None!s:6s} final_state={st} "
              f"(relative_path_used={rel})")
    finally:
        shutil.rmtree(parent, ignore_errors=True)


def probe_composition_root_and_field_mismatch():
    from macao.cli.main import DEFAULT_CONFIG_TEMPLATE, get_orchestrator
    from macao.storage.db import reset_db_manager
    from macao.adapter.claude import ClaudeCodeAdapter

    root = Path(tempfile.mkdtemp())
    try:
        (root / "macao.yaml").write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
        reset_db_manager()
        orch = get_orchestrator(str(root))
        print("get_orchestrator(...).executor is None ->", orch.executor is None)
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
          "MUST_REACH_EXECUTOR_XYZ" in prompt, "(prompt: %r)" % prompt)


def probe_application_front_matter():
    """Read-only git introspection against the already-committed repository history."""
    repo = "/home/debian/macao"
    resolved = subprocess.run(["git", "rev-parse", "e06d44c"], cwd=repo, capture_output=True, text=True).stdout.strip()
    claimed = "e06d44c77c688bb715bb997a3cf556bc91f6920f"
    exists_rc = subprocess.run(["git", "cat-file", "-t", claimed], cwd=repo, capture_output=True, text=True).returncode
    print(f"short SHA e06d44c resolves to -> {resolved}")
    print(f"application-claimed full SHA  -> {claimed} (exists_as_git_object={exists_rc == 0})")

    in_tree = subprocess.run(
        ["git", "ls-tree", "-r", "e06d44c", "--name-only"], cwd=repo, capture_output=True, text=True
    ).stdout
    doc_path = "docs/reviews/2026-09-09-review-request-e06d44c.md"
    print(f"'{doc_path}' present inside commit e06d44c -> {doc_path in in_tree}")

    first_commit = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H", "--", doc_path], cwd=repo, capture_output=True, text=True
    ).stdout.strip().splitlines()
    print(f"document first added in commit -> {first_commit[-1] if first_commit else 'UNKNOWN'}")

    claimed_sha256 = "d599dca03ec19592bb519b8a7b3f4a7bf6fb5f48d39e9163435f4d40fd246222"
    actual_sha256 = hashlib.sha256(Path(repo, doc_path).read_bytes()).hexdigest()
    print(f"envelope-claimed sha256 -> {claimed_sha256}")
    print(f"actual on-disk sha256   -> {actual_sha256} (match={claimed_sha256 == actual_sha256})")


probe_sibling_escape()
probe_composition_root_and_field_mismatch()
probe_application_front_matter()
