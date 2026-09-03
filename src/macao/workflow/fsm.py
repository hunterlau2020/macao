"""FSM Orchestration Engine (PRD §3.1 / §3.3)."""

import shutil
import hashlib
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
        """Executes a validated state transition enforcing TransitionTable rules."""
        task = self.store.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        from_state = AgentState(task["state"])
        ref = task.get("checkpoint_ref")
        rnd = task.get("review_round", 1)

        # Enforce unified transition table whitelist
        if not TransitionTable.can_transition(from_state, to_state, trigger_id):
            self.store.log_audit_event(task_id, "TRANSITION_REJECTED", {
                "from_state": from_state.value,
                "to_state": to_state.value,
                "trigger_id": trigger_id,
                "detail": detail
            })
            raise ValueError(
                f"Illegal state transition from {from_state.value} to {to_state.value} via trigger {trigger_id}"
            )

        # Update State Store
        new_ref = (detail.get("latest_commit") or detail.get("checkpoint_ref") or ref) if detail else ref
        new_rnd = rnd

        # Advance round if moving to REWORK
        if to_state == AgentState.REWORK and from_state != AgentState.REWORK:
            new_rnd = rnd + 1

        self.store.update_task_state(task_id, to_state, checkpoint_ref=new_ref, review_round=new_rnd)

        # Log event
        change = StateChange(
            task_id=task_id,
            from_state=from_state,
            to_state=to_state,
            trigger=trigger_id,
            review_round=new_rnd,
            checkpoint_ref=new_ref,
            note=detail.get("note") if detail else None
        )
        self.store.log_audit_event(task_id, f"STATE_TRANSITION_{trigger_id}", {
            "from_state": from_state.value,
            "to_state": to_state.value,
            "checkpoint_ref": new_ref,
            "review_round": new_rnd,
            "detail": detail
        })

        # Archive logic (PRD §3.4 / §11.4 / P1-NEW-9)
        if trigger_id == "E2" and ref:
            self._archive_file(".macao/.dev.yml", ref, rnd, task_id, "dev_manifest")
        elif trigger_id in ("E4", "E5", "E7", "E9", "E10") and ref:
            self._archive_file(".macao/vote_result.json", ref, rnd, task_id, "vote_result")
            self._archive_reviews(ref, rnd, task_id)
        elif trigger_id in ("E4a", "E4b") and ref:
            self._archive_file(".macao/vote_result.json", ref, rnd, task_id, "vote_result")

        return change

    def _get_generation(self, task_id: str, review_round: int) -> int:
        try:
            dispatches = self.store.get_audit_events_by_type(task_id, "REVIEW_REQUESTS_DISPATCHED", review_round=review_round)
            return len(dispatches) if dispatches else 1
        except Exception:
            return 1

    def _archive_file(self, rel_path: str, checkpoint_ref: str, review_round: int, task_id: str, kind: str) -> None:
        src = self.root / rel_path
        if src.exists():
            gen = self._get_generation(task_id, review_round)
            archive_dir = self.root / ".macao" / "archive" / checkpoint_ref / f"r{review_round}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            dst = archive_dir / src.name

            # Non-destructive archiving (P1-NEW-9): preserve distinct generation artifacts
            if dst.exists():
                src_hash = hashlib.sha256(src.read_bytes()).hexdigest()
                dst_hash = hashlib.sha256(dst.read_bytes()).hexdigest()
                if src_hash != dst_hash:
                    dst = archive_dir / f"g{gen}_{src.name}"

            shutil.copy2(src, dst)
            archived_rel = str(dst.relative_to(self.root))
            self.store.mark_artifact_consumed(
                task_id=task_id,
                kind=kind,
                checkpoint_ref=checkpoint_ref,
                review_round=review_round,
                archived_path=archived_rel
            )
            sha256 = hashlib.sha256(dst.read_bytes()).hexdigest() if dst.exists() else ""
            self.store.log_audit_event(
                task_id=task_id,
                event_type="ARTIFACT_ARCHIVED",
                detail={
                    "kind": kind,
                    "checkpoint_ref": checkpoint_ref,
                    "review_round": review_round,
                    "generation": gen,
                    "archived_path": archived_rel,
                    "sha256": sha256
                }
            )

    def _archive_reviews(self, checkpoint_ref: str, review_round: int, task_id: str) -> None:
        reviews_dir = self.root / ".macao" / ".reviews"
        if reviews_dir.exists():
            gen = self._get_generation(task_id, review_round)
            archive_dir = self.root / ".macao" / "archive" / checkpoint_ref / f"r{review_round}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            for rev_file in sorted(reviews_dir.glob("*.review.yml")):
                dst = archive_dir / rev_file.name
                if dst.exists():
                    src_hash = hashlib.sha256(rev_file.read_bytes()).hexdigest()
                    dst_hash = hashlib.sha256(dst.read_bytes()).hexdigest()
                    if src_hash != dst_hash:
                        dst = archive_dir / f"g{gen}_{rev_file.name}"

                shutil.copy2(rev_file, dst)
                reviewer_id = rev_file.name.replace(".review.yml", "")
                archived_rel = str(dst.relative_to(self.root))
                self.store.mark_artifact_consumed(
                    task_id=task_id,
                    kind="review_manifest",
                    checkpoint_ref=checkpoint_ref,
                    review_round=review_round,
                    archived_path=archived_rel,
                    reviewer_id=reviewer_id
                )
                sha256 = hashlib.sha256(dst.read_bytes()).hexdigest() if dst.exists() else ""
                self.store.log_audit_event(
                    task_id=task_id,
                    event_type="ARTIFACT_ARCHIVED",
                    detail={
                        "kind": "review_manifest",
                        "checkpoint_ref": checkpoint_ref,
                        "review_round": review_round,
                        "reviewer_id": reviewer_id,
                        "generation": gen,
                        "archived_path": archived_rel,
                        "sha256": sha256
                    }
                )
