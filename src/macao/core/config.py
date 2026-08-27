"""MACAO Configuration Loader and Manager (PRD §13)."""

import os
import math
from pathlib import Path
from typing import Dict, Any, Optional, Union
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
    def auto_rebase_disabled(self) -> bool:
        """PRD §13/§14.5: MVP mandates rebase_before_merge is disabled."""
        policy = self.data.get("policy", {})
        rebase_policy = policy.get("rebase_policy", {})
        return not rebase_policy.get("allow_clean_rebase", False)

    @property
    def min_effective_votes(self) -> int:
        policy = self.data.get("policy", {})
        return policy.get("min_effective_votes", 2)

    @property
    def max_rework_rounds(self) -> int:
        policy = self.data.get("policy", {})
        rework_policy = policy.get("rework_policy", {})
        return rework_policy.get("max_rework_rounds", 3)

    @property
    def require_human_signoff(self) -> bool:
        policy = self.data.get("policy", {})
        merge_policy = policy.get("merge_policy", {})
        return merge_policy.get("require_human_signoff", True)
