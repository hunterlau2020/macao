"""Git Operations and Worktree Sandbox Management (PRD §5.3 / §12.2)."""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List


class GitManager:
    """Encapsulates Git commands and Reviewer Worktree isolation."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()

    def _run(self, *args: str, cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        work_dir = cwd or self.repo_path
        res = subprocess.run(
            ["git", *args],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()

    def get_head_commit(self) -> Optional[str]:
        code, stdout, _ = self._run("rev-parse", "HEAD")
        return stdout if code == 0 else None

    def commit_exists(self, commit_sha: str) -> bool:
        code, _, _ = self._run("cat-file", "-e", f"{commit_sha}^{{commit}}")
        return code == 0

    def get_diff(self, base_commit: str, head_commit: str) -> str:
        code, stdout, _ = self._run("diff", f"{base_commit}..{head_commit}")
        return stdout if code == 0 else ""

    def get_diff_summary(self, base_commit: str, head_commit: str) -> str:
        code, stdout, _ = self._run("diff", "--shortstat", f"{base_commit}..{head_commit}")
        return stdout if code == 0 else ""

    def create_isolated_worktree(self, reviewer_id: str, task_id: str, review_round: int, commit_sha: str) -> Path:
        """Create an isolated worktree directory for a reviewer session."""
        worktree_dir = self.repo_path / ".macao" / "worktrees" / reviewer_id / task_id / f"r{review_round}"
        worktree_dir.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing if any
        if worktree_dir.exists():
            self.remove_worktree(worktree_dir)

        code, stdout, stderr = self._run("worktree", "add", "--detach", str(worktree_dir), commit_sha)
        if code != 0:
            # Fallback or raise error
            raise RuntimeError(f"Failed to create git worktree: {stderr or stdout}")
        return worktree_dir

    def remove_worktree(self, worktree_path: Path) -> bool:
        """Prune and remove an isolated worktree directory."""
        code, _, _ = self._run("worktree", "remove", "--force", str(worktree_path))
        self._run("worktree", "prune")
        return code == 0

    def stage_and_commit(self, file_paths: List[str], message: str) -> bool:
        """Stage specified paths and create a commit."""
        for p in file_paths:
            self._run("add", p)
        code, _, _ = self._run("commit", "-m", message)
        return code == 0
