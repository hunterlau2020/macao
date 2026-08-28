"""Git integration utilities for workspace and worktree management (PRD §16.3)."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class GitManager:
    """Encapsulates Git operations for workspace, diffs, and isolated worktrees."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()

    def _run(self, *args: str) -> Tuple[int, str, str]:
        try:
            res = subprocess.run(
                ["git"] + list(args),
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=False
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except Exception as e:
            return 1, "", str(e)

    def commit_exists(self, ref: str) -> bool:
        code, _, _ = self._run("cat-file", "-e", f"{ref}^{{commit}}")
        return code == 0

    def resolve_ref(self, ref: str) -> Optional[str]:
        """Resolves any ref / branch / short SHA to full 40-char commit SHA."""
        code, out, _ = self._run("rev-parse", ref)
        if code == 0 and out:
            return out.strip()
        return None

    def get_head_commit(self) -> str:
        code, stdout, _ = self._run("rev-parse", "HEAD")
        return stdout if code == 0 else ""

    def get_merge_base(self, commit1: str, commit2: str) -> str:
        code, stdout, _ = self._run("merge-base", commit1, commit2)
        return stdout if code == 0 else ""

    def get_diff_summary(self, base_commit: str, head_commit: str) -> Tuple[int, int, int]:
        """Returns (files_changed, insertions, deletions)."""
        code, stdout, _ = self._run("diff", "--shortstat", f"{base_commit}..{head_commit}")
        if code != 0 or not stdout:
            return 0, 0, 0
        parts = stdout.split(",")
        files, ins, dels = 0, 0, 0
        for p in parts:
            p = p.strip()
            if "file" in p:
                files = int(p.split()[0])
            elif "insertion" in p:
                ins = int(p.split()[0])
            elif "deletion" in p:
                dels = int(p.split()[0])
        return files, ins, dels

    def get_changed_files(self, base_commit: str, head_commit: str) -> List[Dict[str, Any]]:
        """Returns list of changed files with path and status (Fail-closed on errors)."""
        code, stdout, _ = self._run("diff", "--name-status", f"{base_commit}..{head_commit}")
        if code != 0 or not stdout:
            return []
        files = []
        for line in stdout.split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                status_code = parts[0][0].upper()
                file_path = parts[1]
                status_map = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed"}
                files.append({
                    "path": file_path,
                    "status": status_map.get(status_code, "modified")
                })
        return files

    def create_isolated_worktree(self, reviewer_id: str, task_id: str, review_round: int, commit_sha: str) -> Path:
        """Create an isolated worktree directory for a reviewer session (PRD §16.3, Fail-closed)."""
        worktree_dir = self.repo_path / ".macao" / "worktrees" / reviewer_id / task_id / f"r{review_round}"
        worktree_dir.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing if any
        if worktree_dir.exists():
            self.remove_worktree(worktree_dir)

        # Check if repo is git repository
        code, _, _ = self._run("rev-parse", "--is-inside-work-tree")
        if code != 0:
            raise RuntimeError(f"Cannot create worktree: '{self.repo_path}' is not a valid git repository (Fail-closed)")

        if not self.commit_exists(commit_sha):
            raise RuntimeError(f"Cannot create worktree: commit '{commit_sha}' does not exist in repository")

        code, stdout, stderr = self._run("worktree", "add", "--detach", str(worktree_dir), commit_sha)
        if code != 0:
            raise RuntimeError(f"Failed to create git worktree for reviewer '{reviewer_id}': {stderr or stdout}")

        return worktree_dir

    def remove_worktree(self, worktree_path: Path) -> bool:
        """Prune and remove an isolated worktree directory."""
        code, _, _ = self._run("worktree", "remove", "--force", str(worktree_path))
        self._run("worktree", "prune")
        if worktree_path.exists():
            shutil.rmtree(worktree_path, ignore_errors=True)
        return True
