"""Unit tests for SQLite StateStore and Reconcile (PRD §11.4 / §11.5)."""

import os
import unittest
import tempfile
from pathlib import Path
from macao.core.types import AgentState
from macao.storage.store import StateStore
from macao.storage.reconcile import StateReconciler


class TestStateStore(unittest.TestCase):

    def test_state_store_task_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            store = StateStore(db_path)

            task = store.create_task("task-001", "Test Feature", "feat/1", "main")
            self.assertEqual(task["task_id"], "task-001")
            self.assertEqual(task["state"], AgentState.IDLE.value)

            store.update_task_state("task-001", AgentState.CODING, checkpoint_ref="commit-1", review_round=1)
            updated = store.get_task("task-001")
            self.assertEqual(updated["state"], AgentState.CODING.value)
            self.assertEqual(updated["checkpoint_ref"], "commit-1")

            # Log audit event
            seq_id = store.log_audit_event("task-001", "TEST_EVENT", {"k": "v"})
            self.assertGreater(seq_id, 0)
            events = store.list_audit_events("task-001")
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["type"], "TEST_EVENT")

            # Overrides
            ov_id = store.record_override("task-001", "DEADLOCK", "APPROVED", "Manual approve")
            self.assertGreater(ov_id, 0)

    def test_artifact_registration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            store = StateStore(db_path)

            store.register_artifact(
                task_id="task-001",
                kind="dev_manifest",
                checkpoint_ref="c1",
                review_round=1,
                path=".macao/.dev.yml"
            )
            artifacts = store.list_artifacts("task-001")
            self.assertEqual(len(artifacts), 1)
            self.assertEqual(artifacts[0]["kind"], "dev_manifest")

            store.mark_artifact_consumed("task-001", "dev_manifest", "c1", 1, ".macao/archive/c1/r1/.dev.yml")
            artifacts_updated = store.list_artifacts("task-001")
            self.assertEqual(artifacts_updated[0]["consumed"], 1)


if __name__ == "__main__":
    unittest.main()
