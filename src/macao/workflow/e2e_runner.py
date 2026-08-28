"""MACAO End-to-End Controlled Integration Runner (Phase 2 Micro-Task Collaboration)."""

import os
import yaml
import shutil
import tempfile
import datetime
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from macao.core.config import ConfigManager
from macao.core.types import AgentState, Decision, Vote, OpinionStatus, ExecutionMode
from macao.storage.store import StateStore
from macao.workflow.orchestrator import Orchestrator
from macao.adapter.mock import MockAgentAdapter
from macao.utils.git_utils import GitManager


class ControlledE2ERunner:
    """Executes a full end-to-end micro-task collaboration simulation workflow."""

    def __init__(self, base_dir: Optional[str] = None):
        self.temp_dir: Optional[str] = None
        self.remote_dir: Optional[Path] = None
        if base_dir:
            self.repo_dir = Path(base_dir).resolve()
        else:
            self.temp_dir = tempfile.mkdtemp(prefix="macao_e2e_phase2_")
            self.repo_dir = Path(self.temp_dir).resolve()

        self.db_path = str(self.repo_dir / ".macao" / "state.db")
        self.config: Dict[str, Any] = {}

    def setup_repo(self) -> None:
        """Initializes a clean Git repository with target branch 'main' and bare remote 'origin'."""
        self.repo_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-b", "main"], cwd=str(self.repo_dir), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "MACAO Bot"], cwd=str(self.repo_dir), check=True)
        subprocess.run(["git", "config", "user.email", "bot@macao.dev"], cwd=str(self.repo_dir), check=True)

        # Initial commit
        readme = self.repo_dir / "README.md"
        readme.write_text("# MACAO Micro-Task Collaboration Sandbox\n", encoding="utf-8")

        gitignore = self.repo_dir / ".gitignore"
        gitignore.write_text(".macao/\n__pycache__/\n*.pyc\n", encoding="utf-8")

        # Default macao.yaml
        cfg_content = """project:
  name: "macao-micro-calc"
  repository:
    workspace_path: "."
    remote_name: "origin"
    default_branch: "main"

team:
  executor:
    id: "claude-code"
    cli: "claude-code"
    adapter: "claude-hook"
  reviewers:
    - id: "codex"
      cli: "codex"
      adapter: "pty-wrapper"
    - id: "opencode"
      cli: "opencode"
      adapter: "pty-wrapper"
    - id: "antigravity"
      cli: "agy"
      adapter: "pty-wrapper"

policy:
  consensus_rule: "2/3_majority"
  min_effective_votes: 2
  max_rework_rounds: 3
  review_strategy: "delta_plus_focus"

merge:
  strategy: "ff_only"
  ci_gate_command: null
  require_human_signoff: false
  rebase_before_merge: false
"""
        (self.repo_dir / "macao.yaml").write_text(cfg_content, encoding="utf-8")
        subprocess.run(["git", "add", "README.md", ".gitignore", "macao.yaml"], cwd=str(self.repo_dir), check=True)
        subprocess.run(["git", "commit", "-m", "chore: initial repository structure and configuration"], cwd=str(self.repo_dir), check=True)

        # Setup local bare remote 'origin' for testing push verification
        remote_tmp = tempfile.mkdtemp(prefix="macao_remote_origin_")
        self.remote_dir = Path(remote_tmp).resolve()
        subprocess.run(["git", "init", "--bare", "-b", "main"], cwd=str(self.remote_dir), check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(self.remote_dir)], cwd=str(self.repo_dir), check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=str(self.repo_dir), check=True, capture_output=True)

        self.config = ConfigManager.load_config(str(self.repo_dir / "macao.yaml"))

    def run_e2e_cycle(self) -> Dict[str, Any]:
        """Runs the complete micro-task lifecycle from CODING to DONE."""
        if not (self.repo_dir / ".git").exists():
            self.setup_repo()

        steps_log: List[Dict[str, Any]] = []

        # Instantiate real/mock adapters injected from configuration
        executor_adapter = MockAgentAdapter(
            agent_id="claude-code",
            cli_name="claude-code",
            role="executor"
        )
        reviewer_adapters = [
            MockAgentAdapter(agent_id="codex", cli_name="codex", role="reviewer"),
            MockAgentAdapter(agent_id="opencode", cli_name="opencode", role="reviewer"),
            MockAgentAdapter(agent_id="antigravity", cli_name="agy", role="reviewer")
        ]

        orchestrator = Orchestrator(
            project_root=str(self.repo_dir),
            config=self.config,
            executor_adapter=executor_adapter,
            reviewer_adapters=reviewer_adapters
        )

        # 1. Start Task
        task_data = orchestrator.start_task(
            title="Implement Safe Arithmetic Module with Unit Tests",
            task_description="Implement add(a, b) and subtract(a, b) in src/calc.py with tests",
            acceptance_criteria={"unit_tests_pass": True, "coverage": 100},
            source_branch="feature/micro-calc",
            target_branch="main"
        )
        task_id = task_data["task_id"]
        steps_log.append({"step": "1. Task Start", "state": task_data["state"], "task_id": task_id})

        # 2. Checkout feature branch and implement code
        subprocess.run(["git", "checkout", "-b", "feature/micro-calc"], cwd=str(self.repo_dir), check=True, capture_output=True)
        src_dir = self.repo_dir / "src"
        src_dir.mkdir(exist_ok=True)
        calc_file = src_dir / "calc.py"
        calc_file.write_text(
            '"""Safe Arithmetic Module."""\n\n'
            'def add(a: float, b: float) -> float:\n'
            '    return a + b\n\n'
            'def subtract(a: float, b: float) -> float:\n'
            '    return a - b\n',
            encoding="utf-8"
        )

        test_dir = self.repo_dir / "tests"
        test_dir.mkdir(exist_ok=True)
        test_file = test_dir / "test_calc.py"
        test_file.write_text(
            'import unittest\n'
            'from src.calc import add, subtract\n\n'
            'class TestCalc(unittest.TestCase):\n'
            '    def test_add(self):\n'
            '        self.assertEqual(add(2, 3), 5)\n'
            '    def test_subtract(self):\n'
            '        self.assertEqual(subtract(5, 2), 3)\n\n'
            'if __name__ == "__main__":\n'
            '    unittest.main()\n',
            encoding="utf-8"
        )

        # Commit code to produce checkpoint_ref
        subprocess.run(["git", "add", "src/", "tests/"], cwd=str(self.repo_dir), check=True)
        subprocess.run(["git", "commit", "-m", "feat: implement add and subtract functions with unit tests"], cwd=str(self.repo_dir), check=True)

        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(self.repo_dir), capture_output=True, text=True, check=True)
        checkpoint_ref = res.stdout.strip()

        # Write valid Schema .dev.yml
        macao_dir = self.repo_dir / ".macao"
        macao_dir.mkdir(parents=True, exist_ok=True)
        dev_manifest = {
            "version": "1.0",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "executor": {"id": "claude-code", "role": "executor", "cli": "claude-code"},
            "development": {
                "description": "Implemented safe add and subtract operations with 100% test coverage",
                "artifacts": [{"path": "src/calc.py"}, {"path": "tests/test_calc.py"}],
                "quality_metrics": {"tests_passed": True},
                "git": {
                    "base_commit": "main",
                    "latest_commit": checkpoint_ref,
                    "branch": "feature/micro-calc",
                    "changed_files": ["src/calc.py", "tests/test_calc.py"]
                }
            },
            "review_round": 1,
            "status": "ready_for_review",
            "signal": "EXPLICIT"
        }
        with open(macao_dir / ".dev.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump(dev_manifest, f)

        # 3. Check Development Checkpoint
        change1 = orchestrator.check_development_checkpoint(task_id)
        if change1 is None:
            raise RuntimeError("check_development_checkpoint failed to transition to READY_FOR_REVIEW")

        steps_log.append({
            "step": "2. Checkpoint Validation",
            "state": change1.to_state.value,
            "checkpoint_ref": checkpoint_ref[:8]
        })

        # 4. Dispatch Review Requests (creates 3 isolated worktrees for configured reviewers)
        change_dispatch = orchestrator.dispatch_review_requests(task_id)
        if change_dispatch is None:
            raise RuntimeError("dispatch_review_requests failed to transition to WAITING_REVIEW")

        reviewers = [r.agent_id for r in reviewer_adapters]
        steps_log.append({
            "step": "3. Worktree Dispatch",
            "state": change_dispatch.to_state.value,
            "reviewers_count": len(reviewers),
            "reviewers": reviewers
        })

        # 5. Reviewers generate reviews in their isolated worktrees
        reviews_dir = macao_dir / ".reviews"
        reviews_dir.mkdir(parents=True, exist_ok=True)

        for r_id in reviewers:
            rev_manifest = {
                "version": "1.0",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "reviewer": {"id": r_id, "cli": r_id},
                "checkpoint_ref": checkpoint_ref,
                "review_round": 1,
                "opinion": {
                    "status": "APPROVED",
                    "confidence": 0.95,
                    "summary": f"Review by {r_id}: Code is clean, well-tested, adheres to standards."
                },
                "vote": "YES_APPROVE"
            }
            with open(reviews_dir / f"{r_id}.review.yml", "w", encoding="utf-8") as f:
                yaml.safe_dump(rev_manifest, f)

        # 6. Collect Consensus
        change2, vdata = orchestrator.collect_and_evaluate_consensus(task_id, configured_reviewers=len(reviewers))
        if change2 is None or vdata is None:
            raise RuntimeError("collect_and_evaluate_consensus failed to reach consensus")

        breakdown = vdata.get("vote_breakdown", {})
        approve_count = breakdown.get("approve", breakdown.get("yes_approve", 0))
        effective_count = breakdown.get("effective_votes", approve_count)

        steps_log.append({
            "step": "4. Consensus Evaluation",
            "decision": vdata.get("decision"),
            "state": change2.to_state.value,
            "votes_yes": approve_count,
            "effective_votes": effective_count,
            "confidence": vdata.get("decision_confidence", 1.0)
        })

        # 7. Return to main branch before merging, and execute merge
        subprocess.run(["git", "checkout", "main"], cwd=str(self.repo_dir), check=True, capture_output=True)

        merge_ok, merge_msg, change_merge = orchestrator.execute_merge(task_id)
        if not merge_ok or change_merge is None:
            raise RuntimeError(f"execute_merge failed: {merge_msg}")

        steps_log.append({
            "step": "5. Fast-Forward Merge",
            "state": change_merge.to_state.value,
            "message": merge_msg
        })

        # Check latest target branch commit
        res_main = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(self.repo_dir), capture_output=True, text=True, check=True)
        main_head = res_main.stdout.strip()
        merge_exact_match = (main_head == checkpoint_ref)

        # Check physical archive in .macao/archive/<checkpoint_ref>/r1/
        archive_dir = macao_dir / "archive" / checkpoint_ref / "r1"
        archived_files = [f.name for f in archive_dir.glob("*")] if archive_dir.exists() else []

        return {
            "task_id": task_id,
            "checkpoint_ref": checkpoint_ref,
            "main_head": main_head,
            "merge_exact_match": merge_exact_match,
            "final_state": change_merge.to_state.value,
            "decision": vdata.get("decision"),
            "steps": steps_log,
            "archived_files": archived_files,
            "archived_count": len(archived_files),
            "status": "PASS" if (change_merge.to_state == AgentState.DONE and merge_exact_match and len(archived_files) > 0) else "FAIL"
        }

    def cleanup(self) -> None:
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        if self.remote_dir and Path(self.remote_dir).exists():
            shutil.rmtree(self.remote_dir, ignore_errors=True)
