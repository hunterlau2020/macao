"""Fast-forward Merge Controller with CI gates and Signoff verification (PRD §14.5)."""

import os
import shlex
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

from macao.storage.store import StateStore
from macao.utils.git_utils import GitManager


class MergeController:
    """Controls the MERGING pipeline: signoff gate -> target branch checkout -> fast-forward -> CI gate -> push."""

    def __init__(self, store: StateStore, project_root: str = "."):
        self.store = store
        self.root = Path(project_root).resolve()
        self.git = GitManager(str(self.root))

    def execute_merge_pipeline(
        self,
        task_id: str,
        target_branch: str = "main",
        ci_gate_command: Optional[str] = None,
        require_signoff: bool = True,
        remote_name: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Executes merge pipeline (PRD §14.5):
        1. Verifies human signoff if require_signoff is True
        2. Checks inside git work tree (Fail-closed)
        3. Checkouts target branch and captures pre_merge_head
        4. Performs git merge --ff-only <checkpoint_ref>
        5. Runs optional ci_gate_command (with atomic reset rollback on failure)
        6. Verifies exact 40-character SHA match: HEAD == checkpoint_ref
        7. Pushes to remote and verifies remote SHA if remote_name is configured (Fail-closed)
        """
        task = self.store.get_task(task_id)
        if not task:
            return False, f"Task {task_id} not found", None

        checkpoint_ref = task.get("checkpoint_ref")
        if not checkpoint_ref:
            return False, "No checkpoint_ref attached to task", None

        # Check signoff requirement (Fail-closed)
        if require_signoff:
            audits = self.store.list_audit_events(task_id, limit=50)
            signoffs = [a for a in audits if a.get("type") in ("HUMAN_MERGE_APPROVED", "MERGE_SIGNOFF_APPROVED")]
            if not signoffs:
                return False, "Human signoff required before merge (macao merge approve)", None

        # Check if in a valid git repository (Fail-closed)
        code, _, _ = self.git._run("rev-parse", "--is-inside-work-tree")
        if code != 0:
            return False, "Directory is not a valid git repository (Fail-closed)", None

        # 1. Checkout target branch and capture pre-merge HEAD
        code, out, err = self.git._run("checkout", target_branch)
        if code != 0:
            return False, f"Failed to checkout {target_branch}: {err or out}", None

        pre_merge_head = self.git.get_head_commit()

        # 2. Fast-forward merge
        code, out, err = self.git._run("merge", "--ff-only", checkpoint_ref)
        if code != 0:
            return False, f"Fast-forward merge failed (conflict or non-ff): {err or out}", None

        # 3. Optional CI gate (with atomic rollback on failure to prevent target branch contamination)
        if ci_gate_command:
            try:
                cmd_args = shlex.split(ci_gate_command)
                res = subprocess.run(
                    cmd_args,
                    cwd=str(self.root),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if res.returncode != 0:
                    # Rollback target branch to pre-merge commit
                    if pre_merge_head:
                        self.git._run("reset", "--hard", pre_merge_head)
                    return False, f"CI gate command failed ({ci_gate_command}): {res.stderr or res.stdout}", None
            except Exception as e:
                if pre_merge_head:
                    self.git._run("reset", "--hard", pre_merge_head)
                return False, f"CI gate execution error: {e}", None

        # 4. Hard verification: head commit == full checkpoint_ref (PRD §14.5 P0-1)
        head_commit = self.git.get_head_commit()
        full_checkpoint_ref = self.git.resolve_ref(checkpoint_ref) or checkpoint_ref
        if head_commit != full_checkpoint_ref:
            if pre_merge_head:
                self.git._run("reset", "--hard", pre_merge_head)
            return False, f"Merge commit mismatch: HEAD ({head_commit}) != checkpoint ({full_checkpoint_ref})", None

        # 5. Optional remote push with remote existence check and post-push SHA verification (Fail-closed)
        if remote_name:
            code_rem, out_rem, _ = self.git._run("remote")
            if code_rem != 0 or remote_name not in out_rem.split():
                if pre_merge_head:
                    self.git._run("reset", "--hard", pre_merge_head)
                return False, f"Configured remote '{remote_name}' not found in repository remotes (Fail-closed)", None

            code, out, err = self.git._run("push", remote_name, target_branch)
            if code != 0:
                if pre_merge_head:
                    self.git._run("reset", "--hard", pre_merge_head)
                return False, f"Git push to {remote_name}/{target_branch} failed: {err or out}", None

            # Verify remote SHA equals checkpoint_ref
            code_ls, out_ls, _ = self.git._run("ls-remote", remote_name, f"refs/heads/{target_branch}")
            if code_ls == 0 and out_ls.strip():
                remote_sha = out_ls.strip().split()[0]
                if remote_sha != full_checkpoint_ref:
                    if pre_merge_head:
                        self.git._run("reset", "--hard", pre_merge_head)
                    return False, f"Remote SHA mismatch: remote {remote_sha} != local {full_checkpoint_ref}", None

        return True, "Merge pipeline completed successfully", head_commit
