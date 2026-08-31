"""MACAO Background Orchestration Daemon & Deadline Scanner (Phase 3 / PRD §6 & §14)."""

import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from macao.core.types import AgentState, Decision, Resolution, Vote
from macao.storage.store import StateStore
from macao.workflow.orchestrator import Orchestrator


class OrchestratorDaemon:
    """Monitors active task deadlines, handles background timeout degradation, and logs audit events."""

    def __init__(self, project_root: str = ".", poll_interval_sec: float = 2.0, poll_interval: Optional[float] = None):
        self.project_root = Path(project_root).resolve()
        self.store = StateStore(str(self.project_root / ".macao" / "state.db"))
        self.orchestrator = Orchestrator(str(self.project_root))
        self.poll_interval = poll_interval if poll_interval is not None else poll_interval_sec
        self.is_running = False


    def scan_once(self) -> Dict[str, Any]:
        """Executes a single pass over active tasks and evaluates timeout degradations."""
        task = self.store.get_active_task()
        if not task:
            return {"active_task": None, "action_taken": "NONE"}

        task_id = task["task_id"]
        state = task["state"]

        # Check if in WAITING_REVIEW and reviewer deadlines are exceeded
        if state == AgentState.WAITING_REVIEW.value:
            timed_out = self.orchestrator.detect_timed_out_reviewers(task_id)
            if timed_out:
                rnd = task.get("review_round", 1)
                ref = task.get("checkpoint_ref")

                for r_id in timed_out:
                    self.store.log_audit_event(task_id, "REVIEWER_TIMEOUT_ABSTAIN", {
                        "reviewer_id": r_id,
                        "review_round": rnd,
                        "checkpoint_ref": ref,
                        "note": "Reviewer deadline expired; recorded ABSTAIN"
                    })

                # Trigger consensus evaluation with timed_out_reviewers passed
                self.orchestrator.collect_and_evaluate_consensus(task_id, timed_out_reviewers=timed_out)
                return {
                    "active_task": task_id,
                    "state": self.store.get_task(task_id)["state"],
                    "action_taken": "TIMEOUT_DEGRADATION",
                    "timed_out_reviewers": timed_out
                }

        return {"active_task": task_id, "state": state, "action_taken": "NONE"}

    def run_loop(self, max_ticks: Optional[int] = None) -> None:
        """Runs the continuous daemon scanning loop."""
        import sys
        self.is_running = True
        ticks = 0
        while self.is_running:
            try:
                self.scan_once()
            except Exception as e:
                sys.stderr.write(f"[OrchestratorDaemon ERROR] {e}\n")

            ticks += 1
            if max_ticks and ticks >= max_ticks:
                break
            time.sleep(self.poll_interval)

    def stop(self) -> None:
        self.is_running = False
