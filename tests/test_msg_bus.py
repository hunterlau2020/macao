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
        self.assertEqual(env["protocol"], "AEP/1.0")
        self.assertEqual(env["type"], "DEVELOPMENT_STARTED")
        self.assertTrue(env["message_id"].startswith("msg-"))

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
