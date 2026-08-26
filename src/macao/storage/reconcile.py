"""Crash Recovery and State Reconciliation Protocol (PRD §11.5)."""

import os
from pathlib import Path
from typing import Dict, Any, Optional

from macao.core.types import AgentState
from macao.storage.store import StateStore
from macao.core.schema import validate_dev_manifest, validate_vote_result


class StateReconciler:
    """Reconciles memory/SQLite state against physical disk artifacts and Git history."""

    def __init__(self, store: StateStore, project_root: str = "."):
        self.store = store
        self.root = Path(project_root)

    def reconcile(self) -> Optional[Dict[str, Any]]:
        """Scans physical .macao artifacts and repairs StateStore if crash occurred."""
        task = self.store.get_active_task()
        if not task:
            return None

        task_id = task["task_id"]
        current_st = AgentState(task["state"])
        ref = task.get("checkpoint_ref")
        rnd = task.get("review_round", 1)

        reconcile_notes = []

        # 1. Check if vote_result.json exists on disk
        vote_result_file = self.root / ".macao" / "vote_result.json"
        if vote_result_file.exists():
            try:
                import json
                with open(vote_result_file, "r") as f:
                    vdata = json.load(f)
                is_valid, _ = validate_vote_result(vdata)
                if is_valid and vdata.get("review_round") == rnd:
                    decision = vdata.get("decision")
                    target_st = AgentState.MERGING if decision == "APPROVED" else AgentState.REWORK
                    if current_st != target_st:
                        self.store.update_task_state(task_id, target_st, ref, rnd)
                        reconcile_notes.append(f"Reconciled state to {target_st} from physical vote_result.json")
            except Exception as e:
                reconcile_notes.append(f"Failed to parse vote_result.json during reconcile: {e}")

        # 2. Check if .dev.yml exists on disk and unconsumed
        dev_file = self.root / ".macao" / ".dev.yml"
        if dev_file.exists() and current_st in (AgentState.CODING, AgentState.REWORK):
            try:
                import yaml
                with open(dev_file, "r") as f:
                    ddata = yaml.safe_load(f)
                is_valid, _ = validate_dev_manifest(ddata)
                if is_valid and ddata.get("review_round", 1) == rnd and ddata.get("status") == "ready_for_review":
                    commit = ddata.get("development", {}).get("git", {}).get("latest_commit")
                    if current_st != AgentState.READY_FOR_REVIEW:
                        self.store.update_task_state(task_id, AgentState.READY_FOR_REVIEW, commit, rnd)
                        reconcile_notes.append(f"Reconciled state to READY_FOR_REVIEW from unconsumed .dev.yml ({commit})")
            except Exception as e:
                reconcile_notes.append(f"Failed to parse .dev.yml during reconcile: {e}")

        if reconcile_notes:
            self.store.log_audit_event(task_id, "CRASH_RECONCILE", {"actions": reconcile_notes})

        return self.store.get_task(task_id)
