"""Interactive Setup Wizard & Auto-Discovery Engine (Phase 3 / PRD §14)."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

from macao.core.schema import validate_config
from macao.adapter.integ_harness import CLI_ADAPTER_MAP


def probe_available_clis() -> List[Dict[str, Any]]:
    """Probes system PATH to find installed AI Agent CLIs and their versions."""
    found = []
    candidates = [
        ("opencode", "opencode", "1.18.25"),
        ("agy", "agy", "1.1.22"),
        ("cursor", "agent", "2026.08"),
        ("claude-code", "claude", "2.1.251"),
        ("codex", "codex", "2.1.0"),
        ("kimi", "kimi", "1.0.0"),
    ]

    for key, binary, default_ver in candidates:
        exe = shutil.which(binary)
        if exe:
            try:
                res = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=3)
                ver = res.stdout.strip() or default_ver
            except Exception:
                ver = default_ver
            found.append({
                "id": key,
                "cli": key,
                "binary": exe,
                "version": ver
            })
    return found


def detect_git_context(project_root: Path) -> Dict[str, str]:
    """Detects Git repository branch and remote defaults."""
    branch = "main"
    remote = "origin"
    try:
        res = subprocess.run(["git", "branch", "--show-current"], cwd=project_root, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            branch = res.stdout.strip()
    except Exception:
        pass

    try:
        res = subprocess.run(["git", "remote"], cwd=project_root, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            remote = res.stdout.strip().split()[0]
    except Exception:
        pass

    return {"branch": branch, "remote": remote}


def detect_ci_command(project_root: Path) -> Optional[str]:
    """Infers testing command from project build files (optional hint)."""
    if (project_root / "pytest.ini").exists() or (project_root / "pyproject.toml").exists():
        return "pytest -q"
    if (project_root / "package.json").exists():
        return "npm test"
    if (project_root / "Cargo.toml").exists():
        return "cargo test"
    if (project_root / "go.mod").exists():
        return "go test ./..."
    return None


import math


def ensure_gitignore_isolation(project_root: Path) -> bool:
    """Ensures all MACAO runtime worktree, review, archive and DB paths are in .gitignore."""
    gi_path = project_root / ".gitignore"
    required_rules = [
        ".macao/worktrees/",
        ".macao/.reviews/",
        ".macao/.dev.yml",
        ".macao/vote_result.json",
        ".macao/archive/",
        ".macao/*.db",
        ".macao/*.db-journal",
        ".macao/*.db-wal",
        ".macao/*.db-shm",
    ]
    content = gi_path.read_text(encoding="utf-8") if gi_path.exists() else ""
    lines = [line.strip() for line in content.splitlines()]
    missing_rules = [r for r in required_rules if r not in lines]

    if missing_rules:
        new_content = content
        if new_content and not new_content.endswith("\n"):
            new_content += "\n"
        if "# MACAO Runtime Worktrees & State Store (Auto-added)" not in new_content:
            new_content += "\n# MACAO Runtime Worktrees & State Store (Auto-added)\n"
        for r in missing_rules:
            new_content += f"{r}\n"
        gi_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def generate_smart_config(
    project_root: Path,
    executor_cli: str = "opencode",
    executor_model: Optional[str] = "GLM 5.3 max",
    reviewers: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Generates a valid, customized macao.yaml dictionary based on detected environment."""
    git_info = detect_git_context(project_root)
    ci_cmd = detect_ci_command(project_root)
    proj_name = project_root.name or "macao-project"

    if not reviewers:
        reviewers = [
            {"id": "cursor-rev", "cli": "agent", "adapter": "pty-wrapper", "model": "claude-3-5-sonnet"},
            {"id": "claude-rev", "cli": "claude-code", "adapter": "claude-hook", "model": "claude-3-7-sonnet"},
            {"id": "agy-rev", "cli": "agy", "adapter": "pty-wrapper", "model": "gemini-2.0-pro"}
        ]

    exec_adapter = "claude-hook" if executor_cli in ("claude", "claude-code") else "pty-wrapper"
    executor_dict = {
        "id": f"{executor_cli}-dev",
        "cli": executor_cli,
        "adapter": exec_adapter
    }
    if executor_model:
        executor_dict["model"] = executor_model

    rev_count = len(reviewers)
    quorum_votes = math.ceil(2 * rev_count / 3) if rev_count > 0 else 1

    config_data = {
        "project": {
            "name": proj_name,
            "repository": {
                "workspace_path": ".",
                "remote_name": git_info["remote"],
                "default_branch": git_info["branch"]
            }
        },
        "team": {
            "executor": executor_dict,
            "reviewers": reviewers
        },
        "policy": {
            "consensus_rule": "2/3_majority",
            "min_effective_votes": quorum_votes,
            "max_rework_rounds": 3,
            "review_strategy": "delta_plus_focus"
        },

        "merge": {
            "strategy": "ff_only",
            "ci_gate_command": ci_cmd,
            "require_human_signoff": True,
            "rebase_before_merge": False
        },
        "timeouts": {
            "development": "2h",
            "checkpoint_validation": "1m",
            "review_request": "30m",
            "per_reviewer": "10m",
            "consensus_check": "1m"
        },
        "security": {
            "allowed_clis": ["claude-code", "claude", "codex", "opencode", "agy", "antigravity", "agent", "cursor", "kimi"],
            "send_terminal_logs_to_reviewers": False,
            "secrets_masking": True
        }
    }

    # Validate against Schema
    is_val, err = validate_config(config_data)
    if not is_val:
        raise ValueError(f"Generated configuration failed schema validation: {err}")

    return config_data
