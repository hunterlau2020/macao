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

    def __init__(self, project_root: str = ".", poll_interval_sec: float = 2.0):
        self.project_root = Path(project_root).resolve()
        self.store = StateStore(str(self.project_root / ".macao" / "state.db"))
        self.orchestrator = Orchestrator(str(self.project_root))
        self.poll_interval = poll_interval_sec
        self.is_running = False

    def scan_once(self) -> Dict[str, Any]:
        """Executes a single pass over active tasks and evaluates timeout degradations."""
        task = self.store.get_active_task()
        if not task:
            return {"active_task": None, "action_taken": "NONE"}

        task_id = task["task_id"]
        state = task["state"]

        # Check if in WAITING_REVIEW and reviewer deadlines are recorded
        if state == AgentState.WAITING_REVIEW.value:
            events = self.store.get_audit_events(task_id, limit=50)
            now = time.time()

            # Find dispatch event
            dispatch_event = next((e for e in events if e["event_type"] == "REVIEW_DISPATCHED"), None)
            if dispatch_event:
                payload = json.loads(dispatch_event["payload"]) if isinstance(dispatch_event["payload"], str) else dispatch_event["payload"]
                deadline = payload.get("deadline_epoch", 0)
                reviewers = payload.get("reviewers", [])

                if deadline > 0 and now >= deadline:
                    # Deadline expired! Check which reviewers haven't submitted .review.yml
                    artifacts = self.store.list_artifacts(task_id)
                    submitted_reviewers = {
                        a["kind"].split(".")[0] for a in artifacts if a["kind"].endswith(".review.yml")
                    }

                    timed_out_reviewers = [r for r in reviewers if r not in submitted_reviewers]
                    if timed_out_reviewers:
                        for r_id in timed_out_reviewers:
                            self.store.log_audit_event(task_id, "REVIEWER_TIMEOUT_ABSTAIN", {
                                "reviewer_id": r_id,
                                "review_round": task.get("review_round", 1),
                                "checkpoint_ref": task.get("checkpoint_ref")
                            })

                        # Trigger consensus evaluation to enter HOLD / HUMAN_OVERRIDE
                        self.orchestrator.collect_and_evaluate_consensus(task_id)
                        return {
                            "active_task": task_id,
                            "action_taken": "TIMEOUT_DEGRADATION",
                            "timed_out_reviewers": timed_out_reviewers
                        }

        return {"active_task": task_id, "state": state, "action_taken": "NONE"}

    def run_loop(self, max_ticks: Optional[int] = None) -> None:
        """Runs the continuous daemon scanning loop."""
        self.is_running = True
        ticks = 0
        while self.is_running:
            try:
                self.scan_once()
            except Exception:
                pass

            ticks += 1
            if max_ticks and ticks >= max_ticks:
                break
            time.sleep(self.poll_interval)

    def stop(self) -> None:
        self.is_running = False
