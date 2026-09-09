#!/usr/bin/env python3
"""Reproduce remaining P1 gaps in bdc177e.

Issues: P1-bdc177e-01 (untracked full_document accepted) and
P1-bdc177e-02 (unknown configured executor silently becomes None).
Target commit: bdc177eaaff577e119093e686f2164bcc133f781.
Prerequisites: Python 3.10+, Git, PyYAML/jsonschema; run with PYTHONPATH=src.
No network, vendor CLI, or pre-existing repository state is used.
Last executed: 2026-09-10 Asia/Taipei.
"""

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml
from click.testing import CliRunner

from macao.cli.main import DEFAULT_CONFIG_TEMPLATE, cli, get_orchestrator
from macao.core.types import AgentState
from macao.storage.db import reset_db_manager
from macao.storage.store import StateStore
from macao.workflow.orchestrator import Orchestrator


CONFIG = {
    "version": "2.5",
    "project": {"name": "repro", "repository": {"workspace_path": ".", "default_branch": "main"}},
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


class NoopExecutor:
    agent_id = "dev-mock"
    cli_name = "mock-cli"

    def start(self):
        return True

    def inject_task(self, payload):
        return True


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, text=True, capture_output=True).stdout.strip()


def init_repo(repo):
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Review Reproducer")
    git(repo, "config", "user.email", "review@example.test")
    (repo / "README.md").write_text("root\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "initial")
    return git(repo, "rev-parse", "HEAD")


def reproduce_untracked_document(repo):
    head = init_repo(repo)
    reset_db_manager()
    orchestrator = Orchestrator(str(repo), config=CONFIG, executor_adapter=NoopExecutor())
    task = orchestrator.start_task(title="untracked document", task_description="reproduce")
    document = repo / "docs" / "reviews" / "written-after-head.md"
    document.parent.mkdir(parents=True)
    document.write_text("this document is not in the declared commit\n", encoding="utf-8")
    manifest = {
        "version": "1.0",
        "task_id": task["task_id"],
        "checkpoint_ref": head,
        "review_round": 1,
        "status": "ready_for_review",
        "signal": "EXPLICIT",
        "executor": {"id": "dev-mock", "cli": "mock-cli"},
        "full_document": {
            "path": str(document.relative_to(repo)),
            "evidence_commit": head,
            "sha256": hashlib.sha256(document.read_bytes()).hexdigest(),
        },
        "development": {"quality_metrics": {"tests_passed": True}, "git": {"latest_commit": head}},
    }
    manifest_path = repo / ".macao" / ".dev.yml"
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    change = orchestrator.check_development_checkpoint(task["task_id"])
    state = orchestrator.store.get_task(task["task_id"])["state"]
    in_commit = subprocess.run(
        ["git", "cat-file", "-e", f"{head}:docs/reviews/written-after-head.md"],
        cwd=repo,
        capture_output=True,
    )
    assert in_commit.returncode != 0, "fixture unexpectedly added document to HEAD"
    assert change is not None and state == AgentState.READY_FOR_REVIEW.value, state


def reproduce_unknown_executor(repo):
    init_repo(repo)
    cfg = DEFAULT_CONFIG_TEMPLATE.replace('cli: "claude-code"', 'cli: "unknown-executor"', 1)
    (repo / "macao.yaml").write_text(cfg, encoding="utf-8")
    reset_db_manager()
    assert get_orchestrator(str(repo)).executor is None
    original_cwd = Path.cwd()
    try:
        os.chdir(repo)
        result = CliRunner().invoke(
            cli,
            ["task", "create", "--no-probe", "--title", "lost executor", "--acceptance", "must-run"],
        )
        assert result.exit_code == 0, result.output
        active = StateStore(".macao/state.db").get_active_task()
        assert active is not None and active["state"] == AgentState.CODING.value
    finally:
        os.chdir(original_cwd)


def main():
    root = Path(tempfile.mkdtemp(prefix="macao-bdc177e-repro-"))
    first = root / "untracked"
    second = root / "unknown-executor"
    first.mkdir()
    second.mkdir()
    try:
        reproduce_untracked_document(first)
        reset_db_manager()
        reproduce_unknown_executor(second)
        print("REPRODUCED: untracked document accepted and unknown executor creates CODING task")
    finally:
        reset_db_manager()
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
