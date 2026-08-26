"""Unit tests for MessageBus and AEPEnvelope (PRD §2.4 / §11.6)."""

import os
import unittest
import tempfile
from macao.core.types import MessageType
from macao.msg.envelope import AEPEnvelope
from macao.msg.bus import MessageBus


class TestMessageBus(unittest.TestCase):

    def test_aep_envelope_creation(self):
        env = AEPEnvelope.create(
            msg_type=MessageType.DEVELOPMENT_STARTED,
            from_agent="macao",
            to_agent="cc-ds4",
            payload={"task_description": "Build FSM"}
        )
        self.assertEqual(env["protocol"], "AEP/1.0")
        self.assertEqual(env["type"], "DEVELOPMENT_STARTED")
        self.assertTrue(env["message_id"].startswith("msg-"))

    def test_message_bus_pub_sub_ack(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            bus = MessageBus(db_path)

            # Publish
            published = bus.publish(
                msg_type=MessageType.REVIEW_REQUEST,
                from_agent="macao",
                to_agent=["cc-glm", "kimi"],
                payload={"checkpoint_ref": "c1"}
            )
            msg_id = published["message_id"]

            # Receive for cc-glm
            pending = bus.receive_pending("cc-glm")
            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0]["message_id"], msg_id)

            # Receive for kimi
            pending_kimi = bus.receive_pending("kimi")
            self.assertEqual(len(pending_kimi), 1)

            # ACK
            ack_success = bus.ack(msg_id)
            self.assertTrue(ack_success)

            # Receive again should be empty
            self.assertEqual(len(bus.receive_pending("cc-glm")), 0)


if __name__ == "__main__":
    unittest.main()
