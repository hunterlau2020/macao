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

    def __init__(self, db_path: str = ".macao/state.db"):
        self.db = get_db(db_path)

    def _now(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    # --- Task Operations ---
    def create_task(self, task_id: str, title: str, source_branch: str, target_branch: str) -> Dict[str, Any]:
        now = self._now()
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO tasks (task_id, title, source_branch, target_branch, state, checkpoint_ref, review_round, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, NULL, 1, ?, ?)
                """,
                (task_id, title, source_branch, target_branch, AgentState.IDLE.value, now, now)
            )
            conn.commit()
        return self.get_task(task_id)

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            return dict(row) if row else None

    def get_active_task(self) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE state NOT IN (?, ?) ORDER BY created_at DESC LIMIT 1",
                (AgentState.DONE.value, AgentState.CANCELLED.value)
            ).fetchone()
            return dict(row) if row else None

    def update_task_state(self, task_id: str, state: AgentState, checkpoint_ref: Optional[str] = None, review_round: Optional[int] = None) -> None:
        now = self._now()
        with self.db.get_connection() as conn:
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
            conn.commit()

    # --- Artifact Operations ---
    def register_artifact(
        self,
        task_id: str,
        kind: str,
        checkpoint_ref: str,
        review_round: int,
        path: str,
        reviewer_id: str = "",
        sha256: Optional[str] = None
    ) -> None:
        now = self._now()
        if sha256 is None and Path(path).exists():
            with open(path, "rb") as f:
                sha256 = hashlib.sha256(f.read()).hexdigest()

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO artifacts
                (task_id, kind, checkpoint_ref, review_round, reviewer_id, path, sha256, consumed, archived_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, NULL, ?)
                """,
                (task_id, kind, checkpoint_ref, review_round, reviewer_id, path, sha256 or "", now)
            )
            conn.commit()

    def mark_artifact_consumed(self, task_id: str, kind: str, checkpoint_ref: str, review_round: int, archived_path: str, reviewer_id: str = "") -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE artifacts
                SET consumed = 1, archived_path = ?
                WHERE task_id = ? AND kind = ? AND checkpoint_ref = ? AND review_round = ? AND reviewer_id = ?
                """,
                (archived_path, task_id, kind, checkpoint_ref, review_round, reviewer_id)
            )
            conn.commit()

    def list_artifacts(self, task_id: str, review_round: Optional[int] = None) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            if review_round is not None:
                rows = conn.execute(
                    "SELECT * FROM artifacts WHERE task_id = ? AND review_round = ?",
                    (task_id, review_round)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM artifacts WHERE task_id = ?", (task_id,)).fetchall()
            return [dict(r) for r in rows]

    # --- Audit Log Operations ---
    def log_audit_event(self, task_id: Optional[str], event_type: str, detail: Dict[str, Any]) -> int:
        now = self._now()
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO audit_events (ts, task_id, type, detail) VALUES (?, ?, ?, ?)",
                (now, task_id, event_type, json.dumps(detail, ensure_ascii=False))
            )
            conn.commit()
            return cursor.lastrowid

    def list_audit_events(self, task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
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
            return [dict(r) for r in rows]

    # --- Override Operations ---
    def record_override(self, task_id: str, trigger: str, choice: str, note: Optional[str] = None) -> int:
        now = self._now()
        seq_id = self.log_audit_event(task_id, "HUMAN_OVERRIDE_RESOLVED", {
            "trigger": trigger,
            "choice": choice,
            "note": note
        })
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO overrides (sequence_id, task_id, trigger, choice, note, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (seq_id, task_id, trigger, choice, note or "", now)
            )
            conn.commit()
            return cursor.lastrowid
