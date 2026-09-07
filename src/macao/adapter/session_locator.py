"""MACAO Active CLI Session Discovery Module.

Inspects local runtime session stores across supported AI CLI tools (Antigravity agy,
Claude Code, OpenCode, Codex, Cursor Agent, Pi Coding Agent, Kimi) to determine active
session IDs, human-readable session names/titles, workspace bindings, and recent activity
timestamps without fabricating state.
"""

import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


def _sanitize_session_name(raw_text: Optional[str], default_id: str = "") -> str:
    """Cleans, masks secrets, and truncates session name or user prompt."""
    if not raw_text or not isinstance(raw_text, str):
        return default_id[:8] if default_id else "unknown"
    cleaned = raw_text.strip().replace("\r\n", " ").replace("\n", " ")
    cleaned = re.sub(r"^[\s#*\->]+", "", cleaned)
    # Mask sensitive credentials / API keys / tokens (Reviewer B-2 fix)
    cleaned = re.sub(r"\b(sk-[a-zA-Z0-9]{15,}|[0-9a-fA-F]{24,}\.[a-zA-Z0-9_-]{10,})\b", "******", cleaned)
    cleaned = cleaned.strip()
    if len(cleaned) > 50:
        cleaned = cleaned[:47] + "..."
    return cleaned or (default_id[:8] if default_id else "unknown")


class SessionLocator:
    """Discovers active sessions for CLI agents bound to a specific project repository."""

    @staticmethod
    def list_sessions(cli_name: str, project_path: Path) -> List[Dict[str, Any]]:
        """
        Discovers all available sessions for the given CLI in the specified project directory,
        sorted by most recent activity descending.
        """
        cli = (cli_name or "").lower()
        project_path = project_path.resolve()

        if "agy" in cli or "antigravity" in cli:
            return SessionLocator._find_agy_sessions(project_path)
        elif "claude" in cli:
            return SessionLocator._find_claude_sessions(project_path)
        elif "opencode" in cli:
            return SessionLocator._find_opencode_sessions(project_path)
        elif "codex" in cli:
            return SessionLocator._find_codex_sessions(project_path)
        elif "cursor" in cli or "agent" in cli:
            return SessionLocator._find_cursor_sessions(project_path)
        elif "pi" in cli:
            return SessionLocator._find_pi_sessions(project_path)
        elif "kimi" in cli:
            return SessionLocator._find_kimi_sessions(project_path)
        return []

    @staticmethod
    def find_session(
        cli_name: str,
        project_path: Path,
        session_ref: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Locates a session for the given CLI in the specified project directory.
        If session_ref is given, matches by session_id or session_name.
        Otherwise, returns the most recent session with total_sessions count.
        """
        sessions = SessionLocator.list_sessions(cli_name, project_path)
        if not sessions:
            return None

        total = len(sessions)

        if session_ref:
            ref_lower = session_ref.lower()
            for s in sessions:
                sid = (s.get("session_id") or "").lower()
                sname = (s.get("session_name") or "").lower()
                if sid == ref_lower or sid.startswith(ref_lower) or ref_lower in sname:
                    res = dict(s)
                    res["total_sessions"] = total
                    return res

        # Default to the most recently active session
        res = dict(sessions[0])
        res["total_sessions"] = total
        return res

    @staticmethod
    def _find_agy_sessions(project_path: Path) -> List[Dict[str, Any]]:
        """Finds agy conversations in ~/.gemini/antigravity-cli/history.jsonl strictly matching project_path."""
        hist_file = Path.home() / ".gemini" / "antigravity-cli" / "history.jsonl"
        if not hist_file.exists():
            return []

        resolved_proj = project_path.resolve()
        matched = []
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
                                if Path(ws).resolve() == resolved_proj:
                                    matched.append((data, ws))
                            except Exception:
                                pass
                    except Exception:
                        pass
        except Exception:
            return []

        results = []
        for data, ws_path in reversed(matched):
            ts = data.get("timestamp")
            iso_time = (
                datetime.fromtimestamp(ts / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
                if ts else "recent"
            )
            cid = data.get("conversationId", "unknown")
            disp = data.get("display", "")
            sname = _sanitize_session_name(disp, cid)
            results.append({
                "cli": "agy",
                "session_id": cid,
                "session_name": sname,
                "title": sname,
                "last_active": iso_time,
                "last_prompt": disp[:100] if disp else None,
                "type": data.get("type", "conversation"),
                "workspace": ws_path,
                "details": f"Active AGY session: {sname} ({cid[:10]}...)"
            })
        return results

    @staticmethod
    def _find_claude_sessions(project_path: Path) -> List[Dict[str, Any]]:
        """Finds Claude Code sessions in ~/.claude/projects/ strictly matching canonical project_path."""
        claude_dir = Path.home() / ".claude" / "projects"
        if not claude_dir.exists():
            return []

        resolved_proj = project_path.resolve()
        sanitized = "-" + re.sub(r"[^a-zA-Z0-9]", "-", str(resolved_proj).lstrip("/"))
        target_dir = claude_dir / sanitized

        if not target_dir.exists() or not target_dir.is_dir():
            exact_name_dir = claude_dir / f"-{resolved_proj.name}"
            short_sanitized = "-" + re.sub(r"[^a-zA-Z0-9]", "-", resolved_proj.name)
            candidate = claude_dir / short_sanitized
            if exact_name_dir.exists() and exact_name_dir.is_dir():
                target_dir = exact_name_dir
            elif candidate.exists() and candidate.is_dir():
                target_dir = candidate
            else:
                return []

        jsonl_files = [
            f for f in target_dir.glob("*.jsonl")
            if not f.name.startswith("memory")
        ]
        if not jsonl_files:
            return []

        # Sort by mtime descending
        jsonl_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        results = []
        for jf in jsonl_files:
            mtime = jf.stat().st_mtime
            iso_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            session_id = jf.stem
            sname = None

            try:
                with open(jf, "r", encoding="utf-8", errors="replace") as f:
                    for _ in range(30):
                        line = f.readline()
                        if not line:
                            break
                        try:
                            obj = json.loads(line)
                            if obj.get("type") == "user":
                                msg = obj.get("message", {})
                                raw_text = msg.get("content") if isinstance(msg, dict) else obj.get("text")
                                if raw_text:
                                    sname = _sanitize_session_name(raw_text, session_id)
                                    break
                            elif isinstance(obj.get("message"), dict) and obj["message"].get("role") == "user":
                                raw_text = obj["message"].get("content")
                                if raw_text:
                                    sname = _sanitize_session_name(str(raw_text), session_id)
                                    break
                        except Exception:
                            continue
            except Exception:
                pass

            sname = sname or _sanitize_session_name(None, session_id)
            results.append({
                "cli": "claude",
                "session_id": session_id,
                "session_name": sname,
                "title": sname,
                "last_active": iso_time,
                "session_file": str(jf),
                "workspace": str(resolved_proj),
                "details": f"Claude Code session: {sname} ({session_id[:10]}...)"
            })
        return results

    @staticmethod
    def _find_opencode_sessions(project_path: Path) -> List[Dict[str, Any]]:
        """Finds OpenCode sessions in ~/.local/share/opencode/opencode.db strictly matching project_path."""
        db_path = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
        if not db_path.exists():
            return []

        resolved_proj = project_path.resolve()
        results = []
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=3.0)
            try:
                cur = conn.execute(
                    "SELECT id, title, directory, time_updated FROM session "
                    "WHERE directory = ? OR directory LIKE ? "
                    "ORDER BY time_updated DESC",
                    (str(resolved_proj), f"%{resolved_proj.name}%")
                )
                for row in cur.fetchall():
                    sid, title, directory, ts = row
                    if not directory:
                        continue
                    try:
                        if Path(directory).resolve() != resolved_proj:
                            continue
                    except Exception:
                        continue

                    iso_time = (
                        datetime.fromtimestamp(ts / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
                        if ts else "recent"
                    )
                    sname = _sanitize_session_name(title, sid)
                    results.append({
                        "cli": "opencode",
                        "session_id": sid,
                        "session_name": sname,
                        "title": sname,
                        "last_active": iso_time,
                        "workspace": directory,
                        "details": f"OpenCode session: {sname} ({sid[:10]}...)"
                    })
            finally:
                conn.close()
        except Exception:
            pass
        return results

    @staticmethod
    def _find_codex_sessions(project_path: Path) -> List[Dict[str, Any]]:
        """Finds Codex sessions from ~/.codex/state_*.sqlite strictly matching canonical project_path."""
        codex_dir = Path.home() / ".codex"
        if not codex_dir.exists():
            return []

        resolved_proj = project_path.resolve()
        state_dbs = sorted(codex_dir.glob("state_*.sqlite"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not state_dbs:
            return []

        results = []
        seen_ids = set()
        for db_path in state_dbs:
            try:
                conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=3.0)
                try:
                    cur = conn.execute(
                        "SELECT id, title, cwd, updated_at FROM threads "
                        "WHERE cwd = ? OR cwd LIKE ? "
                        "ORDER BY updated_at DESC",
                        (str(resolved_proj), f"%{resolved_proj.name}%")
                    )
                    for row in cur.fetchall():
                        sid, title, cwd, ts = row
                        if not cwd:
                            continue
                        try:
                            if Path(cwd).resolve() != resolved_proj:
                                continue
                        except Exception:
                            continue
                        if sid in seen_ids:
                            continue
                        seen_ids.add(sid)
                        iso_time = (
                            datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                            if ts else "recent"
                        )
                        sname = _sanitize_session_name(title, sid)
                        results.append({
                            "cli": "codex",
                            "session_id": sid,
                            "session_name": sname,
                            "title": sname,
                            "last_active": iso_time,
                            "workspace": cwd,
                            "details": f"Codex session: {sname} ({sid[:10]}...)"
                        })
                finally:
                    conn.close()
            except Exception:
                pass

        return results

    @staticmethod
    def _find_cursor_sessions(project_path: Path) -> List[Dict[str, Any]]:
        """Finds active Cursor / Agent sessions in ~/.cursor/chats/ strictly matching canonical project_path."""
        chats_dir = Path.home() / ".cursor" / "chats"
        if not chats_dir.exists():
            return []

        resolved_proj = project_path.resolve()
        matched_chats = []
        try:
            for group in chats_dir.iterdir():
                if not group.is_dir():
                    continue
                for chat in group.iterdir():
                    if not chat.is_dir():
                        continue
                    meta_file = chat / "meta.json"
                    if meta_file.exists():
                        try:
                            with open(meta_file, "r", encoding="utf-8") as mf:
                                meta = json.load(mf)
                                cwd = meta.get("cwd", "")
                                if cwd:
                                    try:
                                        if Path(cwd).resolve() == resolved_proj:
                                            matched_chats.append((chat, meta, cwd))
                                    except Exception:
                                        pass
                        except Exception:
                            pass
        except Exception:
            return []

        matched_chats.sort(key=lambda x: x[0].stat().st_mtime, reverse=True)

        results = []
        for chat_dir, meta, cwd in matched_chats:
            mtime = chat_dir.stat().st_mtime
            iso_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            cid = chat_dir.name
            sname = None

            hist_file = chat_dir / "prompt_history.json"
            if hist_file.exists():
                try:
                    with open(hist_file, "r", encoding="utf-8") as hf:
                        prompts = json.load(hf)
                        if isinstance(prompts, list):
                            substantive = [p for p in prompts if isinstance(p, str) and p.strip() and not p.strip().startswith("/")]
                            if substantive:
                                sname = _sanitize_session_name(substantive[0], cid)
                            elif prompts:
                                sname = _sanitize_session_name(prompts[0], cid)
                except Exception:
                    pass

            sname = sname or _sanitize_session_name(None, cid)
            results.append({
                "cli": "agent",
                "session_id": cid,
                "session_name": sname,
                "title": sname,
                "last_active": iso_time,
                "workspace": cwd,
                "details": f"Cursor agent chat: {sname} ({cid[:10]}...)"
            })
        return results

    @staticmethod
    def _find_pi_sessions(project_path: Path) -> List[Dict[str, Any]]:
        """Finds active Pi Coding Agent sessions in ~/.pi/agent/sessions/ strictly matching project_path."""
        sessions_base = Path.home() / ".pi" / "agent" / "sessions"
        if not sessions_base.exists():
            return []

        resolved_proj = project_path.resolve()
        sanitized = "--" + str(resolved_proj).strip("/").replace("/", "-") + "--"
        target_dir = sessions_base / sanitized

        if not target_dir.exists() or not target_dir.is_dir():
            return []

        jsonl_files = list(target_dir.glob("*.jsonl"))
        if not jsonl_files:
            return []

        jsonl_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        results = []
        for jf in jsonl_files:
            mtime = jf.stat().st_mtime
            iso_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            sid = jf.stem
            sname = None
            first_user_prompt = None

            try:
                with open(jf, "r", encoding="utf-8", errors="replace") as f:
                    for line_idx in range(50):
                        line = f.readline()
                        if not line:
                            break
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue

                        if obj.get("type") == "session" and obj.get("id"):
                            sid = obj.get("id")
                        elif obj.get("type") == "session_info" and obj.get("name"):
                            sname = obj.get("name")
                            break
                        elif obj.get("type") == "message" and not first_user_prompt:
                            msg = obj.get("message", {})
                            if msg.get("role") == "user":
                                content = msg.get("content", [])
                                txt = "".join([
                                    c.get("text", "") for c in content
                                    if isinstance(c, dict) and c.get("type") == "text"
                                ])
                                if txt:
                                    first_user_prompt = txt
            except Exception:
                pass

            final_name = sname or first_user_prompt or f"pi-{sid[:8]}"
            sname_clean = _sanitize_session_name(final_name, sid)
            results.append({
                "cli": "pi",
                "session_id": sid,
                "session_name": sname_clean,
                "title": sname_clean,
                "last_active": iso_time,
                "session_file": str(jf),
                "workspace": str(resolved_proj),
                "details": f"Pi session: {sname_clean} ({sid[:10]}...)"
            })
        return results

    @staticmethod
    def _find_kimi_sessions(project_path: Path) -> List[Dict[str, Any]]:
        """Finds active Kimi sessions strictly matching project_path. Fail-closed: returns [] if no verifiable binding."""
        # Kimi CLI currently does not expose a verifiable local project-bound session index.
        # Fail-closed: return empty list to prevent fabricating synthetic session state (Reviewer P1-2).
        return []

