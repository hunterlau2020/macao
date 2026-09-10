#!/usr/bin/env python3
"""Reproduce P1-51fa456-01 against commit 51fa456ada474818a1107f1a11b061661dab1063.

Issue: the checkpoint validator resolves ``full_document.path`` before it
checks the Git tree.  An untracked symlink can therefore name an arbitrary
path while borrowing a committed target document's blob and digest.

Last executed: 2026-09-10 Asia/Taipei
Prerequisites: Python 3.10+, git; no network and no vendor CLI credentials.
The script creates and removes its own temporary Git clone and test project.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


TARGET = "51fa456ada474818a1107f1a11b061661dab1063"
SOURCE_ROOT = Path(__file__).resolve().parents[4]


def run(*args: str, cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(args)}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.stdout.strip()


def main() -> None:
    sandbox = Path(tempfile.mkdtemp(prefix="macao-51fa456-symlink-"))
    try:
        checkout = sandbox / "checkout"
        project = sandbox / "project"
        run("git", "clone", "--quiet", "--no-local", str(SOURCE_ROOT), str(checkout), cwd=sandbox)
        run("git", "checkout", "--quiet", TARGET, cwd=checkout)
        sys.path.insert(0, str(checkout / "src"))

        from macao.core.types import AgentState
        from macao.utils.git_utils import GitManager
        from macao.workflow.orchestrator import Orchestrator

        run("git", "init", "-q", "-b", "main", str(project), cwd=sandbox)
        run("git", "config", "user.name", "reviewer", cwd=project)
        run("git", "config", "user.email", "reviewer@example.test", cwd=project)
        trusted = project / "docs" / "reviews" / "committed.md"
        trusted.parent.mkdir(parents=True)
        trusted.write_text("# Committed evidence\n", encoding="utf-8")
        run("git", "add", "docs/reviews/committed.md", cwd=project)
        run("git", "commit", "-qm", "initial evidence", cwd=project)

        config = {
            "version": "2.5",
            "team": {
                "executor": {"id": "dev", "cli": "mock-cli"},
                "reviewers": [{"id": "reviewer", "cli": "mock-cli"}],
            },
        }
        orchestrator = Orchestrator(str(project), config=config)
        task = orchestrator.start_task("symlink evidence", "negative checkpoint test")
        head = GitManager(str(project)).get_head_commit()

        declared_path = trusted.with_name("untracked-alias.md")
        declared_path.symlink_to(trusted.name)
        declared_rel = declared_path.relative_to(project).as_posix()
        assert GitManager(str(project))._run(
            "cat-file", "-e", f"{head}:{declared_rel}"
        )[0] != 0, "the declared path must be absent from the evidence commit"

        manifest = {
            "version": "1.0",
            "task_id": task["task_id"],
            "checkpoint_ref": head,
            "review_round": 1,
            "signal": "EXPLICIT",
            "status": "ready_for_review",
            "executor": {"id": "dev", "cli": "mock-cli"},
            "full_document": {
                "path": declared_rel,
                "evidence_commit": head,
                "sha256": hashlib.sha256(declared_path.read_bytes()).hexdigest(),
            },
            "development": {
                "quality_metrics": {"tests_passed": True},
                "git": {"latest_commit": head},
            },
        }
        dev_manifest = project / ".macao" / ".dev.yml"
        dev_manifest.parent.mkdir(exist_ok=True)
        dev_manifest.write_text(yaml.safe_dump(manifest), encoding="utf-8")

        change = orchestrator.check_development_checkpoint(task["task_id"])
        state = orchestrator.store.get_task(task["task_id"])["state"]
        assert change is not None, "a safe implementation must reject this checkpoint"
        assert state == AgentState.READY_FOR_REVIEW.value, state
        print("REPRODUCED: untracked symlink declaration advanced to READY_FOR_REVIEW")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


if __name__ == "__main__":
    main()
