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

        # Compute derived defaults (e.g. min_effective_votes = ceil(2 * N / 3))
        reviewers = content.get("team", {}).get("reviewers", [])
        num_reviewers = len(reviewers)
        derived_quorum = math.ceil(2 * num_reviewers / 3) if num_reviewers > 0 else 2

        policy = content.setdefault("policy", {})
        configured_quorum = policy.get("min_effective_votes")
        if configured_quorum is None or configured_quorum < derived_quorum:
            policy["min_effective_votes"] = derived_quorum

        self.data = content
        self.is_loaded = True
        return self.data

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
        return self.data.get("team", {}).get("executor", {"id": "cc-ds4", "cli": "claude-code", "adapter": "claude-hook"})

    @property
    def reviewers_config(self) -> List[Dict[str, Any]]:
        return self.data.get("team", {}).get("reviewers", [
            {"id": "cc-glm", "cli": "codex", "adapter": "pty-wrapper"},
            {"id": "kimi", "cli": "kimi", "adapter": "pty-wrapper"}
        ])

    @property
    def auto_rebase_disabled(self) -> bool:
        """PRD §13/§14.5: MVP mandates rebase_before_merge is disabled."""
        merge_policy = self.data.get("merge", {})
        return not merge_policy.get("rebase_before_merge", False)

    @property
    def min_effective_votes(self) -> int:
        policy = self.data.get("policy", {})
        return policy.get("min_effective_votes", 2)

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
