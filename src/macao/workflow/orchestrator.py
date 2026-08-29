"""High-Level Multi-Agent Workflow Orchestrator (PRD §3, §10)."""

import os
import uuid
import yaml
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Set, Union

from macao.core.types import (
    AgentState,
    AEPType,
    Decision,
    Vote,
    OpinionStatus,
    Resolution,
    OverrideChoice,
    StateChange
)
from macao.storage.store import StateStore
from macao.msg.bus import MessageBus
from macao.consensus.engine import ConsensusEngine
from macao.consensus.vote import VoteAggregator
from macao.utils.context_builder import ReviewContextBuilder
from macao.adapter.base import AgentAdapter
from macao.merge.controller import MergeController
from macao.workflow.fsm import WorkflowFSM
from macao.utils.git_utils import GitManager
from macao.core.config import ConfigManager


def parse_duration(val: Union[str, int, float]) -> float:
    """Parses duration string like '10m', '30s', '1h' to float seconds."""
    if isinstance(val, (int, float)):
        return float(val)
    val = str(val).strip().lower()
    if val.endswith("s"):
        return float(val[:-1])
    elif val.endswith("m"):
        return float(val[:-1]) * 60
    elif val.endswith("h"):
        return float(val[:-1]) * 3600
    elif val.endswith("d"):
        return float(val[:-1]) * 86400
    try:
        return float(val)
    except ValueError:
        return 600.0


class Orchestrator:
    """Coordinates Agent Lifecycles, State Transitions, and Artifact Pipelines."""

    def __init__(
        self,
        project_root: str = ".",
        db_path: Optional[str] = None,
        executor_adapter: Optional[AgentAdapter] = None,
        reviewer_adapters: Optional[List[AgentAdapter]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.root = Path(project_root).resolve()
        self.macao_dir = self.root / ".macao"
        self.macao_dir.mkdir(parents=True, exist_ok=True)

        if db_path:
            self.actual_db_path = str(Path(db_path).resolve())
        else:
            self.actual_db_path = str(self.macao_dir / "state.db")

        self.db_path = self.actual_db_path
        self.store = StateStore(self.actual_db_path, project_root=str(self.root))
        self.msg_bus = MessageBus(self.actual_db_path)
        self.git = GitManager(str(self.root))
        self.fsm = WorkflowFSM(self.store, str(self.root))
        self.vote_aggregator = VoteAggregator(str(self.root))
        self.merge_controller = MergeController(self.store, str(self.root))

        self.executor = executor_adapter
        self.reviewers = reviewer_adapters or []

        # Normalized configuration extraction (Single Truth)
        raw_config = config or {}
        policy = raw_config.get("policy", {})
        merge_policy = raw_config.get("merge", {})
        team = raw_config.get("team", {})
        repo = raw_config.get("project", {}).get("repository", {})
        timeouts = raw_config.get("timeouts", {})

        reviewers_list = raw_config.get("reviewers") or team.get("reviewers") or [
            {"id": "codex", "cli": "codex", "adapter": "pty-wrapper"},
            {"id": "opencode", "cli": "opencode", "adapter": "pty-wrapper"},
            {"id": "antigravity", "cli": "agy", "adapter": "pty-wrapper"}
        ]

        if reviewer_adapters:
            active_rev_ids = [r.agent_id for r in reviewer_adapters]
        elif reviewers_list:
            active_rev_ids = [r["id"] for r in reviewers_list]
        else:
            active_rev_ids = ["codex", "opencode", "antigravity"]

        reviewer_ids = raw_config.get("reviewer_ids", active_rev_ids)

        self.config: Dict[str, Any] = {
            "max_rework_rounds": raw_config.get("max_rework_rounds", policy.get("max_rework_rounds", 3)),
            "min_effective_votes": raw_config.get("min_effective_votes", policy.get("min_effective_votes", len(reviewer_ids))),
            "require_signoff": raw_config.get("require_signoff", merge_policy.get("require_human_signoff", True)),
            "ci_gate_command": raw_config.get("ci_gate_command", merge_policy.get("ci_gate_command")),
            "strategy": raw_config.get("strategy", merge_policy.get("strategy", "ff_only")),
            "rebase_before_merge": raw_config.get("rebase_before_merge", merge_policy.get("rebase_before_merge", False)),
            "remote_name": raw_config.get("remote_name", repo.get("remote_name", "origin")),
            "target_branch": raw_config.get("target_branch", repo.get("default_branch", "main")),
            "executor_id": raw_config.get("executor_id", team.get("executor", {}).get("id", "claude-code")),
            "reviewers": reviewers_list,
            "reviewer_ids": reviewer_ids,
            "timeouts": timeouts
        }

    # --- High-Level Workflow Actions ---

    def start_task(
        self,
        title: str,
        task_description: str,
        acceptance_criteria: Optional[Dict[str, Any]] = None,
        source_branch: Optional[str] = None,
        target_branch: str = "main",
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """E1: IDLE -> CODING (Task Initialization with collision-proof high-entropy ID)."""
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
        rand_suffix = uuid.uuid4().hex[:6]
        t_id = task_id or f"task-{date_str}-{rand_suffix}"
        src_branch = source_branch or f"feature/{t_id}"

        # Create Task in store
        task_record = self.store.create_task(
            task_id=t_id,
            title=title,
            source_branch=src_branch,
            target_branch=target_branch,
            acceptance_criteria=acceptance_criteria or {}
        )

        # Transition FSM to CODING
        self.fsm.transition(t_id, AgentState.CODING, "E1", {
            "title": title,
            "description": task_description,
            "source_branch": src_branch,
            "target_branch": target_branch
        })

        # Inject task to executor if present
        exec_id = self.config.get("executor_id", "claude-code")
        if self.executor:
            self.executor.start()
            self.executor.inject_task({
                "task_id": t_id,
                "task_description": task_description,
                "acceptance_criteria": acceptance_criteria or {}
            })

        # Broadcast DEVELOPMENT_STARTED AEP
        self.msg_bus.publish(
            msg_type=AEPType.DEVELOPMENT_STARTED,
            from_agent="macao",
            to_agent=exec_id,
            payload={
                "task_id": t_id,
                "title": title,
                "task_description": task_description,
                "source_branch": src_branch,
                "target_branch": target_branch
            }
        )

        return self.store.get_task(t_id)

    def check_development_checkpoint(self, task_id: str) -> Optional[StateChange]:
        """
        Layer 1a: Scans .macao/.dev.yml for explicit checkpoint signal.
        Registers dev_manifest in StateStore and transitions from CODING/REWORK to READY_FOR_REVIEW.
        """
        task = self.store.get_task(task_id)
        if not task:
            return None

        current_st = AgentState(task["state"])
        if current_st not in (AgentState.CODING, AgentState.REWORK):
            return None

        rnd = task.get("review_round", 1)
        dev_file = self.root / ".macao" / ".dev.yml"
        if not dev_file.exists():
            return None

        try:
            with open(dev_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            return None

        if not data or not isinstance(data, dict):
            return None

        # Check scope matching (round and status)
        dev_rnd = data.get("review_round", 1)
        status = data.get("status")
        git_info = data.get("development", {}).get("git", {})
        latest_commit = git_info.get("latest_commit")

        if dev_rnd == rnd and status == "ready_for_review" and latest_commit:
            # Register artifact in StateStore (PRD §11.4 / P1-2)
            try:
                rel_path = str(dev_file.relative_to(self.root))
            except Exception:
                rel_path = ".macao/.dev.yml"

            self.store.register_artifact(
                task_id=task_id,
                kind="dev_manifest",
                checkpoint_ref=latest_commit,
                review_round=rnd,
                path=rel_path
            )

            # Transition to READY_FOR_REVIEW (产物型转移)
            trigger = "E6" if current_st == AgentState.REWORK else "E1_PRODUCED"
            change = self.fsm.transition(
                task_id,
                AgentState.READY_FOR_REVIEW,
                trigger,
                detail={"latest_commit": latest_commit, "dev_manifest": data}
            )
            return change

        return None

    def dispatch_review_requests(self, task_id: str) -> StateChange:
        """
        E2: READY_FOR_REVIEW -> WAITING_REVIEW.
        Creates dedicated isolated worktrees for each reviewer FIRST (Fail-closed & Transactional).
        Only after all worktrees succeed, transitions FSM and publishes REVIEW_REQUEST with deadline to reviewers.
        """
        task = self.store.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        checkpoint_ref = task.get("checkpoint_ref")
        if not checkpoint_ref:
            raise ValueError(f"No checkpoint_ref attached to task {task_id}")

        rnd = task.get("review_round", 1)

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

        # 3. For each reviewer, create isolated worktree FIRST (FAIL-CLOSED & TRANSACTIONAL: PRD §16.3 / P0-2 / P0-3)
        rev_ids = [r.agent_id for r in self.reviewers] if self.reviewers else self.config.get("reviewer_ids", ["codex", "opencode", "antigravity"])
        created_worktrees: Dict[str, Path] = {}
        try:
            for rev_id in rev_ids:
                worktree_path = self.git.create_isolated_worktree(rev_id, task_id, rnd, checkpoint_ref)
                created_worktrees[rev_id] = worktree_path
        except Exception as e:
            # Cleanup any partially created worktrees from this dispatch physically
            for rev_id, p in created_worktrees.items():
                try:
                    self.git.remove_isolated_worktree(rev_id, task_id, rnd)
                except Exception:
                    pass
            self.store.log_audit_event(task_id, "WORKTREE_CREATION_FAILED", {
                "reviewer_id": rev_id,
                "checkpoint_ref": checkpoint_ref,
                "error": str(e)
            })
            raise RuntimeError(
                f"Security Gate Blocked: Failed to create isolated worktree for Reviewer '{rev_id}': {e}. "
                "Refusing fallback to main workspace (Fail-closed)."
            )

        # 4. Only after all worktrees are successfully prepared, transition FSM (E2) and archive .dev.yml
        change = self.fsm.transition(task_id, AgentState.WAITING_REVIEW, "E2")

        # 5. Calculate deadline and publish REVIEW_REQUEST with deadline to each reviewer
        timeout_val = self.config.get("timeouts", {}).get("per_reviewer", "10m")
        timeout_sec = parse_duration(timeout_val)
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        deadline_dt = now_dt + datetime.timedelta(seconds=timeout_sec)
        deadline_iso = deadline_dt.isoformat()

        self.store.log_audit_event(task_id, "REVIEW_REQUESTS_DISPATCHED", {
            "checkpoint_ref": checkpoint_ref,
            "review_round": rnd,
            "reviewers": list(created_worktrees.keys()),
            "deadline": deadline_iso,
            "timeout_seconds": timeout_sec
        })

        for rev_id, worktree_path in created_worktrees.items():
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
                "isolated_worktree_path": str(worktree_path),
                "deadline": deadline_iso
            }

            self.msg_bus.publish(
                msg_type=AEPType.REVIEW_REQUEST,
                from_agent="macao",
                to_agent=rev_id,
                payload=payload,
                deadline=deadline_iso
            )

        return change

    def detect_timed_out_reviewers(
        self,
        task_id: str,
        current_time: Optional[datetime.datetime] = None
    ) -> List[str]:
        """
        Scans active review round for unsubmitted reviewers whose review deadline has elapsed.
        Uses targeted query on StateStore to eliminate limit window truncation.
        """
        task = self.store.get_task(task_id)
        if not task:
            return []

        if task["state"] not in (AgentState.WAITING_REVIEW.value, AgentState.CONSENSUS_CHECK.value):
            return []

        ref = task.get("checkpoint_ref")
        rnd = task.get("review_round", 1)
        if not ref:
            return []

        # Targeted query on dispatch audits
        audits = self.store.get_audit_events_by_type(task_id, "REVIEW_REQUESTS_DISPATCHED", review_round=rnd)
        if not audits:
            audits = self.store.get_audit_events_by_type(task_id, "STATE_TRANSITION_E2", review_round=rnd)

        if not audits:
            return []

        dispatch_time = None
        for a in audits:
            ts_str = a.get("ts") or a.get("timestamp")
            if ts_str:
                try:
                    dispatch_time = datetime.datetime.fromisoformat(ts_str)
                    break
                except Exception:
                    pass

        if not dispatch_time:
            return []

        timeout_val = self.config.get("timeouts", {}).get("per_reviewer", "10m")
        timeout_sec = parse_duration(timeout_val)

        now = current_time or datetime.datetime.now(datetime.timezone.utc)
        if dispatch_time.tzinfo is None:
            dispatch_time = dispatch_time.replace(tzinfo=datetime.timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=datetime.timezone.utc)

        elapsed = (now - dispatch_time).total_seconds()
        if elapsed < timeout_sec:
            return []

        expected = set(self.config.get("reviewer_ids", ["codex", "opencode", "antigravity"]))
        submitted = {r["reviewer_id"] for r in self.vote_aggregator.collect_reviews(ref, rnd, allowed_reviewer_ids=expected)}
        timed_out = sorted(list(expected - submitted))
        return timed_out

    def collect_and_evaluate_consensus(
        self,
        task_id: str,
        configured_reviewers: Optional[int] = None,
        timed_out_reviewers: Optional[List[str]] = None
    ) -> Tuple[Optional[StateChange], Optional[Dict[str, Any]]]:
        """
        Consensus Engine Evaluation:
        1. Checks quorum in WAITING_REVIEW -> moves to CONSENSUS_CHECK (E3).
        2. Evaluates votes in CONSENSUS_CHECK:
           - APPROVED -> writes vote_result.json, moves to MERGING (E4).
           - REWORK_REQUIRED -> writes vote_result.json, moves to REWORK (E5 if round < max else HOLD).
           - DEADLOCK / TIMEOUT ABSTAIN -> DOES NOT WRITE vote_result.json (PRD §3.3 E3 / §6.1 / P1-NEW-3), triggers HUMAN_OVERRIDE_REQUEST, HOLDS in CONSENSUS_CHECK.
           - MAX_REWORK_ROUNDS_REACHED -> DOES NOT WRITE vote_result.json to disk (PRD §3.3 E5/E7 / Codex P0-3), triggers HUMAN_OVERRIDE_REQUEST, HOLDS.
        """
        task = self.store.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        current_st = AgentState(task["state"])
        ref = task.get("checkpoint_ref")
        rnd = task.get("review_round", 1)
        exec_id = task.get("executor_id") or self.config.get("executor_id", "claude-code")

        num_configured = configured_reviewers or len(self.config.get("reviewer_ids", ["codex", "opencode", "antigravity"]))

        # Auto-detect timeouts if not explicitly supplied
        if timed_out_reviewers is None:
            timed_out_reviewers = self.detect_timed_out_reviewers(task_id)

        # Check quorum transition from WAITING_REVIEW -> CONSENSUS_CHECK
        if current_st == AgentState.WAITING_REVIEW and ref:
            allowed_revs = set(self.config.get("reviewer_ids", []))
            reviews = self.vote_aggregator.collect_reviews(ref, rnd, allowed_reviewer_ids=allowed_revs)
            quorum = ConsensusEngine.calculate_minimum_quorum(num_configured)
            # Quorum can be reached by either enough submitted reviews or timeout processing
            if len(reviews) >= quorum or timed_out_reviewers:
                self.fsm.transition(task_id, AgentState.CONSENSUS_CHECK, "E3")
                current_st = AgentState.CONSENSUS_CHECK

        if current_st == AgentState.CONSENSUS_CHECK and ref:
            allowed_revs = set(self.config.get("reviewer_ids", []))
            collected_reviews = self.vote_aggregator.collect_reviews(ref, rnd, allowed_reviewer_ids=allowed_revs)

            # Register each collected review artifact in StateStore (P1-2)
            for r in collected_reviews:
                self.store.register_artifact(
                    task_id=task_id,
                    kind="review_manifest",
                    checkpoint_ref=ref,
                    review_round=rnd,
                    path=r["file_path"],
                    reviewer_id=r["reviewer_id"]
                )

            votes_list = []
            for r in collected_reviews:
                v_data = r["data"]
                votes_list.append({
                    "reviewer": v_data["reviewer"]["id"],
                    "vote": v_data["vote"],
                    "confidence": float(v_data.get("opinion", {}).get("confidence", 0.9))
                })

            # Handle Reviewer Timeouts (REQ-TIMEOUT): Synthesize ABSTAIN votes and idempotent audit
            if timed_out_reviewers:
                existing_timeouts = self.store.get_audit_events_by_type(task_id, "REVIEWER_TIMEOUT_ABSTAIN", review_round=rnd)
                existing_timed_out_ids = {a.get("detail", {}).get("reviewer_id") for a in existing_timeouts}
                for to_rev in timed_out_reviewers:
                    if not any(v["reviewer"] == to_rev for v in votes_list):
                        votes_list.append({
                            "reviewer": to_rev,
                            "vote": Vote.ABSTAIN.value,
                            "confidence": 0.0,
                            "timeout": True
                        })
                        if to_rev not in existing_timed_out_ids:
                            self.store.log_audit_event(task_id, "REVIEWER_TIMEOUT_ABSTAIN", {
                                "reviewer_id": to_rev,
                                "review_round": rnd,
                                "checkpoint_ref": ref
                            })

            decision, breakdown, confidence = ConsensusEngine.evaluate(
                votes=votes_list,
                configured_reviewers=num_configured
            )

            # Rule (P1-NEW-3 / PRD §2.2 / §3.3 / §6.1):
            # If decision is DEADLOCK OR any reviewer timed out, MUST HOLD in CONSENSUS_CHECK and NOT automatically transition to MERGING.
            # Timeout degradation requires human confirmation via resolve_override.
            if decision == Decision.DEADLOCK or (timed_out_reviewers and len(timed_out_reviewers) > 0):
                reason_code = "TIMEOUT_ESCALATION" if timed_out_reviewers else "DEADLOCK_DETECTED"
                self.store.log_audit_event(task_id, "DEADLOCK_DETECTED", {
                    "checkpoint_ref": ref,
                    "review_round": rnd,
                    "reason": reason_code,
                    "summary": f"{reason_code}: approve={breakdown.get('approve')}, reject={breakdown.get('reject')}, abstain={breakdown.get('abstain')}",
                    "vote_breakdown": breakdown
                })
                # Trigger HUMAN_OVERRIDE_REQUEST AEP
                self.msg_bus.publish(
                    msg_type=AEPType.HUMAN_OVERRIDE_REQUEST,
                    from_agent="macao",
                    to_agent="admin",
                    payload={
                        "task_id": task_id,
                        "checkpoint_ref": ref,
                        "review_round": rnd,
                        "reason": reason_code,
                        "summary": f"{reason_code}: approve={breakdown.get('approve')}, reject={breakdown.get('reject')}, abstain={breakdown.get('abstain')}",
                        "vote_breakdown": breakdown
                    }
                )
                return None, None

            # Rule: When max rework rounds is reached, HOLD in CONSENSUS_CHECK and DO NOT write automatic vote_result.json (PRD §3.3 E5/E7 / Codex P0-3)
            max_rnd = self.config.get("max_rework_rounds", 3)
            if decision == Decision.REWORK_REQUIRED and rnd >= max_rnd:
                self.store.log_audit_event(task_id, "MAX_REWORK_ROUNDS_REACHED", {
                    "review_round": rnd,
                    "max_rework_rounds": max_rnd,
                    "summary": f"Max rework rounds reached ({rnd}): reject={breakdown.get('reject')}",
                    "vote_breakdown": breakdown
                })
                self.msg_bus.publish(
                    msg_type=AEPType.HUMAN_OVERRIDE_REQUEST,
                    from_agent="macao",
                    to_agent="admin",
                    payload={
                        "task_id": task_id,
                        "checkpoint_ref": ref,
                        "review_round": rnd,
                        "reason": "MAX_REWORK_ROUNDS_REACHED",
                        "summary": f"Max rework rounds reached ({rnd}): reject={breakdown.get('reject')}",
                        "vote_breakdown": breakdown
                    }
                )
                return None, None

            # Generate and write authoritative vote_result.json for valid non-deadlock decisions
            vdata = self.vote_aggregator.generate_vote_result(
                checkpoint_ref=ref,
                executor_id=exec_id,
                review_round=rnd,
                configured_reviewers=num_configured,
                reviews=collected_reviews,
                human_resolution=None,
                timed_out_reviewers=timed_out_reviewers,
                write_to_disk=True
            )

            # Register vote_result artifact in store (P1-2)
            self.store.register_artifact(
                task_id=task_id,
                kind="vote_result",
                checkpoint_ref=ref,
                review_round=rnd,
                path=".macao/vote_result.json"
            )

            if decision == Decision.APPROVED:
                change = self.fsm.transition(task_id, AgentState.MERGING, "E4", vdata)
                return change, vdata
            elif decision == Decision.REWORK_REQUIRED:
                change = self.fsm.transition(task_id, AgentState.REWORK, "E5", vdata)
                self.msg_bus.publish(
                    msg_type=AEPType.REWORK_REQUEST,
                    from_agent="macao",
                    to_agent=exec_id,
                    payload={
                        "task_id": task_id,
                        "review_round": rnd + 1,
                        "summary": f"Rework required: reject={breakdown.get('reject')}",
                        "vote_breakdown": breakdown
                    }
                )
                return change, vdata
            elif decision == Decision.RETRY_REVIEW:
                change = self.fsm.transition(task_id, AgentState.WAITING_REVIEW, "E9", vdata)
                return change, vdata
            elif decision == Decision.CANCELLED:
                change = self.fsm.transition(task_id, AgentState.CANCELLED, "E10", vdata)
                return change, vdata

        return None, None

    def execute_merge(self, task_id: str) -> Tuple[bool, str, Optional[StateChange]]:
        """
        E4a / E4b: MERGING -> DONE (on success) or REWORK (on failure).
        Invokes Fast-forward Merge Controller with CI gates and Signoff verification (PRD §14.5).
        """
        task = self.store.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        current_st = AgentState(task["state"])
        if current_st != AgentState.MERGING:
            return False, f"Task {task_id} is in state {current_st.value}, expected MERGING", None

        req_signoff = self.config.get("require_signoff", True)
        ci_cmd = self.config.get("ci_gate_command")
        target_branch = task.get("target_branch") or self.config.get("target_branch", "main")
        remote_name = self.config.get("remote_name")

        success, msg, commit = self.merge_controller.execute_merge_pipeline(
            task_id=task_id,
            target_branch=target_branch,
            ci_gate_command=ci_cmd,
            require_signoff=req_signoff,
            remote_name=remote_name
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

    def resolve_override(self, task_id: str, choice: Union[OverrideChoice, str], note: str = "") -> StateChange:
        """E7 / E9 / E10: Resolves human override, writes final vote_result.json, and executes state transition."""
        task = self.store.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        ref = task.get("checkpoint_ref", "")
        rnd = task.get("review_round", 1)
        exec_id = task.get("executor_id") or self.config.get("executor_id", "claude-code")

        # Normalize choice
        if isinstance(choice, str):
            choice_upper = choice.strip().upper()
            if choice_upper in ("APPROVED", "FORCE_MERGE", "MERGE"):
                choice_enum = OverrideChoice.APPROVED
            elif choice_upper in ("REWORK", "FORCE_REWORK"):
                choice_enum = OverrideChoice.REWORK
            elif choice_upper in ("RETRY_REVIEW", "RETRY"):
                choice_enum = OverrideChoice.RETRY_REVIEW
            elif choice_upper in ("CANCEL", "CANCELLED"):
                choice_enum = OverrideChoice.CANCEL
            else:
                choice_enum = OverrideChoice(choice_upper)
        else:
            choice_enum = choice

        # 1. Write human override audit event
        self.store.log_audit_event(
            task_id=task_id,
            event_type="HUMAN_OVERRIDE",
            detail={
                "checkpoint_ref": ref,
                "review_round": rnd,
                "actor": "human_admin",
                "action": choice_enum.value,
                "reason": note
            }
        )

        # 2. Map choice to target state, trigger ID, and resolution string
        choice_map = {
            OverrideChoice.APPROVED: (AgentState.MERGING, "E7", "APPROVED"),
            OverrideChoice.REWORK: (AgentState.REWORK, "E7", "REWORK"),
            OverrideChoice.RETRY_REVIEW: (AgentState.WAITING_REVIEW, "E9", "RETRY_REVIEW"),
            OverrideChoice.CANCEL: (AgentState.CANCELLED, "E10", "CANCEL")
        }
        target_state, trigger_id, resolution_choice = choice_map[choice_enum]

        # 3. Retrieve timed out reviewers from targeted query on audit events (PRD §2.2 / §3.3 / P1-1 / P1-NEW-4)
        timeout_audits = self.store.get_audit_events_by_type(task_id, "REVIEWER_TIMEOUT_ABSTAIN", review_round=rnd)
        timed_out_revs = [
            a["detail"]["reviewer_id"]
            for a in timeout_audits
            if "reviewer_id" in a.get("detail", {})
        ]

        # 4. Generate and write authoritative vote_result.json with human resolution and ABSTAIN votes
        allowed_revs = set(self.config.get("reviewer_ids", []))
        collected_reviews = self.vote_aggregator.collect_reviews(ref, rnd, allowed_reviewer_ids=allowed_revs)
        vdata = self.vote_aggregator.generate_vote_result(
            checkpoint_ref=ref,
            executor_id=exec_id,
            review_round=rnd,
            configured_reviewers=len(self.config.get("reviewer_ids", ["codex", "opencode", "antigravity"])),
            reviews=collected_reviews,
            human_resolution=resolution_choice,
            timed_out_reviewers=timed_out_revs,
            write_to_disk=True
        )

        # Register authoritative vote_result artifact in store
        self.store.register_artifact(
            task_id=task_id,
            kind="vote_result",
            checkpoint_ref=ref,
            review_round=rnd,
            path=".macao/vote_result.json"
        )

        # 5. Perform FSM transition
        change = self.fsm.transition(task_id, target_state, trigger_id, vdata)

        # 6. Broadcast notification using standard Schema AEPType.STATE_CHANGED
        self.msg_bus.publish(
            msg_type=AEPType.STATE_CHANGED,
            from_agent="human_admin",
            to_agent="all",
            payload={
                "task_id": task_id,
                "action": "OVERRIDE_RESOLVED",
                "choice": choice_enum.value,
                "new_state": target_state.value,
                "note": note
            }
        )

        return change
