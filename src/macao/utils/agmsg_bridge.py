"""AGMSG Bridge: Integration utility for agent messaging teams, members, and auto-registration (PRD §11.6 & §14)."""

import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


MACAO_TO_AGMSG_TYPE = {
    "claude-code": "claude-code",
    "claude": "claude-code",
    "codex": "codex",
    "opencode": "opencode",
    "agent": "cursor",
    "cursor": "cursor",
    "agy": "antigravity",
    "antigravity": "antigravity",
    "copilot": "copilot",
    "gemini": "gemini",
    "pi": "opencode",
}


def get_agmsg_dir() -> Optional[Path]:
    """Finds the root directory of the agmsg skill installation."""
    env_dir = os.environ.get("AGMSG_DIR")
    if env_dir:
        p = Path(env_dir).resolve()
        if p.exists():
            return p

    standard_path = Path.home() / ".agents" / "skills" / "agmsg"
    if standard_path.exists():
        return standard_path

    return None


def get_agmsg_teams() -> List[str]:
    """Lists all available team names registered in agmsg."""
    agmsg_dir = get_agmsg_dir()
    if not agmsg_dir:
        return []

    teams_dir = agmsg_dir / "teams"
    if not teams_dir.exists():
        return []

    teams = []
    for entry in teams_dir.iterdir():
        if entry.is_dir() and not entry.name.startswith("."):
            cfg_file = entry / "config.json"
            if cfg_file.exists():
                teams.append(entry.name)
    return sorted(teams)


def load_agmsg_team(team_name: str) -> Optional[Dict[str, Any]]:
    """Loads config.json of a specific agmsg team."""
    agmsg_dir = get_agmsg_dir()
    if not agmsg_dir:
        return None

    cfg_file = agmsg_dir / "teams" / team_name / "config.json"
    if not cfg_file.exists():
        return None

    try:
        data = json.loads(cfg_file.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return None


def find_team_for_project(project_path: Path) -> Optional[str]:
    """Finds if any agmsg team already contains an agent registration matching project_path."""
    agmsg_dir = get_agmsg_dir()
    if not agmsg_dir:
        return None

    target_resolved = str(project_path.resolve())
    for team_name in get_agmsg_teams():
        team_cfg = load_agmsg_team(team_name)
        if not team_cfg:
            continue
        agents = team_cfg.get("agents", {})
        for _, agent_info in agents.items():
            for reg in agent_info.get("registrations", []):
                p = reg.get("project")
                if p and str(Path(p).resolve()) == target_resolved:
                    return team_name
    return None


def resolve_agmsg_type(cli_name: str) -> str:
    """Maps a MACAO CLI name/binary to a valid agmsg registered agent type."""
    normalized = cli_name.lower().strip()
    return MACAO_TO_AGMSG_TYPE.get(normalized, "opencode")


def map_team_members_by_cli(team_data: Dict[str, Any], project_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Returns a mapping of {cli_or_type: agent_id} from an agmsg team config.
    Prioritizes registrations matching project_path if supplied.
    """
    result = {}
    agents = team_data.get("agents", {})
    target_p = str(project_path.resolve()) if project_path else None

    # First pass: look for registrations matching project_path
    for agent_id, agent_info in agents.items():
        regs = agent_info.get("registrations", [])
        for r in regs:
            r_type = r.get("type", "")
            r_proj = r.get("project")
            if target_p and r_proj and str(Path(r_proj).resolve()) == target_p:
                result[r_type] = agent_id

    # Second pass: fill in from any registrations in this team
    for agent_id, agent_info in agents.items():
        regs = agent_info.get("registrations", [])
        for r in regs:
            r_type = r.get("type", "")
            if r_type and r_type not in result:
                result[r_type] = agent_id

    return result


def register_agmsg_member(
    team_name: str,
    agent_id: str,
    cli_name: str,
    project_path: Path
) -> Tuple[bool, str]:
    """
    Registers an agent into an agmsg team using join.sh. Creates team if absent.
    Returns (success, output_or_error_message).
    """
    agmsg_dir = get_agmsg_dir()
    if not agmsg_dir:
        return False, "agmsg skill directory not found on system"

    join_script = agmsg_dir / "scripts" / "join.sh"
    if not join_script.exists():
        return False, f"join.sh not found at {join_script}"

    agent_type = resolve_agmsg_type(cli_name)
    resolved_proj = str(project_path.resolve())

    try:
        res = subprocess.run(
            ["bash", str(join_script), team_name, agent_id, agent_type, resolved_proj, "--force"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if res.returncode == 0:
            return True, res.stdout.strip()
        else:
            err = res.stderr.strip() or res.stdout.strip()
            return False, err
    except Exception as e:
        return False, str(e)
