"""MACAO Dynamic Team and Environment Prober (PRD §12 & §14).

Performs pre-dispatch probing of configured Executor, Reviewers, Git repository,
and active task status to ensure the team is healthy and clearly identifies
task dispatch targets before execution.
"""

import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

from macao.core.config import ConfigManager
from macao.core.types import PreflightCheckResult
from macao.storage.store import StateStore
from macao.utils.git_utils import GitManager
from macao.adapter.claude import ClaudeCodeAdapter
from macao.adapter.codex import CodexAdapter
from macao.adapter.opencode import OpenCodeAdapter
from macao.adapter.antigravity import AntigravityAdapter
from macao.adapter.cursor import CursorAgentAdapter
from macao.adapter.kimi import KimiAdapter
from macao.adapter.mock import MockAgentAdapter

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
    """Probes dynamic readiness of Executor, Reviewers, Git, and active tasks before dispatch."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.cfg_file = self.project_root / "macao.yaml"
        self.git = GitManager(str(self.project_root))

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

    def probe(self) -> Dict[str, Any]:
        """Runs comprehensive dynamic probe across team and environment."""
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
        repo = cfg.get("project", {}).get("repository", {})

        # 1. Probe Active Task in StateStore
        active_task = None
        state_store_error = None
        try:
            store = StateStore(project_root=str(self.project_root))
            active_task = store.get_active_task()
        except Exception as e:
            state_store_error = str(e)

        # 2. Probe Executor
        raw_exec = team.get("executor", {})
        exec_id = raw_exec.get("id", "dev-executor")
        exec_cli = raw_exec.get("cli", "")
        exec_model = raw_exec.get("model")

        exec_probe = {
            "id": exec_id,
            "cli": exec_cli,
            "model": exec_model,
            "installed": False,
            "version": "unknown",
            "status": "MISSING",
            "details": "",
            "error": None
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

        # 3. Probe Reviewers
        reviewers_cfg = team.get("reviewers", [])
        reviewers_probe = []
        ready_reviewers_count = 0
        total_effective_weight = 0.0

        for r in reviewers_cfg:
            r_id = r.get("id", "reviewer")
            r_cli = r.get("cli", "")
            r_weight = float(r.get("vote_weight", r.get("weight", 1.0)))
            r_model = r.get("model")

            r_info = {
                "id": r_id,
                "cli": r_cli,
                "weight": r_weight,
                "model": r_model,
                "installed": False,
                "version": "unknown",
                "status": "MISSING",
                "details": "",
                "error": None
            }

            r_adp = self._get_adapter(r_cli, r_id, r)
            if r_adp:
                try:
                    res = r_adp.preflight()
                    r_info["installed"] = res.installed
                    r_info["version"] = res.version or "detected"
                    r_info["status"] = "READY" if res.installed else "MISSING"
                    r_info["details"] = res.details or ""
                    r_info["error"] = res.error
                except Exception as e:
                    r_info["error"] = str(e)
                    r_info["status"] = "ERROR"
            else:
                path = shutil.which(r_cli)
                if path:
                    r_info["installed"] = True
                    r_info["status"] = "READY"
                    r_info["details"] = f"Found executable in PATH: {path}"
                else:
                    r_info["details"] = f"Executable '{r_cli}' not found in PATH"

            if r_info["installed"]:
                ready_reviewers_count += 1
                total_effective_weight += r_weight

            reviewers_probe.append(r_info)

        # 4. Quorum Analysis
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

        # 5. Git Status
        git_info = {
            "branch": "unknown",
            "commit": "unknown",
            "is_clean": True,
            "error": None
        }
        try:
            git_info["branch"] = self.git.get_current_branch()
            head = self.git.get_head_commit()
            git_info["commit"] = head[:8] if head else "none"
            git_info["is_clean"] = self.git.is_clean()
        except Exception as e:
            git_info["error"] = str(e)

        # 6. Overall dispatch decision
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

        return {
            "valid_config": True,
            "project_name": cfg.get("project", {}).get("name", self.project_root.name),
            "active_task": active_task,
            "state_store_error": state_store_error,
            "executor": exec_probe,
            "reviewers": reviewers_probe,
            "quorum": quorum_info,
            "git": git_info,
            "can_dispatch": can_dispatch,
            "blocking_reasons": blocking_reasons
        }
