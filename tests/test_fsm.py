"""Unit tests for WorkflowFSM and TransitionTable (PRD §3.1 / §3.3)."""

import os
import unittest
import tempfile
from macao.core.types import AgentState
from macao.storage.store import StateStore
from macao.workflow.fsm import WorkflowFSM
from macao.workflow.transitions import TransitionTable


class TestWorkflowFSM(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "state.db")
        self.store = StateStore(self.db_path)
        self.fsm = WorkflowFSM(self.store, self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_transition_rules_and_whitelist_enforcement(self):
        # 1. Valid transitions
        self.assertTrue(TransitionTable.can_transition(AgentState.IDLE, AgentState.CODING, "E1"))
        self.assertTrue(TransitionTable.can_transition(AgentState.CODING, AgentState.READY_FOR_REVIEW, "E1_PRODUCED"))
        self.assertTrue(TransitionTable.can_transition(AgentState.READY_FOR_REVIEW, AgentState.WAITING_REVIEW, "E2"))
        self.assertTrue(TransitionTable.can_transition(AgentState.WAITING_REVIEW, AgentState.CONSENSUS_CHECK, "E3"))
        self.assertTrue(TransitionTable.can_transition(AgentState.CONSENSUS_CHECK, AgentState.MERGING, "E4"))
        self.assertTrue(TransitionTable.can_transition(AgentState.MERGING, AgentState.DONE, "E4a"))
        self.assertTrue(TransitionTable.can_transition(AgentState.MERGING, AgentState.REWORK, "E4b"))
        self.assertTrue(TransitionTable.can_transition(AgentState.CONSENSUS_CHECK, AgentState.REWORK, "E5"))
        self.assertTrue(TransitionTable.can_transition(AgentState.REWORK, AgentState.READY_FOR_REVIEW, "E6"))
        self.assertTrue(TransitionTable.can_transition(AgentState.CODING, AgentState.CANCELLED, "E10"))

        # 2. Invalid transitions (must return False)
        self.assertFalse(TransitionTable.can_transition(AgentState.IDLE, AgentState.DONE, "E1"))
        self.assertFalse(TransitionTable.can_transition(AgentState.WAITING_REVIEW, AgentState.MERGING, "E4"))
        self.assertFalse(TransitionTable.can_transition(AgentState.DONE, AgentState.CANCELLED, "E10"))
        self.assertFalse(TransitionTable.can_transition(AgentState.CANCELLED, AgentState.CODING, "E1"))

    def test_fsm_transition_lifecycle_and_rejection(self):
        task = self.store.create_task("task-1", "Feature A", "feat", "main")
        self.assertEqual(task["state"], AgentState.IDLE.value)

        # E1: IDLE -> CODING
        change = self.fsm.transition("task-1", AgentState.CODING, "E1")
        self.assertEqual(change.to_state, AgentState.CODING)

        # Illegal Transition: CODING -> DONE via E4a (Must raise ValueError)
        with self.assertRaises(ValueError):
            self.fsm.transition("task-1", AgentState.DONE, "E4a")

        # Legal E1_PRODUCED: CODING -> READY_FOR_REVIEW
        change = self.fsm.transition("task-1", AgentState.READY_FOR_REVIEW, "E1_PRODUCED", {"latest_commit": "c1"})
        self.assertEqual(change.to_state, AgentState.READY_FOR_REVIEW)


if __name__ == "__main__":
    unittest.main()
