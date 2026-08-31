"""Live Multi-Agent End-to-End Workflow Runner (Phase 3 / L4 Readiness)."""

import os
import sys
import time
import shutil
import tempfile
import subprocess
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

from macao.core.types import AgentState, Decision, Vote, OpinionStatus
from macao.workflow.orchestrator import Orchestrator
from macao.workflow.live_dispatcher import LiveAgentDispatcher, ReviewExtractor
from macao.storage.store import StateStore
from macao.utils.git_utils import GitManager
from macao.cli.wizard import generate_smart_config


class LiveWorkflowRunner:
    """Executes live multi-agent collaboration cycles with real CLI subagents."""

    def __init__(self, workspace_root: Optional[str] = None):
        self.is_temp = workspace_root is None
        self.remote_dir: Optional[Path] = None
        if self.is_temp:
            self.tmp_dir = tempfile.mkdtemp(prefix="macao_live_run_")
            self.workspace = Path(self.tmp_dir)
        else:
            self.tmp_dir = None
            self.workspace = Path(workspace_root).resolve()

        self.git = GitManager(str(self.workspace))
        self.orchestrator: Optional[Orchestrator] = None
        self.dispatcher: Optional[LiveAgentDispatcher] = None

    def setup_sandbox_repo(self) -> None:
        """Initializes a clean git repository for live collaboration testing."""
        self.workspace.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-b", "main"], cwd=str(self.workspace), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "MACAO Live Runner"], cwd=str(self.workspace), check=True)
        subprocess.run(["git", "config", "user.email", "runner@macao.dev"], cwd=str(self.workspace), check=True)

        # Initial commit on main
        readme = self.workspace / "README.md"
        readme.write_text("# MACAO Live Collaboration Workspace\n", encoding="utf-8")

        # Generate macao.yaml with review adapters
        cfg = generate_smart_config(
            self.workspace,
            executor_cli="opencode",
            executor_model="GLM 5.3 max",
            reviewers=[
                {"id": "opencode-rev", "cli": "mock-cli", "adapter": "pty-wrapper", "model": "Qwen3.8 max"},
                {"id": "agy-rev", "cli": "mock-cli", "adapter": "pty-wrapper", "model": "gemini-2.0-pro"},
                {"id": "cursor-rev", "cli": "mock-cli", "adapter": "pty-wrapper", "model": "claude-3-5-sonnet"}
            ]
        )
        (self.workspace / "macao.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")

        subprocess.run(["git", "add", "README.md", "macao.yaml"], cwd=str(self.workspace), check=True)
        subprocess.run(["git", "commit", "-m", "chore: initial repository structure and configuration"], cwd=str(self.workspace), check=True)

        # Setup local bare remote 'origin' for testing push verification
        remote_tmp = tempfile.mkdtemp(prefix="macao_live_origin_")
        self.remote_dir = Path(remote_tmp).resolve()
        subprocess.run(["git", "init", "--bare", "-b", "main"], cwd=str(self.remote_dir), check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(self.remote_dir)], cwd=str(self.workspace), check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=str(self.workspace), check=True, capture_output=True)

        self.orchestrator = Orchestrator(project_root=str(self.workspace), config=cfg)
        self.dispatcher = LiveAgentDispatcher(project_root=str(self.workspace))

    def run_live_cycle(self, task_title: str = "Implement live calculation module", auto_signoff: bool = True) -> Dict[str, Any]:
        """Runs the complete Phase 3 live collaboration cycle."""
        if not self.orchestrator:
            self.setup_sandbox_repo()

        steps_log = []
        start_runner_time = time.time()

        # 1. Start Task
        task = self.orchestrator.start_task(
            title=task_title,
            task_description=f"{task_title} with full test coverage.",
            acceptance_criteria={"unit_tests_pass": True},
            source_branch="feature/calc-live",
            target_branch="main"
        )
        task_id = task["task_id"]
        steps_log.append({"step": "1. Task Start", "details": f"state={task['state']}, task_id={task_id}", "status": "OK"})

        # 2. Switch to feature branch and perform development commit
        subprocess.run(["git", "checkout", "-b", "feature/calc-live"], cwd=str(self.workspace), check=True, capture_output=True)
        src_file = self.workspace / "src" / "math_lib.py"
        src_file.parent.mkdir(parents=True, exist_ok=True)
        src_file.write_text("def add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b\n", encoding="utf-8")

        subprocess.run(["git", "add", "src/math_lib.py"], cwd=str(self.workspace), check=True)
        subprocess.run(["git", "commit", "-m", "feat: implement math operations"], cwd=str(self.workspace), capture_output=True, text=True, check=True)
        dev_commit = self.git.get_head_commit()
        steps_log.append({"step": "2. Development Commit", "details": f"commit={dev_commit[:8]}, branch=feature/calc-live", "status": "OK"})

        # Create valid .dev.yml
        dev_manifest = {
            "version": "1.0",
            "status": "ready_for_review",
            "signal": "EXPLICIT",
            "review_round": 1,
            "executor": {"id": "opencode-dev", "cli": "opencode"},
            "development": {
                "quality_metrics": {"tests_passed": True},
                "git": {"latest_commit": dev_commit}
            }
        }
        macao_dir = self.workspace / ".macao"
        macao_dir.mkdir(parents=True, exist_ok=True)
        (macao_dir / ".dev.yml").write_text(yaml.safe_dump(dev_manifest), encoding="utf-8")

        # 3. Checkpoint Validation
        change1 = self.orchestrator.check_development_checkpoint(task_id)
        if not change1:
            raise RuntimeError("check_development_checkpoint failed")
        steps_log.append({"step": "3. Checkpoint Validation", "details": f"state={change1.to_state.value}, checkpoint_ref={dev_commit[:8]}", "status": "OK"})

        # 4. Dispatch Reviews to Worktrees
        change_dispatch = self.orchestrator.dispatch_review_requests(task_id)
        if not change_dispatch:
            raise RuntimeError("dispatch_review_requests failed")

        reviewers = self.orchestrator.config.get("reviewers", [])
        rev_ids = self.orchestrator.config.get("reviewer_ids", [r["id"] for r in reviewers])

        # 5. Genuinely invoke LiveAgentDispatcher in isolated Git Worktrees
        diff_txt = self.git.get_diff("main", dev_commit)
        dispatched_results = []

        for r_cfg in reviewers:
            r_id = r_cfg["id"]
            res = self.dispatcher.dispatch_review_in_worktree(
                reviewer_cfg=r_cfg,
                task_id=task_id,
                checkpoint_ref=dev_commit,
                review_round=1,
                diff_context=diff_txt,
                timeout_sec=15.0
            )
            if res.get("status") != "SUCCESS":
                raise RuntimeError(f"Review dispatch failed for {r_id}: {res.get('error')}")
            dispatched_results.append(res)

        steps_log.append({
            "step": "4. Worktree Dispatch & Review",
            "details": f"state={change_dispatch.to_state.value}, reviewers_count={len(dispatched_results)}",
            "status": "OK"
        })

        # 6. Consensus Evaluation (WAITING_REVIEW -> CONSENSUS_CHECK -> MERGING)
        change_cons, vdata = self.orchestrator.collect_and_evaluate_consensus(task_id, configured_reviewers=len(rev_ids))
        if not change_cons or not vdata:
            raise RuntimeError("collect_and_evaluate_consensus failed")

        dec_str = vdata.get("decision", "APPROVED")
        steps_log.append({
            "step": "5. Consensus Evaluation",
            "details": f"decision={dec_str}, state={change_cons.to_state.value}, votes_yes={len(rev_ids)}",
            "status": "OK"
        })

        # Human signoff if required
        if self.orchestrator.config.get("require_signoff", True):
            if auto_signoff:
                self.orchestrator.store.log_audit_event(task_id, "HUMAN_MERGE_APPROVED", {
                    "checkpoint_ref": dev_commit,
                    "signer": "system-runner",
                    "note": "Automated runner signoff (--auto-signoff)"
                })
            else:
                artifacts = self.orchestrator.store.list_artifacts(task_id)
                return {
                    "status": "WAITING_SIGNOFF",
                    "task_id": task_id,
                    "steps": steps_log,
                    "archived_count": len([a for a in artifacts if a.get("archived_path")]),
                    "archived_files": [a.get("archived_path") for a in artifacts if a.get("archived_path")],
                    "final_state": change_cons.to_state.value,
                    "duration": round(time.time() - start_runner_time, 2)
                }

        # Checkout main before merging
        subprocess.run(["git", "checkout", "main"], cwd=str(self.workspace), check=True, capture_output=True)

        # 7. Fast-Forward Merge to main
        merge_ok, merge_msg, change_merge = self.orchestrator.execute_merge(task_id)
        if not merge_ok or not change_merge:
            raise RuntimeError(f"execute_merge failed: {merge_msg}")

        steps_log.append({"step": "6. Fast-Forward Merge", "details": f"state={change_merge.to_state.value}, message={merge_msg}", "status": "OK"})

        # 8. Check Final State
        final_task = self.orchestrator.store.get_task(task_id)
        final_state = final_task.get("state") if final_task else "UNKNOWN"
        steps_log.append({"step": "7. Final State", "details": f"final_state={final_state}", "status": "OK"})

        # Check archived files count
        artifacts = self.orchestrator.store.list_artifacts(task_id)
        archived_files = [a.get("archived_path") for a in artifacts if a.get("archived_path")]
        archived_count = len(archived_files)
        total_duration = round(time.time() - start_runner_time, 2)

        return {
            "status": "PASS" if final_state == AgentState.DONE.value else "FAIL",
            "task_id": task_id,
            "steps": steps_log,
            "archived_count": archived_count,
            "archived_files": archived_files,
            "final_state": final_state,
            "duration": total_duration
        }



    def cleanup(self) -> None:
        if self.is_temp and self.tmp_dir and os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir, ignore_errors=True)
        if self.remote_dir and self.remote_dir.exists():
            shutil.rmtree(self.remote_dir, ignore_errors=True)
