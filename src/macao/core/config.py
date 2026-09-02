"""MACAO Configuration Loader and Manager (PRD §13)."""

import os
import math
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

from macao.core.schema import validate_config


DEFAULT_CONFIG_FILENAME = "macao.yaml"


class ConfigManager:
    """Manages the single source of truth configuration (macao.yaml)."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path(DEFAULT_CONFIG_FILENAME)
        self.data: Dict[str, Any] = {}
        self.is_loaded: bool = False

    def load(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load and validate configuration against macao_config.schema.json."""
        target_path = Path(config_path) if config_path else self.config_path
        if not target_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {target_path}")

        with open(target_path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)

        if not isinstance(content, dict):
            raise ValueError("Configuration root must be a YAML mapping/dictionary")

        is_valid, error = validate_config(content)
        if not is_valid:
            raise ValueError(f"Invalid macao.yaml schema: {error}")

        # Compute derived defaults (seat_quorum_required = ceil(2N/3), weight_quorum_required = ceil(2W/3))
        reviewers = content.get("team", {}).get("reviewers", [])
        num_reviewers = len(reviewers)
        total_weight = sum(r.get("vote_weight", 1) for r in reviewers) if reviewers else num_reviewers
        derived_seat_quorum = math.ceil(2 * num_reviewers / 3) if num_reviewers > 0 else 2
        derived_weight_quorum = math.ceil(2 * total_weight / 3) if total_weight > 0 else 2

        policy = content.setdefault("policy", {})
        configured_seat_quorum = policy.get("seat_quorum_required", policy.get("min_effective_votes"))
        if configured_seat_quorum is None or configured_seat_quorum < derived_seat_quorum:
            policy["seat_quorum_required"] = derived_seat_quorum

        configured_weight_quorum = policy.get("weight_quorum_required")
        if configured_weight_quorum is None or configured_weight_quorum < derived_weight_quorum:
            policy["weight_quorum_required"] = derived_weight_quorum

        policy["min_effective_votes"] = policy.get("seat_quorum_required", derived_seat_quorum)

        self.data = content
        self.is_loaded = True
        return self.to_runtime_config()

    def to_runtime_config(self) -> Dict[str, Any]:
        """
        Produces a normalized, fail-safe runtime configuration dictionary
        supporting both nested schema access and normalized runtime keys.
        """
        policy = self.data.get("policy", {})
        merge_policy = self.data.get("merge", {})
        team = self.data.get("team", {})
        repo = self.data.get("project", {}).get("repository", {})

        reviewers = team.get("reviewers", [
            {"id": "codex", "cli": "codex", "adapter": "pty-wrapper"},
            {"id": "opencode", "cli": "opencode", "adapter": "pty-wrapper"},
            {"id": "antigravity", "cli": "agy", "adapter": "pty-wrapper"}
        ])
        reviewer_ids = [r["id"] for r in reviewers] if reviewers else ["codex", "opencode", "antigravity"]

        return {
            # Raw schema hierarchy
            "project": self.data.get("project", {}),
            "team": team,
            "policy": policy,
            "merge": merge_policy,
            "timeouts": self.data.get("timeouts", {}),
            "security": self.data.get("security", {}),

            # Normalized runtime keys for orchestrator & merge controller
            "max_rework_rounds": policy.get("max_rework_rounds", 3),
            "min_effective_votes": policy.get("min_effective_votes", len(reviewer_ids)),
            "require_signoff": merge_policy.get("require_human_signoff", True),
            "ci_gate_command": merge_policy.get("ci_gate_command"),
            "strategy": merge_policy.get("strategy", "ff_only"),
            "rebase_before_merge": merge_policy.get("rebase_before_merge", False),
            "remote_name": repo.get("remote_name", "origin"),
            "target_branch": repo.get("default_branch", "main"),
            "executor_id": team.get("executor", {}).get("id", "claude-code"),
            "executor_config": team.get("executor", {"id": "claude-code", "cli": "claude-code", "adapter": "claude-hook"}),
            "reviewers": reviewers,
            "reviewer_ids": reviewer_ids
        }

    @classmethod
    def load_config(cls, config_path: str = DEFAULT_CONFIG_FILENAME) -> Dict[str, Any]:
        mgr = cls(config_path)
        return mgr.load()

    @property
    def project_name(self) -> str:
        return self.data.get("project", {}).get("name", "macao-project")

    @property
    def workspace_path(self) -> str:
        return self.data.get("project", {}).get("repository", {}).get("workspace_path", ".")

    @property
    def target_branch(self) -> str:
        return self.data.get("project", {}).get("repository", {}).get("default_branch", "main")

    @property
    def remote_name(self) -> str:
        return self.data.get("project", {}).get("repository", {}).get("remote_name", "origin")

    @property
    def executor_config(self) -> Dict[str, Any]:
        return self.data.get("team", {}).get("executor", {"id": "claude-code", "cli": "claude-code", "adapter": "claude-hook"})

    @property
    def reviewers_config(self) -> List[Dict[str, Any]]:
        return self.data.get("team", {}).get("reviewers", [
            {"id": "codex", "cli": "codex", "adapter": "pty-wrapper"},
            {"id": "opencode", "cli": "opencode", "adapter": "pty-wrapper"},
            {"id": "antigravity", "cli": "agy", "adapter": "pty-wrapper"}
        ])

    @property
    def auto_rebase_disabled(self) -> bool:
        """PRD §13/§14.5: MVP mandates rebase_before_merge is disabled."""
        merge_policy = self.data.get("merge", {})
        return not merge_policy.get("rebase_before_merge", False)

    @property
    def min_effective_votes(self) -> int:
        policy = self.data.get("policy", {})
        return policy.get("seat_quorum_required", policy.get("min_effective_votes", 2))

    @property
    def max_rework_rounds(self) -> int:
        policy = self.data.get("policy", {})
        return policy.get("max_rework_rounds", 3)

    @property
    def require_human_signoff(self) -> bool:
        merge_policy = self.data.get("merge", {})
        return merge_policy.get("require_human_signoff", True)

    @property
    def ci_gate_command(self) -> Optional[str]:
        merge_policy = self.data.get("merge", {})
        return merge_policy.get("ci_gate_command")
