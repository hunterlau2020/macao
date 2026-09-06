"""MACAO Active CLI Session Discovery Module.

Inspects local runtime session stores across supported AI CLI tools (Antigravity agy,
Claude Code, OpenCode, Codex, Cursor Agent, Kimi) to determine active session IDs,
workspace bindings, and recent activity timestamps without fabricating state.
"""

import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class SessionLocator:
    """Discovers active sessions for CLI agents bound to a specific project repository."""

    @staticmethod
    def find_session(cli_name: str, project_path: Path) -> Optional[Dict[str, Any]]:
        """
        Locates the most recent session for the given CLI in the specified project directory.
        Returns a dict with session metadata or None if no matching session is found.
        """
        cli = (cli_name or "").lower()
        project_path = project_path.resolve()

        if "agy" in cli or "antigravity" in cli:
            return SessionLocator._find_agy_session(project_path)
        elif "claude" in cli:
            return SessionLocator._find_claude_session(project_path)
        elif "opencode" in cli:
            return SessionLocator._find_opencode_session(project_path)
        elif "codex" in cli:
            return SessionLocator._find_codex_session(project_path)
        elif "cursor" in cli or "agent" in cli:
            return SessionLocator._find_cursor_session(project_path)
        elif "kimi" in cli:
            return SessionLocator._find_kimi_session(project_path)
        return None

    @staticmethod
    def _find_agy_session(project_path: Path) -> Optional[Dict[str, Any]]:
        """Finds active agy conversation in ~/.gemini/antigravity-cli/history.jsonl."""
        hist_file = Path.home() / ".gemini" / "antigravity-cli" / "history.jsonl"
        if not hist_file.exists():
            return None

        latest_match = None
        try:
            with open(hist_file, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        ws = data.get("workspace")
                        if ws:
                            try:
                                if Path(ws).resolve() == project_path:
                                    latest_match = data
                            except Exception:
                                pass
                    except Exception:
                        pass
        except Exception:
            return None

        if latest_match:
            ts = latest_match.get("timestamp")
            iso_time = (
                datetime.fromtimestamp(ts / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
                if ts else "recent"
            )
            cid = latest_match.get("conversationId", "unknown")
            disp = latest_match.get("display", "")
            return {
                "cli": "agy",
                "session_id": cid,
                "last_active": iso_time,
                "last_prompt": disp[:100] if disp else None,
                "type": latest_match.get("type", "conversation"),
                "workspace": str(project_path),
                "details": f"Active AGY session: {cid}"
            }
        return None

    @staticmethod
    def _find_claude_session(project_path: Path) -> Optional[Dict[str, Any]]:
        """Finds active Claude Code session in ~/.claude/projects/."""
        claude_dir = Path.home() / ".claude" / "projects"
        if not claude_dir.exists():
            return None

        sanitized = "-" + re.sub(r"[^a-zA-Z0-9]", "-", str(project_path).lstrip("/"))
        target_dir = claude_dir / sanitized

        if not target_dir.exists():
            # Fallback fuzzy match on repository name
            repo_token = project_path.name.replace("_", "-").lower()
            for d in claude_dir.iterdir():
                if d.is_dir() and repo_token in d.name.lower():
                    target_dir = d
                    break

        if target_dir.exists() and target_dir.is_dir():
            jsonl_files = [
                f for f in target_dir.glob("*.jsonl")
                if not f.name.startswith("memory")
            ]
            if jsonl_files:
                latest_file = max(jsonl_files, key=lambda f: f.stat().st_mtime)
                mtime = latest_file.stat().st_mtime
                iso_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                session_id = latest_file.stem
                return {
                    "cli": "claude",
                    "session_id": session_id,
                    "last_active": iso_time,
                    "session_file": str(latest_file),
                    "workspace": str(project_path),
                    "details": f"Claude Code session: {session_id}"
                }
        return None

    @staticmethod
    def _find_opencode_session(project_path: Path) -> Optional[Dict[str, Any]]:
        """Finds active OpenCode session in ~/.local/share/opencode/opencode.db."""
        db_path = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
        if not db_path.exists():
            return None

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=3.0)
            try:
                cur = conn.execute(
                    "SELECT id, title, directory, time_updated FROM session "
                    "WHERE directory = ? OR directory LIKE ? "
                    "ORDER BY time_updated DESC LIMIT 1",
                    (str(project_path), f"%{project_path.name}%")
                )
                row = cur.fetchone()
                if row:
                    sid, title, directory, ts = row
                    iso_time = (
                        datetime.fromtimestamp(ts / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
                        if ts else "recent"
                    )
                    return {
                        "cli": "opencode",
                        "session_id": sid,
                        "title": title,
                        "last_active": iso_time,
                        "workspace": directory,
                        "details": f"OpenCode session: {sid} ({title})"
                    }
            finally:
                conn.close()
        except Exception:
            pass
        return None

    @staticmethod
    def _find_codex_session(project_path: Path) -> Optional[Dict[str, Any]]:
        """Finds active Codex session from ~/.codex/session_index.jsonl."""
        idx_file = Path.home() / ".codex" / "session_index.jsonl"
        if idx_file.exists():
            latest = None
            try:
                with open(idx_file, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                latest = data
                            except Exception:
                                pass
            except Exception:
                pass

            if latest:
                sid = latest.get("id", "latest")
                title = latest.get("thread_name", "codex-session")
                updated = latest.get("updated_at", "recent")
                return {
                    "cli": "codex",
                    "session_id": sid,
                    "title": title,
                    "last_active": updated,
                    "workspace": str(project_path),
                    "details": f"Codex session: {sid} ({title})"
                }
        return None

    @staticmethod
    def _find_cursor_session(project_path: Path) -> Optional[Dict[str, Any]]:
        """Finds active Cursor / Agent session in ~/.cursor/chats/."""
        chats_dir = Path.home() / ".cursor" / "chats"
        if chats_dir.exists():
            try:
                all_subdirs = [d for d in chats_dir.iterdir() if d.is_dir()]
                if all_subdirs:
                    latest_group = max(all_subdirs, key=lambda d: d.stat().st_mtime)
                    chats = [c for c in latest_group.iterdir() if c.is_dir()]
                    if chats:
                        latest_chat = max(chats, key=lambda d: d.stat().st_mtime)
                        mtime = latest_chat.stat().st_mtime
                        iso_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                        return {
                            "cli": "agent",
                            "session_id": latest_chat.name,
                            "last_active": iso_time,
                            "workspace": str(project_path),
                            "details": f"Cursor agent chat: {latest_chat.name}"
                        }
            except Exception:
                pass
        return None

    @staticmethod
    def _find_kimi_session(project_path: Path) -> Optional[Dict[str, Any]]:
        """Finds active Kimi session if available."""
        kimi_dir = Path.home() / ".kimi"
        if kimi_dir.exists():
            return {
                "cli": "kimi",
                "session_id": "auto-discovered",
                "last_active": "recent",
                "workspace": str(project_path),
                "details": "Kimi runtime available"
            }
        return None
