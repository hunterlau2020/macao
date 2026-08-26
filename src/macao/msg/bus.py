"""Local Message Queue (agmsg SQLite Implementation with DLQ, PRD §11.6)."""

import json
import datetime
from typing import Optional, List, Dict, Any, Union

from macao.storage.db import get_db, DatabaseManager
from macao.core.types import MessageType
from macao.msg.envelope import AEPEnvelope


class MessageBus:
    """Provides publish/subscribe and queue mechanics for AEP messages."""

    def __init__(self, db_path: str = ".macao/state.db"):
        self.db = get_db(db_path)

    def _now(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def publish(
        self,
        msg_type: Union[MessageType, str],
        from_agent: str,
        to_agent: Union[str, List[str]],
        payload: Dict[str, Any],
        deadline: Optional[str] = None
    ) -> Dict[str, Any]:
        """Publishes an AEP message to the queue."""
        envelope = AEPEnvelope.create(msg_type, from_agent, to_agent, payload)
        now = self._now()

        to_str = json.dumps(to_agent) if isinstance(to_agent, list) else json.dumps([to_agent])
        payload_str = json.dumps(payload, ensure_ascii=False)

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO message_queue (message_id, type, from_agent, to_agent, payload, status, retry_count, deadline, created_at)
                VALUES (?, ?, ?, ?, ?, 'PENDING', 0, ?, ?)
                """,
                (envelope["message_id"], envelope["type"], from_agent, to_str, payload_str, deadline, now)
            )
            conn.commit()

        return envelope

    def receive_pending(self, recipient: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves pending messages targeted at a specific recipient."""
        messages = []
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM message_queue WHERE status = 'PENDING' ORDER BY created_at ASC LIMIT ?",
                (limit * 3,)
            ).fetchall()

            for row in rows:
                recipients = json.loads(row["to_agent"])
                if recipient in recipients or "all" in recipients or "*" in recipients:
                    payload = json.loads(row["payload"])
                    msg = {
                        "protocol": "AEP/1.0",
                        "message_id": row["message_id"],
                        "timestamp": row["created_at"],
                        "type": row["type"],
                        "from": row["from_agent"],
                        "to": recipients if len(recipients) > 1 else recipients[0],
                        "payload": payload,
                    }
                    messages.append(msg)
                    if len(messages) >= limit:
                        break

        return messages

    def ack(self, message_id: str) -> bool:
        """Acknowledge message processing completion."""
        now = self._now()
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE message_queue SET status = 'ACKED', acked_at = ? WHERE message_id = ?",
                (now, message_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def fail_to_dlq(self, message_id: str, reason: str) -> None:
        """Moves an unprocessable/expired message to Dead Letter Queue."""
        now = self._now()
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM message_queue WHERE message_id = ?", (message_id,)).fetchone()
            if row:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO dead_letter_queue (message_id, type, payload, retry_count, reason, ts)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (message_id, row["type"], row["payload"], row["retry_count"] + 1, reason, now)
                )
                conn.execute("UPDATE message_queue SET status = 'DEAD' WHERE message_id = ?", (message_id,))
                conn.commit()
