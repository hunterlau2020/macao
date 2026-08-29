"""State Store CRUD API for Tasks, Artifacts, and Audits (PRD §11.4)."""

import json
import hashlib
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from macao.core.types import AgentState
from macao.storage.db import get_db, DatabaseManager


class StateStore:
    """Provides high-level state persistence operations for MACAO."""

    def __init__(self, db_path: str = ".macao/state.db", project_root: Optional[str] = None):
        self.db = get_db(db_path)
        self.project_root = project_root

    def _now(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    # --- Task Operations ---
    def create_task(
        self,
        task_id: str,
        title: str,
        source_branch: str,
        target_branch: str = "main",
        acceptance_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        now = self._now()
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT INTO tasks (task_id, title, source_branch, target_branch, state, checkpoint_ref, review_round, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, NULL, 1, ?, ?)
                """,
                (task_id, title, source_branch, target_branch, AgentState.IDLE.value, now, now)
            )
        return self.get_task(task_id)

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self.db.connection() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            return dict(row) if row else None

    def get_active_task(self) -> Optional[Dict[str, Any]]:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE state NOT IN (?, ?) ORDER BY created_at DESC LIMIT 1",
                (AgentState.DONE.value, AgentState.CANCELLED.value)
            ).fetchone()
            return dict(row) if row else None

    def update_task_state(self, task_id: str, state: AgentState, checkpoint_ref: Optional[str] = None, review_round: Optional[int] = None) -> None:
        now = self._now()
        with self.db.connection() as conn:
            updates = ["state = ?", "updated_at = ?"]
            params = [state.value, now]
            if checkpoint_ref is not None:
                updates.append("checkpoint_ref = ?")
                params.append(checkpoint_ref)
            if review_round is not None:
                updates.append("review_round = ?")
                params.append(review_round)
            params.append(task_id)

            conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE task_id = ?", params)

    # --- Artifact Operations ---
    def register_artifact(
        self,
        task_id: str,
        kind: str,
        checkpoint_ref: str,
        review_round: int,
        path: str,
        content: Optional[bytes] = None,
        reviewer_id: str = ""
    ) -> int:
        now = self._now()
        if content is not None:
            sha256 = hashlib.sha256(content).hexdigest()
        elif path:
            p_obj = Path(path)
            if not p_obj.is_absolute() and self.project_root:
                p_obj = Path(self.project_root) / path
            if p_obj.exists() and p_obj.is_file():
                try:
                    sha256 = hashlib.sha256(p_obj.read_bytes()).hexdigest()
                except Exception:
                    sha256 = ""
            else:
                sha256 = ""
        else:
            sha256 = ""

        with self.db.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO artifacts (task_id, kind, checkpoint_ref, review_round, reviewer_id, path, sha256, created_at, consumed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(task_id, kind, checkpoint_ref, review_round, reviewer_id)
                DO UPDATE SET path = excluded.path, sha256 = excluded.sha256, created_at = excluded.created_at
                """,
                (task_id, kind, checkpoint_ref, review_round, reviewer_id, path, sha256, now)
            )
            return cursor.lastrowid

    def mark_artifact_consumed(self, task_id: str, kind: str, checkpoint_ref: str, review_round: int, archived_path: str, reviewer_id: str = "") -> None:
        p_obj = Path(archived_path)
        if not p_obj.is_absolute() and self.project_root:
            p_obj = Path(self.project_root) / archived_path
        sha256 = ""
        if p_obj.exists() and p_obj.is_file():
            try:
                sha256 = hashlib.sha256(p_obj.read_bytes()).hexdigest()
            except Exception:
                pass

        with self.db.connection() as conn:
            if sha256:
                conn.execute(
                    """
                    UPDATE artifacts
                    SET consumed = 1, archived_path = ?, sha256 = CASE WHEN (sha256 IS NULL OR sha256 = '') THEN ? ELSE sha256 END
                    WHERE task_id = ? AND kind = ? AND checkpoint_ref = ? AND review_round = ? AND reviewer_id = ?
                    """,
                    (archived_path, sha256, task_id, kind, checkpoint_ref, review_round, reviewer_id)
                )
            else:
                conn.execute(
                    """
                    UPDATE artifacts
                    SET consumed = 1, archived_path = ?
                    WHERE task_id = ? AND kind = ? AND checkpoint_ref = ? AND review_round = ? AND reviewer_id = ?
                    """,
                    (archived_path, task_id, kind, checkpoint_ref, review_round, reviewer_id)
                )

    def list_artifacts(self, task_id: str, review_round: Optional[int] = None) -> List[Dict[str, Any]]:
        with self.db.connection() as conn:
            if review_round is not None:
                rows = conn.execute(
                    "SELECT * FROM artifacts WHERE task_id = ? AND review_round = ? ORDER BY artifact_id ASC",
                    (task_id, review_round)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM artifacts WHERE task_id = ? ORDER BY artifact_id ASC", (task_id,)).fetchall()
            return [dict(r) for r in rows]

    # --- Audit Log Operations ---
    def log_audit_event(self, task_id: Optional[str], event_type: str, detail: Dict[str, Any]) -> int:
        now = self._now()
        with self.db.connection() as conn:
            cursor = conn.execute(
                "INSERT INTO audit_events (ts, task_id, type, detail) VALUES (?, ?, ?, ?)",
                (now, task_id, event_type, json.dumps(detail, ensure_ascii=False))
            )
            return cursor.lastrowid

    def list_audit_events(self, task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self.db.connection() as conn:
            if task_id:
                rows = conn.execute(
                    "SELECT * FROM audit_events WHERE task_id = ? ORDER BY sequence_id DESC LIMIT ?",
                    (task_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM audit_events ORDER BY sequence_id DESC LIMIT ?",
                    (limit,)
                ).fetchall()

            result = []
            for r in rows:
                d = dict(r)
                if isinstance(d.get("detail"), str):
                    try:
                        d["detail"] = json.loads(d["detail"])
                    except Exception:
                        pass
                result.append(d)
            return result

    def get_audit_events_by_type(
        self,
        task_id: str,
        event_type: str,
        review_round: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Finds all audit events of a specific type for a task, optionally filtered by review_round."""
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_events WHERE task_id = ? AND type = ? ORDER BY sequence_id DESC",
                (task_id, event_type)
            ).fetchall()

            result = []
            for r in rows:
                d = dict(r)
                if isinstance(d.get("detail"), str):
                    try:
                        d["detail"] = json.loads(d["detail"])
                    except Exception:
                        pass
                if review_round is not None:
                    if d.get("detail", {}).get("review_round") != review_round:
                        continue
                result.append(d)
            return result

    # --- Message Queue Queries ---
    def list_messages(self, task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM message_queue ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            results = []
            for r in rows:
                m_dict = dict(r)
                p = m_dict.get("payload")
                if isinstance(p, str):
                    try:
                        p = json.loads(p)
                    except Exception:
                        pass
                to_val = m_dict["to_agent"]
                if isinstance(to_val, str) and to_val.startswith("["):
                    try:
                        to_val = json.loads(to_val)
                    except Exception:
                        pass

                env = {
                    "protocol": "AEP/1.0",
                    "message_id": m_dict["message_id"],
                    "timestamp": m_dict["created_at"],
                    "type": m_dict["type"],
                    "from": m_dict["from_agent"],
                    "to": to_val,
                    "payload": p if isinstance(p, dict) else {}
                }
                results.append(env)
            return results
