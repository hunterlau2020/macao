"""MACAO Configuration Loader and Manager (PRD §13)."""

import os
import math
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from macao.core.schema import validate_config


DEFAULT_CONFIG_FILENAME = "macao.yaml"


class ConfigManager:
    """Manages the single source of truth configuration (macao.yaml)."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path(DEFAULT_CONFIG_FILENAME)
        self.data: Dict[str, Any] = {}
        self.is_loaded: bool = False

    def load(self) -> Dict[str, Any]:
        """Load and validate configuration against macao_config.schema.json."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)

        if not isinstance(content, dict):
            raise ValueError("Configuration root must be a YAML mapping/dictionary")

        is_valid, error = validate_config(content)
        if not is_valid:
            raise ValueError(f"Invalid macao.yaml schema: {error}")

        # Compute derived defaults (e.g. min_effective_votes = ceil(2 * N / 3))
        reviewers = content.get("team", {}).get("reviewers", [])
        num_reviewers = len(reviewers)
        derived_quorum = math.ceil(2 * num_reviewers / 3)

        policy = content.setdefault("policy", {})
        configured_quorum = policy.get("min_effective_votes")
        if configured_quorum is None or configured_quorum < derived_quorum:
            policy["min_effective_votes"] = derived_quorum

        self.data = content
        self.is_loaded = True
        return self.data

    @property
    def project_name(self) -> str:
        return self.data.get("project", {}).get("name", "macao-project")

    @property
    def workspace_path(self) -> str:
        return self.data.get("project", {}).get("repository", {}).get("workspace_path", ".")

    @property
    def default_branch(self) -> str:
        return self.data.get("project", {}).get("repository", {}).get("default_branch", "main")

    @property
    def remote_name(self) -> str:
        return self.data.get("project", {}).get("repository", {}).get("remote_name", "origin")

    @property
    def executor_id(self) -> str:
        return self.data.get("team", {}).get("executor", {}).get("id", "cc-ds4")

    @property
    def reviewer_ids(self) -> list:
        return [r.get("id") for r in self.data.get("team", {}).get("reviewers", [])]

    @property
    def min_effective_votes(self) -> int:
        return self.data.get("policy", {}).get("min_effective_votes", 2)

    @property
    def max_rework_rounds(self) -> int:
        return self.data.get("policy", {}).get("max_rework_rounds", 3)


# Global helper instance
def load_config(path: Optional[str] = None) -> ConfigManager:
    cfg = ConfigManager(path)
    cfg.load()
    return cfg
