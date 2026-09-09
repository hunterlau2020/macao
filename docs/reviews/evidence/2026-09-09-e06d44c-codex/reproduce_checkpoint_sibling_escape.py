#!/usr/bin/env python3
"""Reproduce checkpoint full_document provenance gaps.

Issue: P1-e06d44c-02.  Target commit:
e06d44cb31a0dbcbe199e6bb124430e9701e087f.  Prerequisites: Python 3.10+,
Git, and MACAO dependencies; run with PYTHONPATH=src.  No network or vendor
CLI is used.  Last executed: 2026-09-09 Asia/Taipei.
"""

import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

from macao.core.types import AgentState
from macao.storage.db import reset_db_manager
from macao.workflow.orchestrator import Orchestrator


CONFIG = {
    "version": "2.5",
    "project": {"name": "escape-repro", "repository": {"workspace_path": ".", "default_branch": "main"}},
    "team": {
        "executor": {"id": "dev-mock", "cli": "mock-cli", "adapter": "pty-wrapper"},
        "reviewers": [{"id": "reviewer", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1}],
    },
    "policy": {
        "consensus_rule": "weighted_2/3_v1",
        "dictator_cap_enabled": True,
        "minimum_winning_seats": 1,
        "seat_quorum_required": 1,
        "weight_quorum_required": 1,
    },
}


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, text=True, capture_output=True).stdout.strip()


def main():
    repo = Path(tempfile.mkdtemp(prefix="macao-e06d44c-root-"))
    sibling = repo.with_name(repo.name + "-sibling")
    try:
        git(repo, "init", "-b", "main")
        git(repo, "config", "user.name", "Review Reproducer")
        git(repo, "config", "user.email", "review@example.test")
        (repo / "README.md").write_text("root\n", encoding="utf-8")
        git(repo, "add", "README.md")
        git(repo, "commit", "-m", "initial")
        head = git(repo, "rev-parse", "HEAD")

        sibling.mkdir()
        external_doc = sibling / "untrusted-review-request.md"
        external_doc.write_text("outside the project root\n", encoding="utf-8")
        escaped_path = f"../{sibling.name}/{external_doc.name}"

        reset_db_manager()
        orchestrator = Orchestrator(project_root=str(repo), config=CONFIG)
        task = orchestrator.start_task(title="escape", task_description="reproduce")
        manifest = {
            "version": "1.0",
            "task_id": task["task_id"],
            "checkpoint_ref": head,
            "review_round": 1,
            "status": "ready_for_review",
            "signal": "EXPLICIT",
            "executor": {"id": "dev-mock", "cli": "mock-cli"},
            "full_document": {
                "path": escaped_path,
                "evidence_commit": head,
                "sha256": hashlib.sha256(external_doc.read_bytes()).hexdigest(),
            },
            "development": {"quality_metrics": {"tests_passed": True}, "git": {"latest_commit": head}},
        }
        manifest_path = repo / ".macao" / ".dev.yml"
        manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

        change = orchestrator.check_development_checkpoint(task["task_id"])
        state = orchestrator.store.get_task(task["task_id"])["state"]
        assert change is not None and state == AgentState.READY_FOR_REVIEW.value, state
        assert not external_doc.is_relative_to(repo.resolve())

        # A document created after the declared evidence commit is also accepted:
        # runtime code compares only the current working-tree bytes, not the blob
        # at evidence_commit.
        orchestrator.cancel_task(task["task_id"], reason="next provenance case")
        uncommitted_doc = repo / "docs" / "reviews" / "written-after-checkpoint.md"
        uncommitted_doc.parent.mkdir(parents=True, exist_ok=True)
        uncommitted_doc.write_text("not part of HEAD\n", encoding="utf-8")
        task2 = orchestrator.start_task(title="uncommitted", task_description="reproduce")
        manifest["task_id"] = task2["task_id"]
        manifest["full_document"] = {
            "path": str(uncommitted_doc.relative_to(repo)),
            "evidence_commit": head,
            "sha256": hashlib.sha256(uncommitted_doc.read_bytes()).hexdigest(),
        }
        manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
        change2 = orchestrator.check_development_checkpoint(task2["task_id"])
        state2 = orchestrator.store.get_task(task2["task_id"])["state"]
        assert change2 is not None and state2 == AgentState.READY_FOR_REVIEW.value, state2
        tracked = subprocess.run(
            ["git", "cat-file", "-e", f"{head}:docs/reviews/written-after-checkpoint.md"],
            cwd=repo,
            capture_output=True,
        )
        assert tracked.returncode != 0, "fixture document unexpectedly exists in HEAD"
        print("REPRODUCED: sibling escape and uncommitted document both advanced to READY_FOR_REVIEW")
    finally:
        reset_db_manager()
        shutil.rmtree(repo, ignore_errors=True)
        shutil.rmtree(sibling, ignore_errors=True)


if __name__ == "__main__":
    main()
