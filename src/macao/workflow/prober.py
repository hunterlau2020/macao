"""MACAO Dynamic Team and Environment Prober (PRD §12 & §14).

Performs pre-dispatch dynamic probing of configured Executor, Reviewers, Git repository,
worktrees, and active task progress to ensure the team is healthy and clearly identifies
task dispatch targets before execution.
Guaranteed strictly read-only and zero mutation to state.db or git.
"""

import os
import shutil
import sqlite3
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from macao.core.config import ConfigManager
from macao.core.types import PreflightCheckResult
from macao.utils.git_utils import GitManager
from datetime import datetime
from macao.adapter.claude import ClaudeCodeAdapter
from macao.adapter.codex import CodexAdapter
from macao.adapter.opencode import OpenCodeAdapter
from macao.adapter.antigravity import AntigravityAdapter
from macao.adapter.cursor import CursorAgentAdapter
from macao.adapter.kimi import KimiAdapter
from macao.adapter.mock import MockAgentAdapter
from macao.adapter.session_locator import SessionLocator

ADAPTER_MAP = {
    "claude": ClaudeCodeAdapter,
    "claude-code": ClaudeCodeAdapter,
    "codex": CodexAdapter,
    "opencode": OpenCodeAdapter,
    "agy": AntigravityAdapter,
    "antigravity": AntigravityAdapter,
    "agent": CursorAgentAdapter,
    "cursor": CursorAgentAdapter,
    "kimi": KimiAdapter,
    "mock-cli": MockAgentAdapter,
    "mock-agent": MockAgentAdapter,
}


class TeamProber:
    """Probes dynamic readiness of Executor, Reviewers, Git, worktrees, and active tasks before dispatch."""

    def __init__(self, project_root: str = ".", dry_run: bool = False):
        self.project_root = Path(project_root).resolve()
        self.cfg_file = self.project_root / "macao.yaml"
        self.git = GitManager(str(self.project_root))
        self.dry_run = dry_run

    def _get_adapter(self, cli_name: str, agent_id: str, config: Optional[Dict[str, Any]] = None):
        cls = ADAPTER_MAP.get(cli_name.lower())
        if not cls:
            for k, v in ADAPTER_MAP.items():
                if k in agent_id.lower() or k in cli_name.lower():
                    cls = v
                    break
        if cls:
            try:
                return cls(agent_id=agent_id, config=config)
            except Exception:
                pass
        return None

    def _query_active_task_readonly(self) -> Tuple[Optional[Dict[str, Any]], Optional[str], bool]:
        """
        Reads active task from .macao/state.db strictly in read-only mode without mutating the file
        or creating it if it doesn't exist.
        Returns (active_task_dict, error_string, db_file_exists).
        """
        db_path = self.project_root / ".macao" / "state.db"
        if not db_path.exists():
            return None, None, False

        try:
            conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True, timeout=5.0)
            conn.row_factory = sqlite3.Row
            try:
                cur = conn.execute(
                    "SELECT * FROM tasks WHERE state NOT IN (?, ?) ORDER BY created_at DESC LIMIT 1",
                    ("DONE", "CANCELLED")
                )
                row = cur.fetchone()
                return (dict(row) if row else None), None, True
            finally:
                conn.close()
        except Exception as e:
            return None, str(e), True

    def _query_task_artifacts_readonly(self, task_id: str) -> List[Dict[str, Any]]:
        """Reads task artifacts strictly in read-only mode."""
        db_path = self.project_root / ".macao" / "state.db"
        if not db_path.exists():
            return []

        try:
            conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True, timeout=5.0)
            conn.row_factory = sqlite3.Row
            try:
                cur = conn.execute(
                    "SELECT * FROM artifacts WHERE task_id = ? ORDER BY artifact_id ASC",
                    (task_id,)
                )
                return [dict(r) for r in cur.fetchall()]
            finally:
                conn.close()
        except Exception:
            return []

    def _inspect_worktree(self, worktree_path: Path) -> Tuple[bool, Optional[str]]:
        """Returns (exists_on_disk, commit_head)."""
        if not worktree_path.exists():
            return False, None
        try:
            code, stdout, _ = self.git._run("-C", str(worktree_path), "rev-parse", "--short", "HEAD")
            if code == 0 and stdout.strip():
                return True, stdout.strip()
        except Exception:
            pass
        return True, "detected"

    def _inspect_git_worktrees(self) -> List[Dict[str, Any]]:
        """
        Inspects real Git worktrees registered via 'git worktree list --porcelain'.
        Returns list of dicts: [{"path": str, "commit": str, "branch": str, "is_primary": bool}].
        """
        worktrees = []
        try:
            code, out, _ = self.git._run("worktree", "list", "--porcelain")
            if code == 0 and out.strip():
                current_entry: Dict[str, Any] = {}
                for line in out.splitlines():
                    line = line.strip()
                    if not line:
                        if current_entry.get("path"):
                            worktrees.append(current_entry)
                        current_entry = {}
                        continue
                    if line.startswith("worktree "):
                        current_entry["path"] = line[9:].strip()
                    elif line.startswith("HEAD "):
                        current_entry["commit"] = line[5:].strip()[:8]
                    elif line.startswith("branch "):
                        current_entry["branch"] = line[7:].replace("refs/heads/", "").strip()
                if current_entry.get("path"):
                    worktrees.append(current_entry)
        except Exception:
            pass

        if not worktrees:
            head = self.git.get_head_commit()
            branch = self.git.get_current_branch()
            worktrees.append({
                "path": str(self.project_root),
                "commit": head[:8] if head else "none",
                "branch": branch,
                "is_primary": True
            })
        else:
            for idx, wt in enumerate(worktrees):
                wt["is_primary"] = (idx == 0)

        return worktrees

    def _inspect_physical_reviews(self) -> Dict[str, Any]:
        """
        Inspects physical review documents in docs/reviews/ to discover
        latest review request, baseline commits, submitted reviewer results, and pending status.
        """
        reviews_dir = self.project_root / "docs" / "reviews"
        info = {
            "has_reviews_dir": reviews_dir.exists(),
            "latest_request_file": None,
            "latest_request_title": None,
            "latest_request_baseline": None,
            "has_pending_request": False,
            "matching_results": [],
            "recent_functional_commit": None,
            "recent_functional_msg": None
        }

        # 1. Inspect recent git commits for functional context
        try:
            code, out, _ = self.git._run("log", "-n", "5", "--format=%h|%s")
            if code == 0 and out.strip():
                for line in out.splitlines():
                    if "|" in line:
                        sha, msg = line.split("|", 1)
                        if not msg.startswith("docs(review)") and not info["recent_functional_commit"]:
                            info["recent_functional_commit"] = sha.strip()
                            info["recent_functional_msg"] = msg.strip()
                if not info["recent_functional_commit"] and out.splitlines():
                    sha, msg = out.splitlines()[0].split("|", 1)
                    info["recent_functional_commit"] = sha.strip()
                    info["recent_functional_msg"] = msg.strip()
        except Exception:
            pass

        # 2. Inspect review request documents
        if reviews_dir.exists():
            req_files = sorted(reviews_dir.glob("*-review-request-*.md"))
            res_files = sorted(reviews_dir.glob("*-review-result-*.md"))

            if req_files:
                latest_req = req_files[-1]
                try:
                    info["latest_request_file"] = str(latest_req.relative_to(self.project_root))
                except Exception:
                    info["latest_request_file"] = str(latest_req)

                try:
                    content = latest_req.read_text(encoding="utf-8", errors="replace")
                    lines = content.splitlines()
                    info["latest_request_title"] = lines[0].lstrip("#").strip() if lines else latest_req.name
                except Exception:
                    info["latest_request_title"] = latest_req.name

                import re
                match = re.search(r"([0-9a-f]{7,40})", latest_req.stem)
                baseline = match.group(1) if match else None
                if not baseline:
                    tokens = latest_req.stem.split("-")
                    if tokens and len(tokens[-1]) >= 4:
                        baseline = tokens[-1]
                info["latest_request_baseline"] = baseline

                if baseline:
                    matching = []
                    for rf in res_files:
                        if baseline in rf.name:
                            try:
                                matching.append(str(rf.relative_to(self.project_root)))
                            except Exception:
                                matching.append(str(rf))
                    info["matching_results"] = matching
                    info["has_pending_request"] = (len(matching) == 0)
                else:
                    info["has_pending_request"] = True

        return info

    def _write_probe_log(self, probe_result: Dict[str, Any]) -> Optional[str]:
        """Writes comprehensive probe audit log to .macao/logs/probe/probe_<timestamp>.log."""
        try:
            log_dir = self.project_root / ".macao" / "logs" / "probe"
            log_dir.mkdir(parents=True, exist_ok=True)
            ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"probe_{ts_str}.log"

            exec_data = probe_result.get("executor", {})
            exec_sess = exec_data.get("session", {}) or {}
            exec_prog = exec_data.get("progress_triplet", {}) or {}

            lines = [
                "=== MACAO Runtime State Probe Audit Log ===",
                f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Project: {probe_result.get('project_name')} ({self.project_root})",
                f"Dry-Run Mode: {probe_result.get('dry_run')}",
                "",
                "--- 1. Executor Runtime Inspection ---",
                f"ID: {exec_data.get('id')}",
                f"CLI: {exec_data.get('cli')} (Version: {exec_data.get('version')})",
                f"Active Session: {exec_sess.get('session_id', 'None discovered')}",
                f"Session Last Active: {exec_sess.get('last_active', 'N/A')}",
                f"Worktree: {exec_data.get('worktree', {}).get('path')} ({exec_data.get('worktree', {}).get('type')})",
                f"Last Completed: {exec_prog.get('last_completed', 'N/A')}",
                f"Current Active: {exec_prog.get('current_task', 'N/A')}",
                f"Next Planned: {exec_prog.get('next_planned', 'N/A')}",
                "",
                "--- 2. Reviewers Runtime Inspection ---"
            ]

            for r in probe_result.get("reviewers", []):
                r_sess = r.get("session", {}) or {}
                r_rev = r.get("review", {}) or {}
                lines.extend([
                    f"Reviewer: {r.get('id')} ({r.get('cli')}, weight: {r.get('weight')})",
                    f"  Status: {r.get('status')}",
                    f"  Active Session: {r_sess.get('session_id', 'None discovered')}",
                    f"  Worktree: {r.get('worktree', {}).get('display', 'In-repo')}",
                    f"  Review Progress: {r_rev.get('status_display', 'IDLE')}",
                    f"  Details: {r.get('details')}"
                ])

            lines.extend([
                "",
                "--- 3. Git & Physical Review Artifacts ---",
                f"Git Branch: {probe_result.get('git', {}).get('branch')} @ {probe_result.get('git', {}).get('commit')}",
                f"Uncommitted Changes: {probe_result.get('git', {}).get('modified_files_count', 0)} files",
                f"Physical Review Pending: {probe_result.get('physical_reviews', {}).get('has_pending_request')}",
                f"Latest Review Request: {probe_result.get('physical_reviews', {}).get('latest_request_file')}",
                f"Quorum Readiness: {probe_result.get('quorum', {}).get('ready_count')}/{probe_result.get('quorum', {}).get('total_configured')} Ready (Can Dispatch: {probe_result.get('can_dispatch')})",
                "==========================================="
            ])

            log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            try:
                return str(log_file.relative_to(self.project_root))
            except Exception:
                return str(log_file)
        except Exception:
            return None

    def _inspect_reviewer_manifest(
        self,
        reviewer_id: str,
        active_task: Optional[Dict[str, Any]],
        artifacts: List[Dict[str, Any]],
        worktree_path: Path
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Inspects whether a reviewer has submitted a review manifest.
        Checks:
        1. Root .macao/.reviews/<reviewer_id>.review.yml
        2. Worktree .macao/.reviews/<reviewer_id>.review.yml
        3. Artifacts table in state.db
        Returns (manifest_found, vote, opinion_status, summary, manifest_file_path).
        """
        root_manifest = self.project_root / ".macao" / ".reviews" / f"{reviewer_id}.review.yml"
        candidates = [root_manifest]
        if worktree_path.exists():
            candidates.append(worktree_path / ".macao" / ".reviews" / f"{reviewer_id}.review.yml")

        for mf in candidates:
            if mf.exists():
                try:
                    data = yaml.safe_load(mf.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        opinion = data.get("opinion", {})
                        vote = data.get("vote") or (opinion.get("vote") if isinstance(opinion, dict) else None)
                        st = opinion.get("status") if isinstance(opinion, dict) else None
                        summary = opinion.get("summary") if isinstance(opinion, dict) else None
                        return True, vote, st, summary, str(mf)
                except Exception:
                    pass

        if active_task:
            task_id = active_task["task_id"]
            review_round = active_task.get("review_round", 1)
            for art in artifacts:
                if (
                    art.get("kind") == "review_manifest"
                    and art.get("reviewer_id") == reviewer_id
                    and art.get("review_round") == review_round
                ):
                    art_path = Path(art.get("path", ""))
                    if not art_path.is_absolute():
                        art_path = self.project_root / art_path
                    if art_path.exists():
                        try:
                            data = yaml.safe_load(art_path.read_text(encoding="utf-8"))
                            if isinstance(data, dict):
                                opinion = data.get("opinion", {})
                                vote = data.get("vote") or (opinion.get("vote") if isinstance(opinion, dict) else None)
                                st = opinion.get("status") if isinstance(opinion, dict) else None
                                summary = opinion.get("summary") if isinstance(opinion, dict) else None
                                return True, vote, st, summary, str(art_path)
                        except Exception:
                            pass
                    return True, "RECORDED", "COMPLETED", "Recorded in artifacts", str(art_path)

        return False, None, None, None, None

    def _has_recent_reviewer_session(self, reviewer_id: str, max_age_seconds: float = 600.0) -> bool:
        """Checks if there is an active/recent reviewer log file in .macao/logs/reviewers/."""
        log_dir = self.project_root / ".macao" / "logs" / "reviewers"
        if not log_dir.exists():
            return False
        import time
        now = time.time()
        for log_file in log_dir.glob(f"*{reviewer_id}*.log"):
            try:
                mtime = log_file.stat().st_mtime
                if now - mtime <= max_age_seconds:
                    return True
            except Exception:
                pass
        return False

    def _has_recent_executor_session(self, executor_id: str, max_age_seconds: float = 600.0) -> bool:
        """Checks if there is an active/recent executor log file in .macao/logs/executors/."""
        log_dir = self.project_root / ".macao" / "logs" / "executors"
        if not log_dir.exists():
            return False
        import time
        now = time.time()
        for log_file in log_dir.glob(f"*{executor_id}*.log"):
            try:
                mtime = log_file.stat().st_mtime
                if now - mtime <= max_age_seconds:
                    return True
            except Exception:
                pass
        return False

    def probe(self) -> Dict[str, Any]:
        """Runs comprehensive dynamic probe across team, worktrees, and environment."""
        if not self.cfg_file.exists():
            return {
                "valid_config": False,
                "error": "macao.yaml not found in project root. Run 'macao init' to initialize.",
                "can_dispatch": False,
                "blocking_reasons": ["macao.yaml not found"]
            }

        try:
            cfg = ConfigManager.load_config(str(self.cfg_file))
        except Exception as e:
            return {
                "valid_config": False,
                "error": f"Failed to parse macao.yaml: {e}",
                "can_dispatch": False,
                "blocking_reasons": [f"Invalid macao.yaml: {e}"]
            }

        team = cfg.get("team", {})
        policy = cfg.get("policy", {})

        # 1. Read-only StateStore Probe (Pure read-only, never creates state.db)
        active_task, state_store_error, state_db_exists = self._query_active_task_readonly()
        artifacts = self._query_task_artifacts_readonly(active_task["task_id"]) if active_task else []

        # 2. Git Status
        git_info = {
            "branch": "unknown",
            "commit": "unknown",
            "is_clean": True,
            "modified_files_count": 0,
            "error": None
        }
        try:
            git_info["branch"] = self.git.get_current_branch()
            head = self.git.get_head_commit()
            git_info["commit"] = head[:8] if head else "none"
            git_info["is_clean"] = self.git.is_clean()
            code, out, _ = self.git._run("status", "--porcelain")
            if code == 0:
                lines = [l for l in out.splitlines() if l.strip()]
                git_info["modified_files_count"] = len(lines)
        except Exception as e:
            git_info["error"] = str(e)

        # 3. Discover Registered Git Worktrees and Physical Review Facts
        registered_worktrees = self._inspect_git_worktrees()
        review_facts = self._inspect_physical_reviews()

        # 4. Probe Executor
        raw_exec = team.get("executor", {})
        exec_id = raw_exec.get("id", "dev-executor")
        exec_cli = raw_exec.get("cli", "")
        exec_model = raw_exec.get("model")

        # Session discovery for executor
        exec_session = SessionLocator.find_session(exec_cli, self.project_root)

        exec_probe = {
            "id": exec_id,
            "cli": exec_cli,
            "model": exec_model,
            "installed": False,
            "version": "unknown",
            "status": "MISSING",
            "details": "",
            "error": None,
            "session": exec_session,
            "worktree": {
                "path": str(self.project_root),
                "type": "primary_repository" if len(registered_worktrees) <= 1 else "in_repo",
                "branch": git_info["branch"],
                "commit": git_info["commit"],
                "is_clean": git_info["is_clean"],
                "modified_files_count": git_info["modified_files_count"],
            },
            "progress": "IDLE",
            "progress_desc": "No active task assigned; waiting for task dispatch",
            "progress_triplet": {
                "last_completed": None,
                "current_task": None,
                "next_planned": None
            },
            "session_active": bool(exec_session) or self._has_recent_executor_session(exec_id)
        }

        adp = self._get_adapter(exec_cli, exec_id, raw_exec)
        if adp:
            try:
                res = adp.preflight()
                exec_probe["installed"] = res.installed
                exec_probe["version"] = res.version or "detected"
                exec_probe["status"] = "READY" if res.installed else "MISSING"
                exec_probe["details"] = res.details or ""
                exec_probe["error"] = res.error
            except Exception as e:
                exec_probe["error"] = str(e)
                exec_probe["status"] = "ERROR"
        else:
            path = shutil.which(exec_cli)
            if path:
                exec_probe["installed"] = True
                exec_probe["status"] = "READY"
                exec_probe["details"] = f"Found executable in PATH: {path}"
            else:
                exec_probe["details"] = f"Executable '{exec_cli}' not found in PATH"

        # Check executor coding / checkpoint progress
        dev_yml_path = self.project_root / ".macao" / ".dev.yml"
        dev_manifest_found = False
        dev_manifest_ref = None
        if dev_yml_path.exists():
            try:
                dev_data = yaml.safe_load(dev_yml_path.read_text(encoding="utf-8"))
                if isinstance(dev_data, dict):
                    dev_manifest_found = True
                    dev_manifest_ref = dev_data.get("checkpoint_ref")
            except Exception:
                pass

        # Synthesize progress triplet (三问对账)
        last_completed = (
            f"Commit {review_facts['recent_functional_commit']}: {review_facts['recent_functional_msg']}"
            if review_facts.get("recent_functional_commit")
            else f"Commit {git_info['commit']} on branch {git_info['branch']}"
        )

        if active_task:
            task_state = active_task.get("state", "IDLE")
            source_br = active_task.get("source_branch", "dev")
            task_title = active_task.get("title", active_task.get("task_id", ""))

            if task_state in ("IDLE", "CODING", "REWORK"):
                if dev_manifest_found:
                    exec_probe["progress"] = "CHECKPOINT_SUBMITTED"
                    ref_disp = dev_manifest_ref[:8] if dev_manifest_ref else "HEAD"
                    current_task = f"Checkpoint submitted at {ref_disp}. Ready for review dispatch."
                    next_planned = "Dispatch review to reviewers"
                else:
                    exec_probe["progress"] = "CODING_IN_PROGRESS"
                    clean_note = "clean" if git_info["is_clean"] else f"{git_info['modified_files_count']} uncommitted changes"
                    current_task = f"Actively implementing '{task_title}' on branch '{source_br}' ({clean_note})"
                    next_planned = "Complete implementation, run tests, and submit checkpoint"
            elif task_state in ("WAITING_REVIEW", "IN_REVIEW"):
                exec_probe["progress"] = "WAITING_REVIEW_VERDICT"
                ref_disp = (active_task.get("checkpoint_ref") or dev_manifest_ref or "HEAD")[:8]
                current_task = f"Code submitted at {ref_disp}. Paused waiting for reviewer consensus."
                next_planned = "Await reviewer verdicts to merge or rework"
            elif task_state == "CONSENSUS_REACHED":
                exec_probe["progress"] = "REVIEW_CONCLUDED"
                current_task = f"Review cycle completed for '{task_title}'. Awaiting merge approval."
                next_planned = "Execute merge or address disposition"
            elif task_state == "MERGING":
                exec_probe["progress"] = "READY_TO_MERGE"
                current_task = f"Review approved for '{task_title}'. Ready for merge signoff."
                next_planned = "Execute 'macao merge approve' to merge into default branch"
            elif task_state in ("DONE", "CANCELLED"):
                exec_probe["progress"] = "IDLE"
                current_task = f"Previous task '{active_task['task_id']}' is {task_state}."
                next_planned = "Await new task creation"
            else:
                exec_probe["progress"] = task_state
                current_task = f"Task currently in state {task_state}."
                next_planned = "Advance task state"
        else:
            if not git_info["is_clean"]:
                mod_count = git_info.get("modified_files_count", 0)
                exec_probe["progress"] = "ACTIVE_DEV (UNTRACKED)"
                current_task = f"Working tree has {mod_count} uncommitted file(s) in active development"
                next_planned = "Run tests, commit changes, or run 'macao task create' to adopt into MACAO"
            elif review_facts.get("has_pending_request"):
                req_title = review_facts.get("latest_request_title") or "Review Request"
                req_base = review_facts.get("latest_request_baseline") or "HEAD"
                exec_probe["progress"] = "REVIEW_PENDING"
                current_task = f"Review requested for commit {req_base[:8]}: {req_title}"
                next_planned = "Await reviewer evaluations and verdicts before next commit"
            else:
                exec_probe["progress"] = "IDLE"
                current_task = "No active task assigned; workspace clean"
                next_planned = "Create and dispatch new development task"

        exec_probe["progress_desc"] = current_task
        exec_probe["progress_triplet"] = {
            "last_completed": last_completed,
            "current_task": current_task,
            "next_planned": next_planned
        }

        # 5. Probe Reviewers
        reviewers_cfg = team.get("reviewers", [])
        reviewers_probe = []
        ready_reviewers_count = 0
        total_effective_weight = 0.0

        for r in reviewers_cfg:
            r_id = r.get("id", "reviewer")
            r_cli = r.get("cli", "")
            r_weight = float(r.get("vote_weight", r.get("weight", 1.0)))
            r_model = r.get("model")

            # Session discovery for reviewer
            r_session = SessionLocator.find_session(r_cli, self.project_root)

            # Reviewer worktree determination
            matching_wt = None
            for wt in registered_worktrees:
                if not wt.get("is_primary") and (r_id in wt.get("path", "") or r_cli in wt.get("path", "")):
                    matching_wt = wt
                    break

            if active_task:
                r_wt_path = self.project_root / ".macao" / "worktrees" / r_id / active_task["task_id"] / f"r{active_task.get('review_round', 1)}"
                r_wt_exists, r_wt_commit = self._inspect_worktree(r_wt_path)
                try:
                    r_wt_rel = str(r_wt_path.relative_to(self.project_root))
                except Exception:
                    r_wt_rel = str(r_wt_path)
                r_wt_status = "ACTIVE" if r_wt_exists else "NOT_SPAWNED"
                r_wt_display = f"{r_wt_rel} (ACTIVE @ {r_wt_commit})" if r_wt_exists else f"{r_wt_rel} (NOT_SPAWNED)"
                r_wt_type = "isolated_worktree"
            elif matching_wt:
                r_wt_path = Path(matching_wt["path"])
                r_wt_exists = True
                r_wt_commit = matching_wt.get("commit", "HEAD")
                r_wt_rel = str(r_wt_path)
                r_wt_status = "ACTIVE"
                r_wt_display = f"{r_wt_rel} (ACTIVE @ {r_wt_commit})"
                r_wt_type = "isolated_worktree"
            else:
                r_wt_path = self.project_root
                r_wt_exists = True
                r_wt_commit = git_info["commit"]
                r_wt_rel = "."
                r_wt_status = "IN_REPO"
                r_wt_display = "In-repo (Shared Workspace / Direct Review)"
                r_wt_type = "in_repo"

            # Check review manifest and progress
            manifest_found, vote, op_status, summary, mf_path = self._inspect_reviewer_manifest(
                r_id, active_task, artifacts, r_wt_path
            )

            # If no state.db manifest, check physical review results in docs/reviews/
            if not manifest_found and review_facts.get("latest_request_baseline"):
                base_sha = review_facts["latest_request_baseline"]
                reviews_dir = self.project_root / "docs" / "reviews"
                if reviews_dir.exists():
                    for res_file in reviews_dir.glob(f"*{base_sha}*.md"):
                        fname = res_file.name.lower()
                        if r_id.lower() in fname or r_cli.lower() in fname:
                            manifest_found = True
                            vote = "SUBMITTED"
                            summary = f"Physical review submitted: {res_file.name}"
                            try:
                                mf_path = str(res_file.relative_to(self.project_root))
                            except Exception:
                                mf_path = str(res_file)
                            break

            r_progress = "IDLE"
            r_status_display = "IDLE"
            r_details = "Standby (Awaiting task dispatch)"

            if manifest_found and vote:
                r_progress = "COMPLETED"
                r_status_display = f"COMPLETED ({vote})"
                r_details = f"Vote: {vote}" + (f" - {summary[:50]}" if summary else "")
            elif active_task:
                t_state = active_task.get("state", "IDLE")
                if t_state in ("WAITING_REVIEW", "IN_REVIEW"):
                    if r_wt_exists and r_wt_status == "ACTIVE":
                        has_recent = self._has_recent_reviewer_session(r_id)
                        if has_recent:
                            r_progress = "IN_PROGRESS"
                            r_status_display = "IN_PROGRESS (Reviewing...)"
                            r_details = "Active review CLI session running in isolated worktree"
                        else:
                            r_progress = "IN_PROGRESS"
                            r_status_display = "IN_PROGRESS"
                            r_details = "Worktree allocated; waiting for review completion"
                    else:
                        r_progress = "PENDING"
                        r_status_display = "PENDING (Queued)"
                        r_details = "Review dispatched, worktree pending allocation"
                elif t_state in ("IDLE", "CODING", "REWORK"):
                    r_progress = "WAITING_DEV"
                    r_status_display = "WAITING_DEV"
                    r_details = "Waiting for executor development checkpoint"
                elif t_state in ("CONSENSUS_REACHED", "MERGING", "DONE"):
                    r_progress = "IDLE"
                    r_status_display = "IDLE"
                    r_details = "Review round concluded"
                else:
                    r_progress = "IDLE"
                    r_status_display = "IDLE"
                    r_details = f"Task in state {t_state}"
            elif review_facts.get("has_pending_request"):
                base_disp = (review_facts.get("latest_request_baseline") or "HEAD")[:8]
                r_progress = "AWAITING_REVIEW"
                r_status_display = f"AWAITING_REVIEW (@ {base_disp})"
                r_details = f"Review requested for commit {base_disp}; ready to review"

            r_info = {
                "id": r_id,
                "cli": r_cli,
                "weight": r_weight,
                "model": r_model,
                "installed": False,
                "version": "unknown",
                "status": "MISSING",
                "details": r_details,
                "error": None,
                "session": r_session,
                "worktree": {
                    "expected_path": str(r_wt_path),
                    "relative_path": r_wt_rel,
                    "exists": r_wt_exists,
                    "status": r_wt_status,
                    "commit": r_wt_commit,
                    "display": r_wt_display,
                    "type": r_wt_type
                },
                "review": {
                    "progress": r_progress,
                    "status_display": r_status_display,
                    "vote": vote,
                    "opinion_status": op_status,
                    "manifest_path": mf_path,
                    "summary": summary,
                }
            }

            r_adp = self._get_adapter(r_cli, r_id, r)
            if r_adp:
                try:
                    res = r_adp.preflight()
                    r_info["installed"] = res.installed
                    r_info["version"] = res.version or "detected"
                    r_info["status"] = "READY" if res.installed else "MISSING"
                    r_info["error"] = res.error
                except Exception as e:
                    r_info["error"] = str(e)
                    r_info["status"] = "ERROR"
            else:
                path = shutil.which(r_cli)
                if path:
                    r_info["installed"] = True
                    r_info["status"] = "READY"
                else:
                    r_info["error"] = f"Executable '{r_cli}' not found in PATH"

            if r_info["installed"]:
                ready_reviewers_count += 1
                total_effective_weight += r_weight

            reviewers_probe.append(r_info)

        # 6. Quorum Analysis
        min_winning = policy.get("minimum_winning_seats", 2)
        seat_quorum = policy.get("seat_quorum_required", 2)
        weight_quorum = policy.get("weight_quorum_required", 2.0)
        quorum_achievable = ready_reviewers_count >= min_winning

        quorum_info = {
            "total_configured": len(reviewers_cfg),
            "ready_count": ready_reviewers_count,
            "minimum_winning_seats": min_winning,
            "seat_quorum_required": seat_quorum,
            "weight_quorum_required": weight_quorum,
            "total_effective_weight": total_effective_weight,
            "achievable": quorum_achievable
        }

        # 7. Overall dispatch decision
        blocking_reasons = []
        if not exec_probe["installed"]:
            blocking_reasons.append(f"Executor '{exec_id}' ({exec_cli}) is not installed or unreachable.")
        if not quorum_achievable:
            blocking_reasons.append(
                f"Quorum cannot be reached: only {ready_reviewers_count} reviewer(s) ready, but {min_winning} required."
            )
        if active_task is not None:
            blocking_reasons.append(
                f"Active task '{active_task['task_id']}' is already in state '{active_task['state']}'."
            )

        can_dispatch = (len(blocking_reasons) == 0)

        probe_result = {
            "valid_config": True,
            "dry_run": self.dry_run,
            "project_name": cfg.get("project", {}).get("name", self.project_root.name),
            "project_root": str(self.project_root),
            "state_store": {
                "exists": state_db_exists,
                "path": str(self.project_root / ".macao" / "state.db"),
                "status": "CONNECTED (RO)" if state_db_exists else "NOT_INITIALIZED",
                "error": state_store_error
            },
            "active_task": active_task,
            "executor": exec_probe,
            "reviewers": reviewers_probe,
            "quorum": quorum_info,
            "git": git_info,
            "worktrees": registered_worktrees,
            "physical_reviews": review_facts,
            "can_dispatch": can_dispatch,
            "blocking_reasons": blocking_reasons,
            "log_file": None
        }

        # Write probe audit log
        log_file = self._write_probe_log(probe_result)
        probe_result["log_file"] = log_file

        return probe_result
