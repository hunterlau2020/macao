#!/usr/bin/env python3
"""Reproduce 7bc8d70 Scenario-C and checkpoint fail-closed gaps.

Issue IDs: P1-7bc8d70-01, P1-7bc8d70-02
Commit: 7bc8d7091ba4e39c0b3282492c613817f8d664e9
Prerequisites: Python 3.10+, PyYAML/jsonschema, MACAO source at this commit;
run from repository root with ``PYTHONPATH=src``.
Last executed: 2026-09-08 Asia/Taipei.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml
from click.testing import CliRunner

from macao.cli.main import cli
from macao.core.types import AgentState
from macao.storage.db import reset_db_manager
from macao.storage.store import StateStore
from macao.workflow.orchestrator import Orchestrator


CONFIG = {
    "version": "2.5",
    "project": {
        "name": "review-repro",
        "repository": {
            "workspace_path": ".",
            "remote_name": "origin",
            "default_branch": "main",
        },
    },
    "team": {
        "executor": {"id": "dev-mock", "cli": "mock-cli", "adapter": "pty-wrapper"},
        "reviewers": [
            {"id": "rev-a", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1},
            {"id": "rev-b", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1},
        ],
    },
    "policy": {
        "consensus_rule": "weighted_2/3_v1",
        "dictator_cap_enabled": True,
        "minimum_winning_seats": 2,
        "seat_quorum_required": 2,
        "weight_quorum_required": 2,
    },
}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, text=True, capture_output=True
    ).stdout.strip()


def prepare_repo(repo: Path) -> str:
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Review Reproducer")
    git(repo, "config", "user.email", "review@example.test")
    (repo / "README.md").write_text("# repro\n", encoding="utf-8")
    (repo / "macao.yaml").write_text(yaml.safe_dump(CONFIG), encoding="utf-8")
    git(repo, "add", "README.md", "macao.yaml")
    git(repo, "commit", "-m", "initial")
    return git(repo, "rev-parse", "HEAD")


def reproduce_adopt_accepts_nonexistent_baseline(repo: Path) -> None:
    reviews = repo / "docs" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "2026-09-08-review-request-deadbeef.md").write_text(
        "# Request\n\nBaseline: deadbeef\n", encoding="utf-8"
    )
    result = CliRunner().invoke(cli, ["task", "adopt", "--no-review"])
    assert result.exit_code == 0, result.output
    active = StateStore().get_active_task()
    assert active is not None and active["state"] == AgentState.WAITING_REVIEW.value
    assert active["checkpoint_ref"] == "deadbeef"
    missing = subprocess.run(
        ["git", "cat-file", "-e", "deadbeef^{commit}"], cwd=repo, capture_output=True
    )
    assert missing.returncode != 0, "fixture baseline unexpectedly exists"


def reproduce_checkpoint_accepts_unbound_manifest(repo: Path, head: str) -> None:
    reset_db_manager()
    orch = Orchestrator(project_root=str(repo), config=CONFIG)
    task = orch.start_task("checkpoint repro", "verify checkpoint", [], "main", "main")
    manifest_dir = repo / ".macao"
    manifest_dir.mkdir(exist_ok=True)
    manifest = {
        "version": "1.0",
        "task_id": "different-task-id",
        "checkpoint_ref": "deadbeef",
        "review_round": 1,
        "status": "ready_for_review",
        "signal": "EXPLICIT",
        "executor": {"id": "dev-mock", "cli": "attacker-cli"},
        "full_document": {
            "path": "docs/reviews/does-not-exist.md",
            "evidence_commit": "not-the-head",
            "sha256": "0" * 64,
        },
        "development": {
            "quality_metrics": {"tests_passed": True},
            "git": {"latest_commit": head},
        },
    }
    (manifest_dir / ".dev.yml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    change = orch.check_development_checkpoint(task["task_id"])
    assert change is not None, "7bc8d70 unexpectedly rejected the forged manifest"
    accepted = orch.store.get_task(task["task_id"])
    assert accepted["state"] == AgentState.READY_FOR_REVIEW.value


def main() -> None:
    original_cwd = Path.cwd()
    root = Path(tempfile.mkdtemp(prefix="macao-7bc8d70-repro-"))
    try:
        head = prepare_repo(root)
        os.chdir(root)
        reset_db_manager()
        reproduce_adopt_accepts_nonexistent_baseline(root)
        reset_db_manager()
        shutil.rmtree(root / ".macao")
        reproduce_checkpoint_accepts_unbound_manifest(root, head)
        print("REPRODUCED: nonexistent adoption baseline and unbound checkpoint were accepted")
    finally:
        os.chdir(original_cwd)
        reset_db_manager()
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
