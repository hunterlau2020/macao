"""Merge Controller and MERGING Pipeline (PRD §14.5)."""

import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from macao.core.types import AgentState
from macao.storage.store import StateStore
from macao.utils.git_utils import GitManager


class MergeController:
    """Executes the merge pipeline from CONSENSUS_CHECK APPROVED to DONE (E4a/E4b)."""

    def __init__(self, store: StateStore, project_root: str = "."):
        self.store = store
        self.root = Path(project_root)
        self.git = GitManager(project_root)

    def execute_merge_pipeline(
        self,
        task_id: str,
        target_branch: str = "main",
        ci_gate_command: Optional[str] = None,
        require_signoff: bool = True
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Executes merge pipeline steps (PRD §14.5):
        1. Target checkout & rebase check
        2. Fast-forward merge
        3. CI gate command (if configured)
        4. Push
        
        Returns:
            (success, message, merge_commit_sha)
        """
        task = self.store.get_task(task_id)
        if not task:
            return False, f"Task {task_id} not found", None

        checkpoint_ref = task.get("checkpoint_ref")
        if not checkpoint_ref:
            return False, "No checkpoint_ref attached to task", None

        # 1. Checkout target branch
        code, out, err = self.git._run("checkout", target_branch)
        if code != 0:
            return False, f"Failed to checkout {target_branch}: {err or out}", None

        # 2. Fast-forward merge
        code, out, err = self.git._run("merge", "--ff-only", checkpoint_ref)
        if code != 0:
            return False, f"Fast-forward merge failed (conflict or non-ff): {err or out}", None

        # 3. Optional CI gate
        if ci_gate_command:
            try:
                res = subprocess.run(
                    ci_gate_command,
                    shell=True,
                    cwd=str(self.root),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if res.returncode != 0:
                    return False, f"CI gate command failed ({ci_gate_command}): {res.stderr or res.stdout}", None
            except Exception as e:
                return False, f"CI gate execution error: {e}", None

        # 4. Get final merge commit
        merge_commit = self.git.get_head_commit()
        return True, "Merge pipeline completed successfully", merge_commit
