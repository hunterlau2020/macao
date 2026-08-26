"""Unit tests for WorkflowFSM and TransitionTable (PRD §3.3)."""

import os
import unittest
import tempfile
from macao.core.types import AgentState
from macao.storage.store import StateStore
from macao.workflow.fsm import WorkflowFSM
from macao.workflow.transitions import TransitionTable


class TestWorkflowFSM(unittest.TestCase):

    def test_transition_rules(self):
        self.assertTrue(TransitionTable.can_transition(AgentState.IDLE, AgentState.CODING, "E1"))
        self.assertTrue(TransitionTable.can_transition(AgentState.READY_FOR_REVIEW, AgentState.WAITING_REVIEW, "E2"))
        self.assertTrue(TransitionTable.can_transition(AgentState.WAITING_REVIEW, AgentState.CONSENSUS_CHECK, "E3"))
        self.assertTrue(TransitionTable.can_transition(AgentState.CONSENSUS_CHECK, AgentState.MERGING, "E4"))
        self.assertTrue(TransitionTable.can_transition(AgentState.MERGING, AgentState.DONE, "E4a"))
        self.assertTrue(TransitionTable.can_transition(AgentState.MERGING, AgentState.REWORK, "E4b"))
        self.assertTrue(TransitionTable.can_transition(AgentState.CONSENSUS_CHECK, AgentState.WAITING_REVIEW, "E9"))
        self.assertTrue(TransitionTable.can_transition(AgentState.CODING, AgentState.CANCELLED, "E10"))

    def test_fsm_transition_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            store = StateStore(db_path)
            store.create_task("t1", "Task 1", "f1", "main")

            fsm = WorkflowFSM(store, project_root=tmpdir)

            # IDLE -> CODING (E1)
            fsm.transition("t1", AgentState.CODING, "E1")
            self.assertEqual(store.get_task("t1")["state"], AgentState.CODING.value)

            # CODING -> READY_FOR_REVIEW
            fsm.transition("t1", AgentState.READY_FOR_REVIEW, "EXPLICIT_SIGNAL", {"latest_commit": "c1"})
            self.assertEqual(store.get_task("t1")["state"], AgentState.READY_FOR_REVIEW.value)
            self.assertEqual(store.get_task("t1")["checkpoint_ref"], "c1")

            # READY_FOR_REVIEW -> WAITING_REVIEW (E2)
            fsm.transition("t1", AgentState.WAITING_REVIEW, "E2")
            self.assertEqual(store.get_task("t1")["state"], AgentState.WAITING_REVIEW.value)

            # WAITING_REVIEW -> CONSENSUS_CHECK (E3)
            fsm.transition("t1", AgentState.CONSENSUS_CHECK, "E3")
            self.assertEqual(store.get_task("t1")["state"], AgentState.CONSENSUS_CHECK.value)

            # CONSENSUS_CHECK -> MERGING (E4)
            fsm.transition("t1", AgentState.MERGING, "E4")
            self.assertEqual(store.get_task("t1")["state"], AgentState.MERGING.value)

            # MERGING -> DONE (E4a)
            fsm.transition("t1", AgentState.DONE, "E4a")
            self.assertEqual(store.get_task("t1")["state"], AgentState.DONE.value)


if __name__ == "__main__":
    unittest.main()
