"""Independent reproduction for claude's 7bc8d70 review.
Covers: (1) checkpoint sha256/executor fail-open, (2) task adopt nonexistent-baseline + FSM bypass.
Every probe uses its own tempfile.mkdtemp() sandbox; host repo receives zero writes.
"""
import sys, yaml, hashlib, shutil, tempfile, subprocess
from pathlib import Path
sys.path.insert(0, "/home/debian/macao/src")
from macao.workflow.orchestrator import Orchestrator


def fresh_repo():
    d = tempfile.mkdtemp()
    subprocess.run(["git", "init", "-q", "."], cwd=d, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=d, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=d, check=True)
    Path(d, "README.md").write_text("x")
    Path(d, "docs").mkdir()
    Path(d, "docs", "x.md").write_text("hello world content")
    subprocess.run(["git", "add", "."], cwd=d, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=d, check=True)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()
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
    return d, head, cfg


def probe_checkpoint(label, full_document, executor):
    d, head, cfg = fresh_repo()
    try:
        o = Orchestrator(project_root=d, config=cfg)
        t = o.start_task("T", "checkpoint fail-open probe")
        tid = t["task_id"]
        fd = dict(full_document)
        fd["evidence_commit"] = head
        data = {
            "version": "1.0", "task_id": tid, "checkpoint_ref": head,
            "full_document": fd,
            "status": "ready_for_review", "signal": "EXPLICIT", "review_round": 1,
            "executor": executor,
            "development": {"quality_metrics": {"tests_passed": True}, "git": {"latest_commit": head}}
        }
        Path(d, ".macao").mkdir(parents=True, exist_ok=True)
        Path(d, ".macao", ".dev.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
        ch = o.check_development_checkpoint(tid)
        st = o.store.get_task(tid)["state"]
        print(f"checkpoint/{label:16s} -> advanced={ch is not None!s:6s} final_state={st}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def probe_adopt_nonexistent_baseline():
    d = tempfile.mkdtemp()
    try:
        subprocess.run(["git", "init", "-q", "."], cwd=d, check=True)
        subprocess.run(["git", "config", "user.email", "t@t"], cwd=d, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=d, check=True)
        Path(d, "README.md").write_text("x")
        Path(d, "macao.yaml").write_text(yaml.safe_dump({
            "version": "2.5",
            "project": {"name": "t", "repository": {"workspace_path": ".", "remote_name": "origin", "default_branch": "main"}},
            "team": {"executor": {"id": "dev-claude", "cli": "claude-code", "adapter": "pty-wrapper"},
                     "reviewers": [{"id": "r1", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1},
                                   {"id": "r2", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1}]},
            "policy": {"consensus_rule": "weighted_2/3_v1", "dictator_cap_enabled": True, "minimum_winning_seats": 2,
                       "seat_quorum_required": 2, "weight_quorum_required": 2, "max_rework_rounds": 3},
            "merge": {"strategy": "ff_only", "require_human_signoff": True},
            "timeouts": {"development": "2h", "checkpoint_validation": "1m", "review_request": "30m", "per_reviewer": "10m", "consensus_check": "1m"}
        }))
        Path(d, "docs", "reviews").mkdir(parents=True)
        Path(d, "docs", "reviews", "2026-09-08-review-request-deadbeef.md").write_text("# Fake Review Request\nCommit: deadbeef\n")
        subprocess.run(["git", "add", "."], cwd=d, check=True)
        subprocess.run(["git", "commit", "-qm", "config"], cwd=d, check=True)

        exists_rc = subprocess.run(["git", "cat-file", "-e", "deadbeef^{commit}"], cwd=d).returncode
        result = subprocess.run(
            [sys.executable, "-m", "macao.cli.main", "task", "adopt", "--no-review"],
            cwd=d, env={"PYTHONPATH": "/home/debian/macao/src", "PATH": "/usr/bin:/bin"},
            capture_output=True, text=True
        )
        print(f"adopt/nonexistent_baseline -> git_cat_file_rc={exists_rc} (nonzero=commit absent) "
              f"cli_exit={result.returncode} stdout_has_success={'Successfully adopted' in result.stdout}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


real_sha = hashlib.sha256(b"hello world content").hexdigest()
probe_checkpoint("zero_hash", {"path": "docs/x.md", "sha256": "0" * 64}, {"id": "dev-claude", "cli": "claude-code"})
probe_checkpoint("missing_file", {"path": "docs/does_not_exist.md", "sha256": "a" * 64}, {"id": "dev-claude", "cli": "claude-code"})
probe_checkpoint("empty_sha", {"path": "docs/x.md", "sha256": ""}, {"id": "dev-claude", "cli": "claude-code"})
probe_checkpoint("wrong_cli", {"path": "docs/x.md", "sha256": "0" * 64}, {"id": "dev-claude", "cli": "IMPOSTER-CLI"})
probe_checkpoint("wrong_id (control)", {"path": "docs/x.md", "sha256": "0" * 64}, {"id": "IMPOSTER-ID", "cli": "claude-code"})
probe_checkpoint("tampered_sha (control)", {"path": "docs/x.md", "sha256": "f" * 64}, {"id": "dev-claude", "cli": "claude-code"})
probe_checkpoint("good (control)", {"path": "docs/x.md", "sha256": real_sha}, {"id": "dev-claude", "cli": "claude-code"})
probe_adopt_nonexistent_baseline()
