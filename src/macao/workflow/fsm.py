"""FSM Orchestration Engine (PRD §3.1 / §3.3)."""

import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from macao.core.types import AgentState, StateChange
from macao.storage.store import StateStore
from macao.workflow.state_engine import StateRecognitionEngine
from macao.workflow.transitions import TransitionTable


class WorkflowFSM:
    """Orchestrates 10-state lifecycle progression for MACAO tasks."""

    def __init__(self, store: StateStore, project_root: str = "."):
        self.store = store
        self.root = Path(project_root)
        self.engine = StateRecognitionEngine(project_root)

    def transition(self, task_id: str, to_state: AgentState, trigger_id: str, detail: Optional[Dict[str, Any]] = None) -> StateChange:
        """Executes a validated state transition and archives artifacts if applicable."""
        task = self.store.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        from_state = AgentState(task["state"])
        ref = task.get("checkpoint_ref")
        rnd = task.get("review_round", 1)

        # Update State Store
        new_ref = detail.get("latest_commit", ref) if detail else ref
        new_rnd = rnd

        # Advance round if moving to REWORK
        if to_state == AgentState.REWORK and from_state != AgentState.REWORK:
            new_rnd = rnd + 1

        self.store.update_task_state(task_id, to_state, checkpoint_ref=new_ref, review_round=new_rnd)
        
        # Log event
        change = StateChange(
            from_state=from_state,
            to_state=to_state,
            source=trigger_id,
            transition_id=trigger_id,
            detail=detail
        )
        self.store.log_audit_event(task_id, f"STATE_TRANSITION_{trigger_id}", {
            "from_state": from_state.value,
            "to_state": to_state.value,
            "checkpoint_ref": new_ref,
            "review_round": new_rnd,
            "detail": detail
        })

        # Archive logic (PRD §3.4)
        if trigger_id == "E2" and ref:
            self._archive_file(".macao/.dev.yml", ref, rnd, task_id, "dev_manifest")
        elif trigger_id in ("E4a", "E4b") and ref:
            self._archive_file(".macao/vote_result.json", ref, rnd, task_id, "vote_result")

        return change

    def _archive_file(self, rel_path: str, checkpoint_ref: str, review_round: int, task_id: str, kind: str) -> None:
        src = self.root / rel_path
        if src.exists():
            archive_dir = self.root / ".macao" / "archive" / checkpoint_ref / f"r{review_round}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            dst = archive_dir / src.name
            shutil.copy2(src, dst)
            self.store.mark_artifact_consumed(
                task_id=task_id,
                kind=kind,
                checkpoint_ref=checkpoint_ref,
                review_round=review_round,
                archived_path=str(dst.relative_to(self.root))
            )

    def step(self, task_id: str, configured_reviewers: int = 2) -> Optional[StateChange]:
        """Observes disk artifacts and executes step transition if explicit signal is ready."""
        task = self.store.get_task(task_id)
        if not task:
            return None

        current_st = AgentState(task["state"])
        ref = task.get("checkpoint_ref")
        rnd = task.get("review_round", 1)

        target_st, src, meta = self.engine.recognize_state(current_st, ref, rnd, configured_reviewers)
        if target_st:
            # Map recognition to transition trigger ID
            trigger_map = {
                (AgentState.CODING, AgentState.READY_FOR_REVIEW): "E1_PRODUCED",
                (AgentState.REWORK, AgentState.READY_FOR_REVIEW): "E6",
                (AgentState.WAITING_REVIEW, AgentState.CONSENSUS_CHECK): "E3",
                (AgentState.CONSENSUS_CHECK, AgentState.MERGING): "E4",
                (AgentState.CONSENSUS_CHECK, AgentState.REWORK): "E5",
            }
            tr_id = trigger_map.get((current_st, target_st), "EXPLICIT_STEP")
            return self.transition(task_id, target_st, tr_id, meta)

        return None
