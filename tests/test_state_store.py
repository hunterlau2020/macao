"""Unit tests for StateStore and SQLite integration (PRD §11.4)."""

import os
import unittest
import tempfile
from macao.core.types import AgentState
from macao.storage.store import StateStore


class TestStateStore(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_state.db")
        self.store = StateStore(self.db_path)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_state_store_task_lifecycle(self):
        task = self.store.create_task(
            task_id="task-001",
            title="Implement Redis caching",
            source_branch="feature/redis",
            target_branch="main"
        )
        self.assertEqual(task["task_id"], "task-001")
        self.assertEqual(task["state"], AgentState.IDLE.value)
        self.assertEqual(task["review_round"], 1)

        # Update state
        self.store.update_task_state(
            task_id="task-001",
            state=AgentState.CODING,
            checkpoint_ref="a1b2c3d",
            review_round=1
        )
        updated = self.store.get_task("task-001")
        self.assertEqual(updated["state"], AgentState.CODING.value)
        self.assertEqual(updated["checkpoint_ref"], "a1b2c3d")

    def test_artifact_registration_and_append_semantics(self):
        self.store.create_task("task-002", "Feature X", "feat", "main")

        # 1. Register artifact
        dummy_file = os.path.join(self.tmpdir, "test.dev.yml")
        with open(dummy_file, "w") as f:
            f.write("test_content: true")

        self.store.register_artifact(
            task_id="task-002",
            kind="dev_manifest",
            checkpoint_ref="c001",
            review_round=1,
            path=dummy_file
        )

        artifacts = self.store.list_artifacts("task-002", review_round=1)
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0]["consumed"], 0)
        self.assertIn("artifact_id", artifacts[0])

        # 2. Mark consumed
        self.store.mark_artifact_consumed(
            task_id="task-002",
            kind="dev_manifest",
            checkpoint_ref="c001",
            review_round=1,
            archived_path=".macao/archive/c001/r1/.dev.yml"
        )
        consumed_artifacts = self.store.list_artifacts("task-002", review_round=1)
        self.assertEqual(consumed_artifacts[0]["consumed"], 1)
        self.assertEqual(consumed_artifacts[0]["archived_path"], ".macao/archive/c001/r1/.dev.yml")

        # 3. Non-destructive update: re-registering does not wipe consumed=1 back to 0
        self.store.register_artifact(
            task_id="task-002",
            kind="dev_manifest",
            checkpoint_ref="c001",
            review_round=1,
            path=dummy_file
        )
        preserved = self.store.list_artifacts("task-002", review_round=1)
        self.assertEqual(preserved[0]["consumed"], 1)
        self.assertEqual(preserved[0]["archived_path"], ".macao/archive/c001/r1/.dev.yml")


if __name__ == "__main__":
    unittest.main()
