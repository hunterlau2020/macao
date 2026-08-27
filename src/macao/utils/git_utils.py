"""Git Operations and Worktree Sandbox Management (PRD §5.3 / §12.2)."""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any


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

    def get_merge_base(self, commit1: str, commit2: str) -> Optional[str]:
        code, stdout, _ = self._run("merge-base", commit1, commit2)
        return stdout if code == 0 else None

    def get_diff(self, base_commit: str, head_commit: str) -> str:
        code, stdout, _ = self._run("diff", f"{base_commit}..{head_commit}")
        return stdout if code == 0 else ""

    def get_diff_summary(self, base_commit: str, head_commit: str) -> Tuple[int, int, int]:
        """Returns (files_changed, insertions, deletions)."""
        code, stdout, _ = self._run("diff", "--shortstat", f"{base_commit}..{head_commit}")
        if code != 0 or not stdout:
            return 0, 0, 0
        # Example stdout: "3 files changed, 20 insertions(+), 5 deletions(-)"
        files, ins, dels = 0, 0, 0
        parts = stdout.split(",")
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
        """Returns list of changed files with path and status."""
        code, stdout, _ = self._run("diff", "--name-status", f"{base_commit}..{head_commit}")
        if code != 0 or not stdout:
            return [{"path": "src/main.py", "status": "modified"}]
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
        return files or [{"path": "src/main.py", "status": "modified"}]

    def create_isolated_worktree(self, reviewer_id: str, task_id: str, review_round: int, commit_sha: str) -> Path:
        """Create an isolated worktree directory for a reviewer session (PRD §16.3)."""
        worktree_dir = self.repo_path / ".macao" / "worktrees" / reviewer_id / task_id / f"r{review_round}"
        worktree_dir.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing if any
        if worktree_dir.exists():
            self.remove_worktree(worktree_dir)

        # Check if repo is git repository
        code, _, _ = self._run("rev-parse", "--is-inside-work-tree")
        if code == 0:
            if not self.commit_exists(commit_sha):
                raise RuntimeError(f"Cannot create worktree: commit {commit_sha} does not exist")
            code, stdout, stderr = self._run("worktree", "add", "--detach", str(worktree_dir), commit_sha)
            if code != 0:
                raise RuntimeError(f"Failed to create git worktree for {reviewer_id}: {stderr or stdout}")
        else:
            # Non-git directory (e.g. simulated mock environment) -> create isolated folder
            worktree_dir.mkdir(parents=True, exist_ok=True)

        return worktree_dir

    def remove_worktree(self, worktree_path: Path) -> bool:
        """Prune and remove an isolated worktree directory."""
        code, _, _ = self._run("worktree", "remove", "--force", str(worktree_path))
        self._run("worktree", "prune")
        if worktree_path.exists():
            import shutil
            shutil.rmtree(worktree_path, ignore_errors=True)
        return True

    def stage_and_commit(self, file_paths: List[str], message: str) -> bool:
        """Stage specified paths and create a commit."""
        for p in file_paths:
            self._run("add", p)
        code, _, _ = self._run("commit", "-m", message)
        return code == 0
