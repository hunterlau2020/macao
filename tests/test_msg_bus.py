"""Unit tests for MessageBus and AEPEnvelope (PRD §2.4 / §11.6)."""

import os
import unittest
import tempfile
from macao.core.types import AEPType
from macao.msg.envelope import AEPEnvelope
from macao.msg.bus import MessageBus


class TestMessageBus(unittest.TestCase):

    def test_aep_envelope_creation(self):
        env = AEPEnvelope.create(
            msg_type=AEPType.DEVELOPMENT_STARTED,
            from_agent="macao",
            to_agent="cc-ds4",
            payload={
                "task_id": "task-1",
                "specification_summary": "Build FSM",
                "acceptance_criteria": ["Pass all tests"]
            }
        )
        self.assertEqual(env["protocol"], "AEP/1.1")
        self.assertEqual(env["type"], "DEVELOPMENT_STARTED")
        self.assertTrue(env["message_id"].startswith("msg-"))

    def test_aep_disposition_required_type(self):
        self.assertEqual(AEPType.DISPOSITION_REQUIRED.value, "DISPOSITION_REQUIRED")
        env = AEPEnvelope.create(
            msg_type=AEPType.DISPOSITION_REQUIRED,
            from_agent="macao",
            to_agent="cc-ds4",
            payload={
                "task_id": "task-1",
                "checkpoint_ref": "c1a2b3d",
                "review_round": 1,
                "vote_result_ref": {
                    "path": ".macao/vote_result.json",
                    "evidence_commit": "c1a2b3d",
                    "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
                },
                "issues_index_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                "timeout_deadline": "2026-09-01T12:00:00Z"
            }
        )
        self.assertEqual(env["type"], "DISPOSITION_REQUIRED")
        self.assertEqual(env["protocol"], "AEP/1.1")

    def test_aep_byte_budget_enforcement(self):
        # 1. Total envelope exceeds 16384 bytes -> MUST raise ValueError
        large_summary = "A" * 15000
        # Field over 2048 bytes -> MUST raise ValueError
        with self.assertRaises(ValueError):
            AEPEnvelope.create(
                msg_type=AEPType.DEVELOPMENT_STARTED,
                from_agent="macao",
                to_agent="cc-ds4",
                payload={
                    "task_id": "task-1",
                    "specification_summary": "A" * 2049,
                    "acceptance_criteria": ["Pass all tests"]
                }
            )

        # CJK multi-byte boundary: 700 chinese chars is 2100 bytes (> 2048 bytes) -> MUST raise ValueError
        with self.assertRaises(ValueError):
            AEPEnvelope.create(
                msg_type=AEPType.DEVELOPMENT_STARTED,
                from_agent="macao",
                to_agent="cc-ds4",
                payload={
                    "task_id": "task-1",
                    "specification_summary": "中" * 700,
                    "acceptance_criteria": ["Pass all tests"]
                }
            )

    def test_aep_backward_compatible_parse(self):
        msg_v1 = {
            "protocol": "AEP/1.0",
            "message_id": "msg-20260901-00000001",
            "timestamp": "2026-09-01T10:00:00Z",
            "type": "DEVELOPMENT_STARTED",
            "from": "macao",
            "to": "cc-ds4",
            "payload": {
                "task_id": "task-1",
                "specification_summary": "Legacy AEP 1.0 message",
                "acceptance_criteria": ["Pass tests"]
            }
        }
        valid, err = AEPEnvelope.parse(msg_v1)
        self.assertTrue(valid, f"Failed to parse AEP/1.0 legacy message: {err}")

    def test_message_bus_fanout_independent_ack(self):
        """Verify that multiple recipients receiving a broadcast have independent ACK states."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            bus = MessageBus(db_path)

            # Publish to 2 reviewers
            published = bus.publish(
                msg_type=AEPType.DEVELOPMENT_STARTED,
                from_agent="macao",
                to_agent=["cc-glm", "kimi"],
                payload={
                    "task_id": "task-1",
                    "specification_summary": "Build FSM",
                    "acceptance_criteria": ["Pass all tests"]
                }
            )
            msg_id = published["message_id"]

            # Both should see pending
            self.assertEqual(len(bus.receive_pending("cc-glm")), 1)
            self.assertEqual(len(bus.receive_pending("kimi")), 1)

            # cc-glm ACKs its delivery
            self.assertTrue(bus.ack(msg_id, recipient="cc-glm"))

            # cc-glm has 0 pending, but kimi MUST STILL HAVE 1 pending!
            self.assertEqual(len(bus.receive_pending("cc-glm")), 0)
            self.assertEqual(len(bus.receive_pending("kimi")), 1)

            # kimi ACKs
            self.assertTrue(bus.ack(msg_id, recipient="kimi"))
            self.assertEqual(len(bus.receive_pending("kimi")), 0)


if __name__ == "__main__":
    unittest.main()
