#!/usr/bin/env python3
"""Isolated Codex P1-04 counterexamples for 7bc8d70.

issue_id: grok/P1-1 (Codex P1-04 residual)
commit: 7bc8d7091ba4e39c0b3282492c613817f8d664e9
platform: Linux; no network; no vendor CLI required
last_executed: 2026-09-08T00:55:55+08:00

Each case creates a fresh CODING task so a prior fail-open cannot pollute later asserts.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/home/debian/macao/src")
os.environ["PYTHONPATH"] = "/home/debian/macao/src" + os.pathsep + os.environ.get("PYTHONPATH", "")

import yaml
from macao.cli.main import DEFAULT_CONFIG_TEMPLATE
from macao.core.types import AgentState
from macao.workflow.orchestrator import Orchestrator
import macao.storage.db as db_mod


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def main():
    orig = os.getcwd()
    tmp = Path(tempfile.mkdtemp(prefix="p104_"))
    try:
        os.chdir(tmp)
        db_mod._db_manager = None
        git(tmp, "init", "-b", "main")
        git(tmp, "config", "user.name", "t")
        git(tmp, "config", "user.email", "t@t.dev")
        (tmp / "README.md").write_text("x\n")
        git(tmp, "add", "README.md")
        git(tmp, "commit", "-m", "init")
        cfg = yaml.safe_load(DEFAULT_CONFIG_TEMPLATE)
        cfg["project"]["name"] = "p104"
        cfg["team"]["executor"] = {"id": "dev-mock", "cli": "mock-cli", "adapter": "pty-wrapper"}
        cfg["team"]["reviewers"] = [
            {"id": "r1", "cli": "mock-cli", "adapter": "pty-wrapper", "vote_weight": 1.0}
        ]
        (tmp / "macao.yaml").write_text(yaml.dump(cfg))
        req = tmp / "docs" / "reviews" / "req.md"
        req.parent.mkdir(parents=True)
        req.write_text("Official Review Request Content\n", encoding="utf-8")
        head = git(tmp, "rev-parse", "HEAD").stdout.strip()
        true_sha = hashlib.sha256(req.read_bytes()).hexdigest()

        def write_dev(t_id, sha, exec_id="dev-mock", exec_cli="mock-cli", path="docs/reviews/req.md"):
            manifest = {
                "version": "1.0",
                "task_id": t_id,
                "checkpoint_ref": head,
                "full_document": {"path": path, "evidence_commit": head, "sha256": sha},
                "status": "ready_for_review",
                "signal": "EXPLICIT",
                "review_round": 1,
                "executor": {"id": exec_id, "cli": exec_cli},
                "development": {
                    "quality_metrics": {"tests_passed": True},
                    "git": {"latest_commit": head},
                },
            }
            p = tmp / ".macao" / ".dev.yml"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(yaml.safe_dump(manifest))

        def run_case(name, **kwargs):
            db_mod._db_manager = None
            orch = Orchestrator(".")
            task = orch.start_task(title=name, task_description="d")
            t_id = task["task_id"]
            write_dev(t_id, **kwargs)
            ch = orch.check_development_checkpoint(t_id)
            st = orch.store.get_task(t_id)["state"]
            advanced = st == AgentState.READY_FOR_REVIEW.value
            print(f"{name}: advanced={advanced} trigger={getattr(ch, 'trigger', None)}")
            orch.cancel_task(t_id, reason="next case")
            return name, advanced

        rows = [
            run_case("zero_hash", sha="0" * 64),
            run_case("missing_path", sha=true_sha, path="docs/reviews/does-not-exist.md"),
            run_case("empty_sha", sha=""),
            run_case("wrong_id", sha=true_sha, exec_id="imposter"),
            run_case("wrong_cli", sha=true_sha, exec_cli="claude-code"),
            run_case("tampered", sha="ab" * 32),
            run_case("good", sha=true_sha),
            run_case("outside_path", sha=true_sha, path="/etc/passwd"),
        ]
        # Fail-closed expectations for Codex P1-04 / UC-3 d5-d6
        expect_block = {"zero_hash", "missing_path", "empty_sha", "wrong_id", "wrong_cli", "tampered", "outside_path"}
        expect_pass = {"good"}
        bad = []
        for name, advanced in rows:
            if name in expect_block and advanced:
                bad.append(name)
            if name in expect_pass and not advanced:
                bad.append(name)
        print("FAIL_OPEN" if bad else "ALL_MATCH_CLAIM")
        print("fail_open_cases=" + ",".join(bad))
        return 1 if bad else 0
    finally:
        os.chdir(orig)
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
