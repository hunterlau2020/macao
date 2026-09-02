"""Local Message Queue (agmsg SQLite Implementation with DLQ and Fan-Out Deliveries, PRD §11.6)."""

import json
import datetime
from typing import Optional, List, Dict, Any, Union

from macao.storage.db import get_db, DatabaseManager
from macao.core.types import AEPType
from macao.msg.envelope import AEPEnvelope


class MessageBus:
    """Provides publish/subscribe and queue mechanics for AEP messages."""

    def __init__(self, db_path: str = ".macao/state.db"):
        self.db = get_db(db_path)

    def _now(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def publish(
        self,
        msg_type: Union[AEPType, str],
        from_agent: str,
        to_agent: Union[str, List[str]],
        payload: Dict[str, Any],
        deadline: Optional[str] = None
    ) -> Dict[str, Any]:
        """Publishes an AEP message to the queue and creates per-recipient deliveries."""
        envelope = AEPEnvelope.create(msg_type, from_agent, to_agent, payload)
        now = self._now()

        recipients = to_agent if isinstance(to_agent, list) else [to_agent]
        to_str = json.dumps(recipients)
        payload_str = json.dumps(payload, ensure_ascii=False)

        with self.db.connection() as conn:
            # 1. Insert master message
            conn.execute(
                """
                INSERT INTO message_queue (message_id, type, from_agent, to_agent, payload, status, retry_count, deadline, created_at)
                VALUES (?, ?, ?, ?, ?, 'PENDING', 0, ?, ?)
                """,
                (envelope["message_id"], envelope["type"], from_agent, to_str, payload_str, deadline, now)
            )

            # 2. Insert per-recipient deliveries for independent ACK and fan-out
            for r in recipients:
                conn.execute(
                    """
                    INSERT INTO message_deliveries (message_id, recipient, status, retry_count, created_at)
                    VALUES (?, ?, 'PENDING', 0, ?)
                    """,
                    (envelope["message_id"], r, now)
                )

        return envelope

    def receive_pending(self, recipient: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves pending messages targeted at a specific recipient."""
        messages = []
        with self.db.connection() as conn:
            # Check direct recipient delivery or wildcard deliveries
            rows = conn.execute(
                """
                SELECT q.message_id, q.type, q.from_agent, q.to_agent, q.payload, q.created_at, d.status as delivery_status
                FROM message_deliveries d
                JOIN message_queue q ON d.message_id = q.message_id
                WHERE (d.recipient = ? OR d.recipient IN ('all', '*')) AND d.status = 'PENDING'
                ORDER BY d.created_at ASC LIMIT ?
                """,
                (recipient, limit)
            ).fetchall()

            for row in rows:
                recipients = json.loads(row["to_agent"])
                payload = json.loads(row["payload"])
                msg = {
                    "protocol": "AEP/1.1",
                    "message_id": row["message_id"],
                    "timestamp": row["created_at"],
                    "type": row["type"],
                    "from": row["from_agent"],
                    "to": recipients if len(recipients) > 1 else recipients[0],
                    "payload": payload,
                }
                messages.append(msg)

        return messages

    def ack(self, message_id: str, recipient: Optional[str] = None) -> bool:
        """Acknowledge message processing completion for a specific recipient or all."""
        now = self._now()
        with self.db.connection() as conn:
            if recipient:
                cursor = conn.execute(
                    "UPDATE message_deliveries SET status = 'ACKED', acked_at = ? WHERE message_id = ? AND recipient = ?",
                    (now, message_id, recipient)
                )
                acked_deliveries = cursor.rowcount > 0
            else:
                cursor = conn.execute(
                    "UPDATE message_deliveries SET status = 'ACKED', acked_at = ? WHERE message_id = ?",
                    (now, message_id)
                )
                acked_deliveries = cursor.rowcount > 0

            # Check if all deliveries are ACKed
            pending = conn.execute(
                "SELECT COUNT(*) FROM message_deliveries WHERE message_id = ? AND status = 'PENDING'",
                (message_id,)
            ).fetchone()[0]

            if pending == 0:
                conn.execute(
                    "UPDATE message_queue SET status = 'ACKED', acked_at = ? WHERE message_id = ?",
                    (now, message_id)
                )

            return acked_deliveries

    def fail_to_dlq(self, message_id: str, reason: str) -> None:
        """Moves an unprocessable/expired message to Dead Letter Queue."""
        now = self._now()
        with self.db.connection() as conn:
            row = conn.execute("SELECT * FROM message_queue WHERE message_id = ?", (message_id,)).fetchone()
            if row:
                conn.execute(
                    """
                    INSERT INTO dead_letter_queue (message_id, type, payload, retry_count, reason, ts)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(message_id) DO UPDATE SET
                    retry_count = retry_count + 1, reason = excluded.reason, ts = excluded.ts
                    """,
                    (message_id, row["type"], row["payload"], row["retry_count"] + 1, reason, now)
                )
                conn.execute("UPDATE message_queue SET status = 'DEAD' WHERE message_id = ?", (message_id,))
                conn.execute("UPDATE message_deliveries SET status = 'DEAD' WHERE message_id = ?", (message_id,))
