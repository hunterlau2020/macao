"""Central Orchestrator Event Loop and Multi-Agent Workflow Coordinator (PRD §3.4 / §15)."""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Set

from macao.core.types import AgentState, AEPType, Decision, OverrideChoice, StateChange
from macao.storage.store import StateStore
from macao.msg.bus import MessageBus
from macao.adapter.base import AgentAdapter
from macao.consensus.vote import VoteAggregator
from macao.consensus.engine import ConsensusEngine
from macao.workflow.fsm import WorkflowFSM
from macao.utils.git_utils import GitManager
from macao.utils.context_builder import ReviewContextBuilder
from macao.merge.controller import MergeController


class Orchestrator:
    """Central orchestrator managing the single-process event loop, adapters, and FSM."""

    def __init__(
        self,
        project_root: str = ".",
        db_path: str = ".macao/state.db",
        executor_adapter: Optional[AgentAdapter] = None,
        reviewer_adapters: Optional[List[AgentAdapter]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.root = Path(project_root).resolve()
        if not Path(db_path).is_absolute():
            self.actual_db_path = str(self.root / db_path)
        else:
            self.actual_db_path = db_path

        self.db_path = self.actual_db_path
        self.store = StateStore(self.actual_db_path)
        self.msg_bus = MessageBus(self.actual_db_path)
        self.git = GitManager(str(self.root))
        self.fsm = WorkflowFSM(self.store, str(self.root))
        self.vote_aggregator = VoteAggregator(str(self.root))
        self.merge_controller = MergeController(self.store, str(self.root))

        self.executor = executor_adapter
        self.reviewers = reviewer_adapters or []
        self.config = config or {
            "max_rework_rounds": 3,
            "min_effective_votes": 2,
            "ci_gate_command": None,
            "require_signoff": False
        }

    # --- High-Level Workflow Actions ---

    def start_task(
        self,
        title: str,
        task_description: str,
        acceptance_criteria: Dict[str, Any],
        source_branch: str = "feature/task-01",
        target_branch: str = "main",
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """E1: IDLE -> CODING. Initializes task and sends DEVELOPMENT_STARTED."""
        t_id = task_id or f"task-{os.urandom(4).hex()}"
        task = self.store.create_task(t_id, title, source_branch, target_branch)

        # Transition FSM
        self.fsm.transition(t_id, AgentState.CODING, "E1", {
            "description": task_description,
            "acceptance_criteria": acceptance_criteria
        })

        # Publish AEP Message
        exec_id = self.executor.agent_id if self.executor else "cc-ds4"
        self.msg_bus.publish(
            msg_type=AEPType.DEVELOPMENT_STARTED,
            from_agent="macao",
            to_agent=exec_id,
            payload={
                "task_id": t_id,
                "title": title,
                "description": task_description,
                "acceptance_criteria": acceptance_criteria,
                "source_branch": source_branch,
                "target_branch": target_branch
            }
        )

        return self.store.get_task(t_id)

    def check_development_checkpoint(self, task_id: str) -> Optional[StateChange]:
        """E1_PRODUCED / E6: Recognizes valid .dev.yml and transitions to READY_FOR_REVIEW."""
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

        # 1. Read real .dev.yml data if present
        dev_file = self.root / ".macao" / ".dev.yml"
        dev_data = {}
        if dev_file.exists():
            try:
                with open(dev_file, "r", encoding="utf-8") as f:
                    dev_data = yaml.safe_load(f) or {}
            except Exception:
                pass

        # 2. Get real base commit
        base_commit = task.get("target_branch", "main")
        if self.git.commit_exists(base_commit) and self.git.commit_exists(checkpoint_ref):
            mb = self.git.get_merge_base(base_commit, checkpoint_ref)
            if mb:
                base_commit = mb

        # 3. Transition FSM (E2) and archive .dev.yml
        change = self.fsm.transition(task_id, AgentState.WAITING_REVIEW, "E2")

        # 4. For each reviewer, create isolated worktree (FAIL-CLOSED: PRD §16.3 / P0-2 / P0-3)
        rev_ids = [r.agent_id for r in self.reviewers] if self.reviewers else ["cc-glm", "kimi"]
        for rev_id in rev_ids:
            try:
                worktree_path = self.git.create_isolated_worktree(rev_id, task_id, rnd, checkpoint_ref)
            except Exception as e:
                self.store.log_audit_event(task_id, "WORKTREE_CREATION_FAILED", {
                    "reviewer_id": rev_id,
                    "checkpoint_ref": checkpoint_ref,
                    "error": str(e)
                })
                raise RuntimeError(
                    f"Security Gate Blocked: Failed to create isolated worktree for Reviewer '{rev_id}': {e}. "
                    "Refusing fallback to main workspace (Fail-closed)."
                )

            # Build review_context injecting dedicated worktree path
            ctx_builder = ReviewContextBuilder(
                task_description=task.get("title", ""),
                base_commit=base_commit,
                head_commit=checkpoint_ref,
                workspace_path=str(worktree_path)
            )
            ctx_builder.populate_from_dev_manifest(dev_data)

            # Diff stats from git if available
            files_count, ins, dels = self.git.get_diff_summary(base_commit, checkpoint_ref)
            if files_count > 0:
                files_list = self.git.get_changed_files(base_commit, checkpoint_ref)
                ctx_builder.set_diff_info(files_count, ins, dels, files_list)

            review_context = ctx_builder.build()

            payload = {
                "checkpoint_ref": checkpoint_ref,
                "review_round": rnd,
                "review_context": review_context,
                "isolated_worktree_path": str(worktree_path)
            }

            self.msg_bus.publish(
                msg_type=AEPType.REVIEW_REQUEST,
                from_agent="macao",
                to_agent=rev_id,
                payload=payload
            )

        return change

    def collect_and_evaluate_consensus(self, task_id: str, configured_reviewers: int = 2) -> Tuple[Optional[StateChange], Optional[Dict[str, Any]]]:
        """
        Consensus Engine Evaluation:
        1. Checks quorum in WAITING_REVIEW -> moves to CONSENSUS_CHECK (E3).
        2. Evaluates votes in CONSENSUS_CHECK:
           - APPROVED -> writes vote_result.json, moves to MERGING (E4).
           - REWORK_REQUIRED -> writes vote_result.json, moves to REWORK (E5 if round < max else HOLD).
           - DEADLOCK -> DOES NOT WRITE vote_result.json (PRD §3.3 E3), triggers HUMAN_OVERRIDE_REQUEST, HOLDS in CONSENSUS_CHECK.
        """
        task = self.store.get_task(task_id)
        if not task:
            return None, None

        current_st = AgentState(task["state"])
        ref = task.get("checkpoint_ref")
        rnd = task.get("review_round", 1)
        exec_id = task.get("executor_id", "cc-ds4")
        max_rework_rounds = self.config.get("max_rework_rounds", 3)

        if not ref:
            return None, None

        allowed_rev_ids: Optional[Set[str]] = {r.agent_id for r in self.reviewers} if self.reviewers else None

        # Step 1: In WAITING_REVIEW, check quorum
        if current_st == AgentState.WAITING_REVIEW:
            collected_reviews = self.vote_aggregator.collect_reviews(ref, rnd, allowed_rev_ids)
            quorum = ConsensusEngine.calculate_minimum_quorum(configured_reviewers)
            if len(collected_reviews) >= quorum:
                self.fsm.transition(task_id, AgentState.CONSENSUS_CHECK, "E3", {
                    "valid_reviews": len(collected_reviews),
                    "quorum": quorum
                })
                current_st = AgentState.CONSENSUS_CHECK

        # Step 2: In CONSENSUS_CHECK, compute decision
        if current_st == AgentState.CONSENSUS_CHECK:
            collected_reviews = self.vote_aggregator.collect_reviews(ref, rnd, allowed_rev_ids)
            votes_list = [
                {"reviewer": r["data"]["reviewer"]["id"], "vote": r["data"]["vote"]}
                for r in collected_reviews
            ]
            raw_decision, breakdown, conf = ConsensusEngine.evaluate(votes_list, configured_reviewers)

            # Branch based on decision
            if raw_decision == Decision.APPROVED:
                vdata = self.vote_aggregator.generate_vote_result(
                    checkpoint_ref=ref,
                    executor_id=exec_id,
                    review_round=rnd,
                    configured_reviewers=configured_reviewers,
                    reviews=collected_reviews,
                    write_to_disk=True
                )
                change = self.fsm.transition(task_id, AgentState.MERGING, "E4", vdata)
                return change, vdata

            elif raw_decision == Decision.REWORK_REQUIRED:
                if rnd < max_rework_rounds:
                    vdata = self.vote_aggregator.generate_vote_result(
                        checkpoint_ref=ref,
                        executor_id=exec_id,
                        review_round=rnd,
                        configured_reviewers=configured_reviewers,
                        reviews=collected_reviews,
                        write_to_disk=True
                    )
                    change = self.fsm.transition(task_id, AgentState.REWORK, "E5", vdata)

                    # Dispatch REWORK_REQUEST to executor
                    self.msg_bus.publish(
                        msg_type=AEPType.REWORK_REQUEST,
                        from_agent="macao",
                        to_agent=exec_id,
                        payload={
                            "checkpoint_ref": ref,
                            "round": rnd + 1,
                            "issues_to_fix": vdata.get("next_step", {}).get("issues_to_fix", [])
                        }
                    )
                    return change, vdata
                else:
                    # Max rework rounds reached -> trigger HUMAN_OVERRIDE_REQUEST without writing automatic vote_result
                    self.msg_bus.publish(
                        msg_type=AEPType.HUMAN_OVERRIDE_REQUEST,
                        from_agent="macao",
                        to_agent="human_admin",
                        payload={
                            "trigger": "MAX_REWORK_ROUNDS_REACHED",
                            "checkpoint_ref": ref,
                            "review_round": rnd,
                            "vote_breakdown": breakdown,
                            "options": ["APPROVED", "REWORK", "RETRY_REVIEW", "CANCEL"],
                            "timeout": "10m"
                        }
                    )
                    self.store.log_audit_event(task_id, "MAX_REWORK_REACHED", {
                        "round": rnd,
                        "max_rework_rounds": max_rework_rounds
                    })
                    return None, None

            elif raw_decision == Decision.DEADLOCK:
                # PRD §3.3 E3 Rule: HOLD, DO NOT WRITE vote_result.json, trigger HUMAN_OVERRIDE_REQUEST
                self.msg_bus.publish(
                    msg_type=AEPType.HUMAN_OVERRIDE_REQUEST,
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
                    "action": "Triggered HUMAN_OVERRIDE_REQUEST (HOLD, no vote_result.json on disk)"
                })
                # vdata is generated in-memory for inspectability, but write_to_disk was not called
                vdata = self.vote_aggregator.generate_vote_result(
                    checkpoint_ref=ref,
                    executor_id=exec_id,
                    review_round=rnd,
                    configured_reviewers=configured_reviewers,
                    reviews=collected_reviews,
                    write_to_disk=False
                )
                return None, vdata

        return None, None

    def execute_merge(self, task_id: str) -> Tuple[bool, str, Optional[StateChange]]:
        """Executes the merge pipeline in MERGING state (E4a/E4b)."""
        task = self.store.get_task(task_id)
        if not task or AgentState(task["state"]) != AgentState.MERGING:
            return False, "Task is not in MERGING state", None

        target_branch = task.get("target_branch", "main")
        ci_cmd = self.config.get("ci_gate_command")
        req_signoff = self.config.get("require_signoff", False)

        success, msg, commit = self.merge_controller.execute_merge_pipeline(
            task_id=task_id,
            target_branch=target_branch,
            ci_gate_command=ci_cmd,
            require_signoff=req_signoff
        )

        if success:
            change = self.fsm.transition(task_id, AgentState.DONE, "E4a", {"commit": commit})
            self.msg_bus.publish(
                msg_type=AEPType.MERGE_COMPLETED,
                from_agent="macao",
                to_agent="all",
                payload={"task_id": task_id, "merged_commit": commit, "target_branch": target_branch}
            )
            return True, msg, change
        else:
            # Revert to REWORK (E4b)
            change = self.fsm.transition(task_id, AgentState.REWORK, "E4b", {"error": msg})
            return False, msg, change

    def resolve_override(self, task_id: str, choice: OverrideChoice, note: str = "") -> StateChange:
        """E7 / E9 / E10: Resolves human override, writes final vote_result.json, and executes state transition."""
        task = self.store.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        ref = task.get("checkpoint_ref", "")
        rnd = task.get("review_round", 1)

        self.store.record_override(task_id, "HUMAN_OVERRIDE", choice.value, note)

        # Synthesize final vote_result.json with human_override resolution
        allowed_rev_ids = {r.agent_id for r in self.reviewers} if self.reviewers else None
        collected = self.vote_aggregator.collect_reviews(ref, rnd, allowed_rev_ids)
        self.vote_aggregator.generate_vote_result(
            checkpoint_ref=ref,
            executor_id=task.get("executor_id", "cc-ds4"),
            review_round=rnd,
            configured_reviewers=len(self.reviewers) or 2,
            reviews=collected,
            human_resolution=choice.value,
            write_to_disk=True
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
