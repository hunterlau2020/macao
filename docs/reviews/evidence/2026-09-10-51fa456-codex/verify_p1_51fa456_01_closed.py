#!/usr/bin/env python3
"""Verification probe demonstrating that P1-51fa456-01 is CLOSED.

Verifies:
1. Untracked symlinks are rejected (change is None, state remains CODING).
2. Committed symlinks in Git (mode 120000) are rejected.
3. Parent directory symlinks are rejected.
4. Legitimate regular committed files are accepted (state advances to READY_FOR_REVIEW).

Exit code: 0 on success.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

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
    sandbox = Path(tempfile.mkdtemp(prefix="macao-verify-symlink-"))
    try:
        sys.path.insert(0, str(SOURCE_ROOT / "src"))

        from macao.core.types import AgentState
        from macao.utils.git_utils import GitManager
        from macao.workflow.orchestrator import Orchestrator

        project = sandbox / "project"
        run("git", "init", "-q", "-b", "main", str(project), cwd=sandbox)
        run("git", "config", "user.name", "tester", cwd=project)
        run("git", "config", "user.email", "tester@example.com", cwd=project)

        # 1. Setup real committed document
        trusted = project / "docs" / "reviews" / "committed.md"
        trusted.parent.mkdir(parents=True)
        trusted.write_text("# Committed evidence\n", encoding="utf-8")
        run("git", "add", "docs/reviews/committed.md", cwd=project)

        # 2. Setup committed symlink (mode 120000)
        committed_sym = project / "docs" / "reviews" / "committed_sym.md"
        committed_sym.symlink_to(trusted.name)
        run("git", "add", "docs/reviews/committed_sym.md", cwd=project)

        # 3. Setup parent dir symlink
        outside = project / "docs" / "outside"
        outside.mkdir(parents=True)
        (outside / "target.md").write_text("# Target doc\n", encoding="utf-8")
        sym_dir = project / "docs" / "reviews" / "sym_dir"
        sym_dir.symlink_to("../outside")

        run("git", "add", ".", cwd=project)
        run("git", "commit", "-qm", "initial evidence setup", cwd=project)

        config = {
            "version": "2.5",
            "team": {
                "executor": {"id": "dev", "cli": "mock-cli"},
                "reviewers": [{"id": "reviewer", "cli": "mock-cli"}],
            },
        }
        orchestrator = Orchestrator(str(project), config=config)
        head = GitManager(str(project)).get_head_commit()
        trusted_sha = hashlib.sha256(trusted.read_bytes()).hexdigest()

        # Setup untracked symlink pointing to committed.md
        untracked_alias = trusted.with_name("untracked-alias.md")
        untracked_alias.symlink_to(trusted.name)

        # Test Case 1: Untracked symlink -> MUST BE REJECTED
        t1 = orchestrator.start_task("untracked symlink test", "desc", force=True)
        m1 = {
            "version": "1.0",
            "task_id": t1["task_id"],
            "checkpoint_ref": head,
            "review_round": 1,
            "signal": "EXPLICIT",
            "status": "ready_for_review",
            "executor": {"id": "dev", "cli": "mock-cli"},
            "full_document": {
                "path": "docs/reviews/untracked-alias.md",
                "evidence_commit": head,
                "sha256": trusted_sha,
            },
            "development": {
                "quality_metrics": {"tests_passed": True},
                "git": {"latest_commit": head},
            },
        }
        (project / ".macao" / ".dev.yml").write_text(yaml.safe_dump(m1), encoding="utf-8")
        ch1 = orchestrator.check_development_checkpoint(t1["task_id"])
        st1 = orchestrator.store.get_task(t1["task_id"])["state"]
        assert ch1 is None, f"Untracked symlink must return None, got {ch1}"
        assert st1 == AgentState.CODING.value, f"State must remain CODING, got {st1}"
        print("PASS: Untracked symlink correctly rejected (CODING preserved)")

        # Test Case 2: Committed symlink -> MUST BE REJECTED
        t2 = orchestrator.start_task("committed symlink test", "desc", force=True)
        m2 = dict(m1)
        m2["task_id"] = t2["task_id"]
        m2["full_document"] = {
            "path": "docs/reviews/committed_sym.md",
            "evidence_commit": head,
            "sha256": trusted_sha,
        }
        (project / ".macao" / ".dev.yml").write_text(yaml.safe_dump(m2), encoding="utf-8")
        ch2 = orchestrator.check_development_checkpoint(t2["task_id"])
        st2 = orchestrator.store.get_task(t2["task_id"])["state"]
        assert ch2 is None, f"Committed symlink must return None, got {ch2}"
        assert st2 == AgentState.CODING.value, f"State must remain CODING, got {st2}"
        print("PASS: Committed symlink in Git tree correctly rejected (CODING preserved)")

        # Test Case 3: Parent dir symlink -> MUST BE REJECTED
        t3 = orchestrator.start_task("parent dir symlink test", "desc", force=True)
        m3 = dict(m1)
        m3["task_id"] = t3["task_id"]
        m3["full_document"] = {
            "path": "docs/reviews/sym_dir/target.md",
            "evidence_commit": head,
            "sha256": hashlib.sha256((outside / "target.md").read_bytes()).hexdigest(),
        }
        (project / ".macao" / ".dev.yml").write_text(yaml.safe_dump(m3), encoding="utf-8")
        ch3 = orchestrator.check_development_checkpoint(t3["task_id"])
        st3 = orchestrator.store.get_task(t3["task_id"])["state"]
        assert ch3 is None, f"Parent dir symlink must return None, got {ch3}"
        assert st3 == AgentState.CODING.value, f"State must remain CODING, got {st3}"
        print("PASS: Parent directory symlink correctly rejected (CODING preserved)")

        # Test Case 4: Legitimate regular committed file -> MUST ADVANCE
        t4 = orchestrator.start_task("legitimate regular file test", "desc", force=True)
        m4 = dict(m1)
        m4["task_id"] = t4["task_id"]
        m4["full_document"] = {
            "path": "docs/reviews/committed.md",
            "evidence_commit": head,
            "sha256": trusted_sha,
        }
        (project / ".macao" / ".dev.yml").write_text(yaml.safe_dump(m4), encoding="utf-8")
        ch4 = orchestrator.check_development_checkpoint(t4["task_id"])
        st4 = orchestrator.store.get_task(t4["task_id"])["state"]
        assert ch4 is not None, "Legitimate committed file must advance"
        assert st4 == AgentState.READY_FOR_REVIEW.value, f"State must be READY_FOR_REVIEW, got {st4}"
        print("PASS: Legitimate committed regular file successfully advanced to READY_FOR_REVIEW")

        print("\nALL SYMLINK REMEDIATION CHECKS PASSED (P1-51fa456-01 CLOSED)")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


if __name__ == "__main__":
    main()
