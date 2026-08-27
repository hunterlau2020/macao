"""MACAO Core Orchestrator Engine (PRD §11.1 / §11.2)."""

import os
import uuid
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from macao.core.types import (
    AgentState,
    MessageType,
    Decision,
    Resolution,
    OverrideChoice,
    StateChange,
)
from macao.storage.store import StateStore
from macao.storage.reconcile import StateReconciler
from macao.msg.bus import MessageBus
from macao.workflow.fsm import WorkflowFSM
from macao.consensus.engine import ConsensusEngine
from macao.consensus.vote import VoteAggregator
from macao.utils.git_utils import GitManager
from macao.utils.context_builder import ReviewContextBuilder
from macao.adapter.base import AgentAdapter


class Orchestrator:
    """
    Core single-process event loop and workflow orchestrator.
    Coordinates FSM, Adapters, Consensus, Worktrees, and Storage.
    """

    def __init__(
        self,
        project_root: str = ".",
        db_path: str = ".macao/state.db",
        executor_adapter: Optional[AgentAdapter] = None,
        reviewer_adapters: Optional[List[AgentAdapter]] = None
    ):
        self.root = Path(project_root).resolve()
        self.store = StateStore(db_path)
        self.msg_bus = MessageBus(db_path)
        self.fsm = WorkflowFSM(self.store, project_root=str(self.root))
        self.reconciler = StateReconciler(self.store, project_root=str(self.root))
        self.vote_aggregator = VoteAggregator(project_root=str(self.root))
        self.git = GitManager(str(self.root))

        self.executor = executor_adapter
        self.reviewers = reviewer_adapters or []

    def start_task(
        self,
        title: str,
        task_description: str,
        acceptance_criteria: Dict[str, Any],
        source_branch: str = "feature/new-task",
        target_branch: str = "main",
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """E1: IDLE -> CODING. Initializes task and dispatches DEVELOPMENT_STARTED."""
        tid = task_id or f"task-{uuid.uuid4().hex[:6]}"
        task = self.store.create_task(tid, title, source_branch, target_branch)

        # Transition FSM to CODING (E1)
        self.fsm.transition(tid, AgentState.CODING, "E1", {"title": title, "branch": source_branch})

        # Publish AEP message: DEVELOPMENT_STARTED
        exec_id = self.executor.agent_id if self.executor else "cc-ds4"
        payload = {
            "task_id": tid,
            "task_description": task_description,
            "success_criteria": acceptance_criteria,
            "source_branch": source_branch,
            "target_branch": target_branch
        }
        self.msg_bus.publish(
            msg_type=MessageType.DEVELOPMENT_STARTED,
            from_agent="macao",
            to_agent=exec_id,
            payload=payload
        )

        # Inject task into executor adapter if present
        if self.executor:
            self.executor.inject_task(payload)

        return self.store.get_task(tid)

    def check_development_checkpoint(self, task_id: str) -> Optional[StateChange]:
        """Checks for valid .dev.yml and transitions CODING/REWORK -> READY_FOR_REVIEW."""
        task = self.store.get_task(task_id)
        if not task:
            return None

        current_st = AgentState(task["state"])
        if current_st not in (AgentState.CODING, AgentState.REWORK):
            return None

        rnd = task.get("review_round", 1)
        target_st, src, meta = self.fsm.engine.recognize_state(current_st, None, rnd)
        if target_st == AgentState.READY_FOR_REVIEW:
            tr_id = "E1_PRODUCED" if current_st == AgentState.CODING else "E6"
            change = self.fsm.transition(task_id, AgentState.READY_FOR_REVIEW, tr_id, meta)
            
            # Register physical artifact
            dev_path = str((self.root / ".macao" / ".dev.yml").relative_to(self.root))
            self.store.register_artifact(
                task_id=task_id,
                kind="dev_manifest",
                checkpoint_ref=meta.get("latest_commit", ""),
                review_round=rnd,
                path=dev_path
            )
            return change
        return None

    def dispatch_review_requests(self, task_id: str) -> Optional[StateChange]:
        """E2: READY_FOR_REVIEW -> WAITING_REVIEW. Consumes .dev.yml, creates worktrees, sends REVIEW_REQUEST."""
        task = self.store.get_task(task_id)
        if not task or AgentState(task["state"]) != AgentState.READY_FOR_REVIEW:
            return None

        checkpoint_ref = task["checkpoint_ref"]
        rnd = task.get("review_round", 1)
        if not checkpoint_ref:
            raise ValueError("Cannot dispatch reviews without a valid checkpoint_ref")

        # 1. Transition FSM (E2) and archive .dev.yml
        change = self.fsm.transition(task_id, AgentState.WAITING_REVIEW, "E2")

        # 2. Build review_context
        ctx_builder = ReviewContextBuilder(
            task_description=task.get("title", ""),
            base_commit=task.get("target_branch", "main"),
            head_commit=checkpoint_ref,
            workspace_path=str(self.root)
        )
        review_context = ctx_builder.build()

        # 3. For each reviewer, create isolated worktree and publish AEP REVIEW_REQUEST
        rev_ids = [r.agent_id for r in self.reviewers] if self.reviewers else ["cc-glm", "kimi"]
        for rev_id in rev_ids:
            worktree_path = None
            try:
                if self.git.commit_exists(checkpoint_ref):
                    worktree_path = self.git.create_isolated_worktree(rev_id, task_id, rnd, checkpoint_ref)
            except Exception:
                pass

            payload = {
                "checkpoint_ref": checkpoint_ref,
                "review_round": rnd,
                "review_context": review_context,
                "isolated_worktree_path": str(worktree_path) if worktree_path else str(self.root)
            }

            self.msg_bus.publish(
                msg_type=MessageType.REVIEW_REQUEST,
                from_agent="macao",
                to_agent=rev_id,
                payload=payload
            )

        # 4. Inject into reviewer adapters if present
        for r_adapter in self.reviewers:
            r_adapter.inject_task({
                "checkpoint_ref": checkpoint_ref,
                "review_round": rnd,
                "review_context": review_context
            })

        return change

    def collect_and_evaluate_consensus(self, task_id: str, configured_reviewers: int = 2) -> Tuple[Optional[StateChange], Optional[Dict[str, Any]]]:
        """
        E3: WAITING_REVIEW -> CONSENSUS_CHECK.
        Evaluates 2/3 majority consensus, synthesizes vote_result.json, and branches:
          - APPROVED -> MERGING (E4)
          - REWORK_REQUIRED -> REWORK (E5)
          - DEADLOCK -> dispatches HUMAN_OVERRIDE_REQUEST (waits in CONSENSUS_CHECK)
        """
        task = self.store.get_task(task_id)
        if not task:
            return None, None

        current_st = AgentState(task["state"])
        ref = task["checkpoint_ref"]
        rnd = task.get("review_round", 1)

        # Step 1: Check if reviews reached quorum (E3)
        if current_st == AgentState.WAITING_REVIEW:
            collected_reviews = self.vote_aggregator.collect_reviews(ref, rnd)
            quorum = ConsensusEngine.calculate_minimum_quorum(configured_reviewers)
            
            if len(collected_reviews) >= quorum:
                # Transition to CONSENSUS_CHECK (E3)
                self.fsm.transition(task_id, AgentState.CONSENSUS_CHECK, "E3", {
                    "collected_count": len(collected_reviews),
                    "quorum": quorum
                })
                current_st = AgentState.CONSENSUS_CHECK

        # Step 2: In CONSENSUS_CHECK, compute decision and generate vote_result.json
        if current_st == AgentState.CONSENSUS_CHECK:
            collected_reviews = self.vote_aggregator.collect_reviews(ref, rnd)
            votes_list = [
                {"reviewer": r["data"]["reviewer"]["id"], "vote": r["data"]["vote"]}
                for r in collected_reviews
            ]
            raw_decision, breakdown, conf = ConsensusEngine.evaluate(votes_list, configured_reviewers)

            # Synthesize vote_result.json
            exec_id = task.get("executor_id", "cc-ds4")
            vdata = self.vote_aggregator.generate_vote_result(
                checkpoint_ref=ref,
                executor_id=exec_id,
                review_round=rnd,
                configured_reviewers=configured_reviewers,
                reviews=collected_reviews
            )

            # Branch based on decision
            if raw_decision == Decision.APPROVED:
                change = self.fsm.transition(task_id, AgentState.MERGING, "E4", vdata)
                return change, vdata
            elif raw_decision == Decision.REWORK_REQUIRED:
                change = self.fsm.transition(task_id, AgentState.REWORK, "E5", vdata)
                
                # Dispatch REWORK_REQUEST to executor
                self.msg_bus.publish(
                    msg_type=MessageType.REWORK_REQUEST,
                    from_agent="macao",
                    to_agent=exec_id,
                    payload={
                        "checkpoint_ref": ref,
                        "round": rnd + 1,
                        "issues_to_fix": vdata.get("next_step", {}).get("issues_to_fix", [])
                    }
                )
                return change, vdata
            elif raw_decision == Decision.DEADLOCK:
                # Consensus Deadlock: trigger HUMAN_OVERRIDE_REQUEST
                self.msg_bus.publish(
                    msg_type=MessageType.HUMAN_OVERRIDE_REQUEST,
                    from_agent="macao",
                    to_agent="human_admin",
                    payload={
                        "trigger": "CONSENSUS_DEADLOCK",
                        "checkpoint_ref": ref,
                        "review_round": rnd,
                        "vote_breakdown": breakdown,
                        "options": ["APPROVED", "REWORK", "RETRY_REVIEW", "CANCEL"],
                        "timeout": "10m"
                    }
                )
                self.store.log_audit_event(task_id, "DEADLOCK_DETECTED", {
                    "breakdown": breakdown,
                    "action": "Triggered HUMAN_OVERRIDE_REQUEST"
                })
                return None, vdata

        return None, None

    def resolve_override(self, task_id: str, choice: OverrideChoice, note: str = "") -> StateChange:
        """E7 / E9 / E10: Resolves human override and forces state transition."""
        task = self.store.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        ref = task.get("checkpoint_ref", "")
        rnd = task.get("review_round", 1)

        self.store.record_override(task_id, "HUMAN_OVERRIDE", choice.value, note)

        # Synthesize final vote_result with human_override resolution
        if choice in (OverrideChoice.APPROVED, OverrideChoice.REWORK):
            collected = self.vote_aggregator.collect_reviews(ref, rnd)
            self.vote_aggregator.generate_vote_result(
                checkpoint_ref=ref,
                executor_id="cc-ds4",
                review_round=rnd,
                configured_reviewers=2,
                reviews=collected,
                human_resolution=choice.value
            )

        if choice == OverrideChoice.APPROVED:
            return self.fsm.transition(task_id, AgentState.MERGING, "E7", {"choice": "APPROVED", "note": note})
        elif choice == OverrideChoice.REWORK:
            return self.fsm.transition(task_id, AgentState.REWORK, "E7", {"choice": "REWORK", "note": note})
        elif choice == OverrideChoice.RETRY_REVIEW:
            return self.fsm.transition(task_id, AgentState.WAITING_REVIEW, "E9", {"choice": "RETRY_REVIEW", "note": note})
        elif choice == OverrideChoice.CANCEL:
            return self.fsm.transition(task_id, AgentState.CANCELLED, "E10", {"choice": "CANCEL", "note": note})
        else:
            raise ValueError(f"Unknown override choice: {choice}")
