import os
import json
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
from macao.workflow.transitions import TransitionTable
from macao.utils.git_utils import GitManager
from macao.core.config import ConfigManager
import hashlib
from macao.core.schema import validate_admin_override
from macao.core.schema import validate_dev_manifest
from macao.core.schema import validate_review_disposition


def parse_duration(val: Union[str, int, float], default: Optional[float] = None) -> float:
    """Parses duration string like '10m', '30s', '1h' to float seconds."""
    if isinstance(val, (int, float)):
        return float(val)
    if not val:
        if default is not None:
            return default
        return 600.0
    v = str(val).strip().lower()
    if v.endswith("s"):
        return float(v[:-1])
    elif v.endswith("m"):
        return float(v[:-1]) * 60
    elif v.endswith("h"):
        return float(v[:-1]) * 3600
    elif v.endswith("d"):
        return float(v[:-1]) * 86400
    try:
        return float(v)
    except ValueError:
        if default is not None:
            return default
        raise ValueError(f"Invalid duration format: '{val}'")


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
        raw_config = config
        if raw_config is None and (self.root / "macao.yaml").exists():
            try:
                raw_config = yaml.safe_load((self.root / "macao.yaml").read_text(encoding="utf-8")) or {}
            except Exception:
                raw_config = {}
        raw_config = raw_config or {}
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

        self.raw_config = raw_config
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
            "timeouts": timeouts,
            "team": team,
            "policy": policy
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
        # Create Task in store with collision-proof high-entropy ID and bounded retry (P0-1)
        for attempt in range(5):
            date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
            rand_suffix = uuid.uuid4().hex[:8]
            t_id = task_id or f"task-{date_str}-{rand_suffix}"
            src_branch = source_branch or f"feature/{t_id}"

            try:
                task_record = self.store.create_task(
                    task_id=t_id,
                    title=title,
                    source_branch=src_branch,
                    target_branch=target_branch,
                    acceptance_criteria=acceptance_criteria or {}
                )
                break
            except Exception:
                if task_id is not None or attempt == 4:
                    raise
                continue

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
        crit_list = acceptance_criteria if isinstance(acceptance_criteria, list) and len(acceptance_criteria) > 0 else ["All unit tests pass", "Zero regression"]
        self.msg_bus.publish(
            msg_type=AEPType.DEVELOPMENT_STARTED,
            from_agent="macao",
            to_agent=exec_id,
            payload={
                "task_id": t_id,
                "title": title,
                "specification_summary": task_description or title,
                "acceptance_criteria": crit_list,
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

        # 1. Full Schema validation (PRD §2.1 / P1-NEW-11 / Codex P1-1)
        is_valid, err = validate_dev_manifest(data)
        if not is_valid:
            return None

        # 2. Strict invariant validation (no permissive fallbacks)
        dev_rnd = data.get("review_round")
        status = data.get("status")
        signal = data.get("signal")
        git_info = data.get("development", {}).get("git", {})
        latest_commit = git_info.get("latest_commit")
        quality = data.get("development", {}).get("quality_metrics", {})
        tests_passed = quality.get("tests_passed") is True or quality.get("tests_exempt") is True

        if dev_rnd == rnd and status == "ready_for_review" and signal == "EXPLICIT" and latest_commit and tests_passed:
            # 3. Check commit physically exists in git repository if git repo is present (PRD §2.1)
            if self.git and self.git.is_git_repository():
                if not self.git.commit_exists(latest_commit):
                    return None

            # 4. Rework gate & Checkpoint freshness & topology (PRD §2.1:216 / §3.3 E6:839 / Grok P1-1 / Codex P1-1)
            if current_st == AgentState.REWORK:
                prev_ref = task.get("checkpoint_ref")
                if prev_ref:
                    if latest_commit == prev_ref:
                        return None  # Rework requires a fresh commit different from previous review round
                    if self.git and self.git.is_git_repository():
                        # Previous review checkpoint must be an ancestor of the new rework commit (strict topological progress)
                        if not self.git.is_ancestor(prev_ref, latest_commit):
                            return None

            # Check commit has not already been consumed as a dev_manifest for this task (PRD §2.1:216)
            consumed_devs = [
                a for a in self.store.list_artifacts(task_id)
                if a.get("kind") == "dev_manifest" and a.get("checkpoint_ref") == latest_commit and a.get("consumed")
            ]
            if consumed_devs:
                return None

            # 5. Register artifact in StateStore (PRD §11.4 / P1-2)
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

            # 6. Transition to READY_FOR_REVIEW (产物型转移)
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
        current_state = AgentState(task["state"])
        if current_state != AgentState.WAITING_REVIEW:
            change = self.fsm.transition(task_id, AgentState.WAITING_REVIEW, "E2")
        else:
            change = StateChange(task_id, AgentState.WAITING_REVIEW, AgentState.WAITING_REVIEW, "E2_REDISPATCH", rnd, checkpoint_ref)

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

        # Targeted query on dispatch audits (sorted newest first)
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
        Consensus Engine Evaluation (PRD §3.3 / D-1 / D-2 / D-6 / UC-5 / UC-6):
        1. Checks quorum in WAITING_REVIEW -> moves to CONSENSUS_CHECK (E3).
        2. Evaluates weighted votes in CONSENSUS_CHECK:
           - APPROVED (zero issues) -> writes immutable vote_result.json, transitions via E4 to MERGING.
           - APPROVED (with issues) -> writes immutable vote_result.json, publishes Type E DISPOSITION_REQUIRED,
             and HOLDS in CONSENSUS_CHECK until executor submits valid FINAL executor.disposition.yml.
           - REWORK_REQUIRED -> writes immutable vote_result.json, transitions via E5 to REWORK (if round < max else HOLD).
           - DEADLOCK / TIMEOUT ABSTAIN -> writes immutable vote_result.json (PRD §3.3 E3 / D-1 / D-3),
             publishes Type H HUMAN_OVERRIDE_REQUEST, and HOLDS in CONSENSUS_CHECK for E7 human override.
           - MAX_REWORK_ROUNDS_REACHED -> publishes Type H HUMAN_OVERRIDE_REQUEST, HOLDS for E7 human override.
        """
        task = self.store.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        current_st = AgentState(task["state"])
        ref = task.get("checkpoint_ref")
        rnd = task.get("review_round", 1)
        exec_id = task.get("executor_id") or self.config.get("executor_id", "claude-code")

        num_configured = configured_reviewers or len(self.config.get("reviewer_ids", ["codex", "opencode", "antigravity"]))

        # Check historical timeout disposition in this round (PRD §3.3 / P1-NEW-7 / P1-Q2 / P1-NEW-8)
        # Scoped to the current review dispatch generation within this round.
        # Any timeout recorded prior to the latest REVIEW_REQUESTS_DISPATCHED in this round was voided by RETRY_REVIEW (PRD §3.3 E9).
        dispatches = self.store.get_audit_events_by_type(task_id, "REVIEW_REQUESTS_DISPATCHED", review_round=rnd)
        latest_dispatch_seq = dispatches[0].get("sequence_id", 0) if dispatches else 0

        existing_timeouts = self.store.get_audit_events_by_type(task_id, "REVIEWER_TIMEOUT_ABSTAIN", review_round=rnd)
        historical_timed_out_ids = {
            a.get("detail", {}).get("reviewer_id")
            for a in existing_timeouts
            if a.get("detail", {}).get("reviewer_id") and a.get("sequence_id", 0) >= latest_dispatch_seq
        }

        # Auto-detect timeouts if not explicitly supplied
        if timed_out_reviewers is None:
            detected = self.detect_timed_out_reviewers(task_id)
            timed_out_reviewers = sorted(list(set(detected) | historical_timed_out_ids))
        else:
            timed_out_reviewers = sorted(list(set(timed_out_reviewers) | historical_timed_out_ids))

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

            # Late Review Isolation (P1-NEW-7 / P1-Q2 / Codex P1-2 / P3-NEW-7):
            # Once a reviewer has timed out, their late submitted manifest must NOT participate in automated consensus.
            valid_reviews = []
            for r in collected_reviews:
                r_id = r.get("reviewer_id")
                if timed_out_reviewers and r_id in timed_out_reviewers:
                    # Idempotency guard (P3-NEW-7): only log once per reviewer per dispatch generation
                    existing_isolated = self.store.get_audit_events_by_type(task_id, "LATE_REVIEW_ISOLATED", review_round=rnd)
                    already_logged = any(
                        a.get("detail", {}).get("reviewer_id") == r_id and a.get("sequence_id", 0) >= latest_dispatch_seq
                        for a in existing_isolated
                    )
                    if not already_logged:
                        self.store.log_audit_event(task_id, "LATE_REVIEW_ISOLATED", {
                            "reviewer_id": r_id,
                            "review_round": rnd,
                            "checkpoint_ref": ref,
                            "note": "Late review submitted after timeout disposition; isolated from automated consensus"
                        })
                else:
                    valid_reviews.append(r)

            # Build reviewer_weights and policy from config (Claude A-P1-2 / Codex P1-1)
            reviewer_weights = {}
            for r_cfg in self.config.get("team", {}).get("reviewers", []):
                if isinstance(r_cfg, dict) and "id" in r_cfg:
                    reviewer_weights[r_cfg["id"]] = r_cfg.get("vote_weight", 1)
            for r_cfg in self.config.get("reviewers", []):
                if isinstance(r_cfg, dict) and "id" in r_cfg and r_cfg["id"] not in reviewer_weights:
                    reviewer_weights[r_cfg["id"]] = r_cfg.get("vote_weight", 1)

            policy_cfg = dict(self.config.get("policy", {}))
            total_configured_weight = policy_cfg.get("configured_weight")
            if not total_configured_weight:
                total_configured_weight = sum(reviewer_weights.values()) if reviewer_weights else num_configured

            votes_list = []
            for r in valid_reviews:
                v_data = r["data"]
                vote_val = v_data.get("vote") or v_data.get("opinion", {}).get("vote")
                if not vote_val:
                    continue
                r_id = v_data["reviewer"]["id"]
                w = int(reviewer_weights.get(r_id, v_data.get("reviewer", {}).get("vote_weight", 1)))
                votes_list.append({
                    "reviewer": r_id,
                    "vote": vote_val,
                    "weight": max(1, w),
                    "source": "manifest",
                    "confidence": float(v_data.get("opinion", {}).get("confidence", 0.9))
                })

            # Handle Reviewer Timeouts (REQ-TIMEOUT): Synthesize ABSTAIN votes and idempotent audit
            dispatch_audits = self.store.get_audit_events_by_type(task_id, "REVIEW_REQUESTS_DISPATCHED", review_round=rnd)
            to_deadline = None
            to_ping = None
            if dispatch_audits:
                to_deadline = dispatch_audits[0].get("detail", {}).get("deadline")
                to_ping = dispatch_audits[0].get("ts") or dispatch_audits[0].get("timestamp")
            if not to_deadline:
                to_deadline = datetime.datetime.now(datetime.timezone.utc).isoformat()
            if not to_ping:
                to_ping = datetime.datetime.now(datetime.timezone.utc).isoformat()

            timeout_meta_map = {}
            if timed_out_reviewers:
                for to_rev in timed_out_reviewers:
                    w = int(reviewer_weights.get(to_rev, 1))
                    t_entry = {
                        "deadline": to_deadline,
                        "last_ping_at": to_ping
                    }
                    timeout_meta_map[to_rev] = t_entry

                    if not any(v["reviewer"] == to_rev for v in votes_list):
                        v_entry = {
                            "reviewer": to_rev,
                            "vote": Vote.ABSTAIN.value,
                            "weight": max(1, w),
                            "source": "timeout",
                            "confidence": 0.0,
                            "timeout": True,
                            "deadline": to_deadline,
                            "last_ping_at": to_ping
                        }
                        votes_list.append(v_entry)
                        if to_rev not in historical_timed_out_ids:
                            self.store.log_audit_event(task_id, "REVIEWER_TIMEOUT_ABSTAIN", {
                                "reviewer_id": to_rev,
                                "review_round": rnd,
                                "checkpoint_ref": ref
                            })
                            historical_timed_out_ids.add(to_rev)

            decision, breakdown, confidence = ConsensusEngine.evaluate(
                votes=votes_list,
                configured_reviewers=num_configured,
                configured_weight=total_configured_weight,
                policy=policy_cfg
            )

            # Rule (P1-NEW-3 / P1-NEW-7 / PRD §2.2 / §3.3 / §6.1):
            # If decision is DEADLOCK OR any reviewer timed out, MUST HOLD in CONSENSUS_CHECK and NOT automatically transition to MERGING.
            # Timeout degradation requires human confirmation via resolve_override.
            if decision == Decision.DEADLOCK or (timed_out_reviewers and len(timed_out_reviewers) > 0 and decision != Decision.APPROVED):
                # PRD v2.5 D-1 / §3.4 场景三: Orchestrator writes immutable vote_result.json on DEADLOCK
                vdata = self.vote_aggregator.generate_vote_result(
                    checkpoint_ref=ref,
                    executor_id=exec_id,
                    review_round=rnd,
                    configured_reviewers=num_configured,
                    reviews=collected_reviews,
                    timed_out_reviewers=list(timed_out_reviewers) if timed_out_reviewers else [],
                    write_to_disk=True,
                    task_id=task_id,
                    reviewer_weights=reviewer_weights,
                    policy=policy_cfg,
                    timeout_metadata=timeout_meta_map
                )
                self.store.register_artifact(
                    task_id=task_id,
                    kind="vote_result",
                    checkpoint_ref=ref,
                    review_round=rnd,
                    path=".macao/vote_result.json"
                )

                reason_code = "TIMEOUT_ESCALATION" if timed_out_reviewers else "DEADLOCK_DETECTED"
                existing_deadlocks = self.store.get_audit_events_by_type(task_id, "DEADLOCK_DETECTED", review_round=rnd)
                if not existing_deadlocks:
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
                            "trigger": reason_code,
                            "summary": f"{reason_code}: approve={breakdown.get('approve')}, reject={breakdown.get('reject')}, abstain={breakdown.get('abstain')}",
                            "vote_breakdown": breakdown
                        }
                    )
                return None, None

            # Rule: When max rework rounds is reached, HOLD in CONSENSUS_CHECK and DO NOT write automatic vote_result.json (PRD §3.3 E5/E7 / Codex P0-3)
            max_rnd = self.config.get("max_rework_rounds", 3)
            if decision == Decision.REWORK_REQUIRED and rnd >= max_rnd:
                existing_max = self.store.get_audit_events_by_type(task_id, "MAX_REWORK_ROUNDS_REACHED", review_round=rnd)
                if not existing_max:
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
                            "trigger": "MAX_REWORK_ROUNDS_REACHED",
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
                reviews=valid_reviews,
                human_resolution=None,
                timed_out_reviewers=timed_out_reviewers,
                write_to_disk=True,
                task_id=task_id,
                reviewer_weights=reviewer_weights,
                policy=policy_cfg,
                timeout_metadata=timeout_meta_map
            )
            decision = Decision(vdata["decision"])

            # Register vote_result artifact in store (P1-2)
            self.store.register_artifact(
                task_id=task_id,
                kind="vote_result",
                checkpoint_ref=ref,
                review_round=rnd,
                path=".macao/vote_result.json"
            )

            if decision == Decision.APPROVED:
                if vdata.get("requires_disposition"):
                    # PRD §2.4 / §3.3 / UC-5 / Claude A-P1-4 / Codex P1-2:
                    # APPROVED with issues requires disposition before entering MERGING.
                    disp_path = self.root / ".macao" / ".dispositions" / f"r{rnd}" / "executor.disposition.yml"
                    has_valid_final_disp = False
                    all_no_new_checkpoint = False

                    if disp_path.exists():
                        try:
                            with open(disp_path, "r", encoding="utf-8") as df:
                                disp_data = yaml.safe_load(df)
                            is_valid, _ = self.validate_disposition_fulfillment(task_id, disp_data)
                            if is_valid and disp_data.get("disposition_status") == "FINAL":
                                has_valid_final_disp = True
                                items = disp_data.get("dispositions", [])
                                all_no_new_checkpoint = all(not itm.get("requires_new_checkpoint", False) for itm in items)
                                any_requires_new_checkpoint = any(itm.get("requires_new_checkpoint", False) for itm in items)
                                if any_requires_new_checkpoint:
                                    change = self.fsm.transition(task_id, AgentState.REWORK, "E5a", vdata)
                                    return change, vdata
                        except Exception:
                            pass

                    if not (has_valid_final_disp and all_no_new_checkpoint):
                        # Publish DISPOSITION_REQUIRED AEP and HOLD in CONSENSUS_CHECK.
                        vr_file = self.root / ".macao" / "vote_result.json"
                        vote_result_sha = "0" * 64
                        if vr_file.exists():
                            with open(vr_file, "rb") as f:
                                vote_result_sha = hashlib.sha256(f.read()).hexdigest()
                        self.msg_bus.publish(
                            msg_type=AEPType.DISPOSITION_REQUIRED,
                            from_agent="macao",
                            to_agent=exec_id,
                            payload={
                                "task_id": task_id,
                                "checkpoint_ref": ref or "c1a2b3d",
                                "review_round": rnd,
                                "vote_result_ref": {
                                    "path": ".macao/vote_result.json",
                                    "evidence_commit": ref or "c1a2b3d",
                                    "sha256": vote_result_sha
                                },
                                "issues_index_sha256": vdata.get("issues_index_sha256", "0" * 64),
                                "timeout_deadline": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)).isoformat()
                            }
                        )
                        return None, vdata

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
                        "checkpoint_ref": ref or "c1a2b3d",
                        "round": rnd + 1,
                        "review_round": rnd + 1,
                        "summary": f"Rework required: reject={breakdown.get('reject')}"
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

    def validate_disposition_fulfillment(
        self,
        task_id: str,
        disposition_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validates executor.disposition.yml against current task, consensus vote_result, and rules
        (PRD §2.5 / §3.3 :875 / D-2 / D-5 / UC-6 / Claude A-P1-3 / Codex P1-2).
        Enforces:
        1. Task exists and is in CONSENSUS_CHECK.
        2. Valid Draft-07 review_disposition schema.
        3. Exact task_id, checkpoint_ref, review_round, executor ID binding.
        4. Underlying consensus decision must be APPROVED (or approved by admin override).
        5. vote_result.json existence and sha256 binding.
        6. issues_index_sha256 exact match.
        7. 100% exact coverage of issues_index (no missing, no extraneous issue IDs).
        8. If FINAL, no NEEDS_ADMIN disposition items allowed.
        """
        task = self.store.get_task(task_id)
        if not task:
            return False, f"Task {task_id} not found"

        cur_state = AgentState(task["state"])
        if cur_state != AgentState.CONSENSUS_CHECK:
            return False, f"Task must be in CONSENSUS_CHECK to accept disposition, current: {cur_state.value}"

        is_valid, err = validate_review_disposition(disposition_data)
        if not is_valid:
            return False, f"Invalid review_disposition schema: {err}"

        ref = task.get("checkpoint_ref")
        rnd = task.get("review_round", 1)
        exec_id = task.get("executor_id") or self.config.get("executor_id", "claude-code")

        if disposition_data.get("task_id") != task_id:
            return False, f"Mismatched task_id: expected {task_id}, got {disposition_data.get('task_id')}"
        if disposition_data.get("checkpoint_ref") != ref:
            return False, f"Mismatched checkpoint_ref: expected {ref}, got {disposition_data.get('checkpoint_ref')}"
        if disposition_data.get("review_round") != rnd:
            return False, f"Mismatched review_round: expected {rnd}, got {disposition_data.get('review_round')}"
        if disposition_data.get("executor", {}).get("id") != exec_id:
            return False, f"Mismatched executor id: expected {exec_id}, got {disposition_data.get('executor', {}).get('id')}"

        vr_file = self.root / ".macao" / "vote_result.json"
        if not vr_file.exists():
            return False, "vote_result.json does not exist on disk"

        try:
            with open(vr_file, "r", encoding="utf-8") as f:
                vdata = json.load(f)
        except Exception as e:
            return False, f"Failed to read vote_result.json: {e}"

        # Underlying consensus decision must be APPROVED, or approved by admin override (PRD §3.3 E7 / UC-7)
        is_approved = (vdata.get("decision") == "APPROVED")
        admin_file = self.root / ".macao" / "admin_override.json"
        admin_override_id = None
        if admin_file.exists():
            try:
                with open(admin_file, "r", encoding="utf-8") as af:
                    a_data = json.load(af)
                ch = a_data.get("choice") or a_data.get("override_choice")
                if (ch in ("APPROVED", "MERGE") and
                    a_data.get("task_id") == task_id and
                    a_data.get("checkpoint_ref") == ref and
                    a_data.get("review_round") == rnd):
                    is_approved = True
                    admin_override_id = a_data.get("override_id")
            except Exception:
                pass

        if not is_approved:
            return False, f"Cannot submit disposition when consensus decision is '{vdata.get('decision')}' without approved admin override"

        with open(vr_file, "rb") as fb:
            vr_sha = hashlib.sha256(fb.read()).hexdigest()

        disp_vr_sha = disposition_data.get("vote_result_ref", {}).get("sha256")
        if disp_vr_sha != vr_sha:
            return False, f"vote_result_ref sha256 mismatch: expected {vr_sha}, got {disp_vr_sha}"

        disp_issues_sha = disposition_data.get("issues_index_sha256")
        expected_issues_sha = vdata.get("issues_index_sha256")
        if disp_issues_sha != expected_issues_sha:
            return False, f"issues_index_sha256 mismatch: expected {expected_issues_sha}, got {disp_issues_sha}"

        expected_issues = vdata.get("issues_index", [])
        expected_ids = {item["issue_id"] for item in expected_issues}
        disp_items = disposition_data.get("dispositions", [])
        disp_ids = {d["issue_id"] for d in disp_items}

        if disp_ids != expected_ids:
            return False, f"Dispositions must cover 100% issues exactly: expected {sorted(list(expected_ids))}, got {sorted(list(disp_ids))}"

        for d in disp_items:
            if d.get("disposition_type") == "EXEMPTED_BY_ADMIN":
                if not admin_file.exists():
                    return False, f"Item {d.get('issue_id')} is marked EXEMPTED_BY_ADMIN but no admin_override.json exists"
                if admin_override_id and d.get("override_id") != admin_override_id:
                    return False, f"Item {d.get('issue_id')} override_id mismatch: expected {admin_override_id}, got {d.get('override_id')}"

        if disposition_data.get("disposition_status") == "FINAL":
            if any(d.get("disposition_type") == "NEEDS_ADMIN" for d in disp_items):
                return False, "FINAL disposition cannot contain NEEDS_ADMIN items"

        return True, "Valid"

    def submit_disposition(
        self,
        task_id: str,
        disposition_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[StateChange]]:
        """
        Submits and validates an executor.disposition.yml manifest (PRD §2.5 / D-2 / UC-6 / Claude A-P1-3 / Codex P1-2).
        Enforces 100% issue coverage, task/ref/round/executor binding, hash binding, and approved consensus decision.
        Transitions via E4 (MERGING) if all issues resolved without new checkpoint,
        or E5a (REWORK) if requires_new_checkpoint is True.
        """
        is_valid, err_msg = self.validate_disposition_fulfillment(task_id, disposition_data)
        if not is_valid:
            return False, f"Disposition validation failed: {err_msg}", None

        task = self.store.get_task(task_id)
        rnd = task.get("review_round", 1)
        disp_dir = self.root / ".macao" / ".dispositions" / f"r{rnd}"
        disp_dir.mkdir(parents=True, exist_ok=True)
        disp_file = disp_dir / "executor.disposition.yml"
        with open(disp_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(disposition_data, f)

        self.store.register_artifact(
            task_id=task_id,
            kind="disposition",
            checkpoint_ref=task.get("checkpoint_ref", ""),
            review_round=rnd,
            path=str(disp_file.relative_to(self.root))
        )

        status = disposition_data.get("disposition_status")
        if status == "FINAL":
            items = disposition_data.get("dispositions", [])
            any_requires_new_checkpoint = any(itm.get("requires_new_checkpoint", False) for itm in items)
            if any_requires_new_checkpoint:
                change = self.fsm.transition(task_id, AgentState.REWORK, "E5a", disposition_data)
                return True, "Disposition requires rework, transitioned via E5a to REWORK", change
            else:
                change = self.fsm.transition(task_id, AgentState.MERGING, "E4", disposition_data)
                return True, "Disposition accepted, transitioned via E4 to MERGING", change

        return True, f"Disposition accepted with status {status}", None

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
            chk_ref = task.get("checkpoint_ref") or commit or "c1a2b3d"
            self.msg_bus.publish(
                msg_type=AEPType.MERGE_COMPLETED,
                from_agent="macao",
                to_agent="all",
                payload={
                    "task_id": task_id,
                    "checkpoint_ref": chk_ref,
                    "merged_commit": commit,
                    "target_branch": target_branch
                }
            )
            return True, msg, change
        else:
            # Revert to REWORK (E4b)
            change = self.fsm.transition(task_id, AgentState.REWORK, "E4b", {"error": msg})
            return False, msg, change

    def resolve_override(self, task_id: str, choice: Union[OverrideChoice, str], note: str = "") -> StateChange:
        """
        E7 / E9 / E10: Resolves human override.
        Validates transition legality before writing disk artifacts (Fail-closed & P2-NEW-2).
        Executes full re-dispatch on RETRY_REVIEW (PRD §3.3 E9 / P1-NEW-6).
        """
        task = self.store.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        ref = task.get("checkpoint_ref", "")
        rnd = task.get("review_round", 1)
        exec_id = task.get("executor_id") or self.config.get("executor_id", "claude-code")
        from_state = AgentState(task["state"])

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
            elif choice_upper in ("EXTEND", "TIMEOUT_EXTEND"):
                choice_enum = OverrideChoice.EXTEND
            else:
                choice_enum = OverrideChoice(choice_upper)
        else:
            choice_enum = choice

        # 1. Map choice to target state, trigger ID, and resolution string (PRD §3.3 E7 / UC-7)
        choice_map = {
            OverrideChoice.APPROVED: (AgentState.MERGING, "E7", "APPROVED"),
            OverrideChoice.REWORK: (AgentState.REWORK, "E7", "REWORK"),
            OverrideChoice.RETRY_REVIEW: (AgentState.WAITING_REVIEW, "E9", "RETRY_REVIEW"),
            OverrideChoice.CANCEL: (AgentState.CANCELLED, "E10", "CANCEL"),
            OverrideChoice.EXTEND: (AgentState.CONSENSUS_CHECK, "E7", "EXTEND")
        }
        target_state, trigger_id, resolution_choice = choice_map[choice_enum]

        # 2. Pre-validate FSM transition legality (Fail-closed & P2-NEW-2: prevent orphan vote_result.json)
        if not TransitionTable.can_transition(from_state, target_state, trigger_id):
            self.store.log_audit_event(task_id, "TRANSITION_REJECTED", {
                "from_state": from_state.value,
                "to_state": target_state.value,
                "trigger_id": trigger_id,
                "choice": choice_enum.value
            })
            raise ValueError(
                f"Illegal state transition from {from_state.value} to {target_state.value} via trigger {trigger_id}"
            )

        # 3. Write human override audit event
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

        # 4. Retrieve timed out reviewers from targeted query on audit events (PRD §2.2 / §3.3 / P1-1 / P1-NEW-4 / P1-NEW-8)
        dispatches = self.store.get_audit_events_by_type(task_id, "REVIEW_REQUESTS_DISPATCHED", review_round=rnd)
        latest_dispatch_seq = dispatches[0].get("sequence_id", 0) if dispatches else 0

        timeout_audits = self.store.get_audit_events_by_type(task_id, "REVIEWER_TIMEOUT_ABSTAIN", review_round=rnd)
        timed_out_revs = [
            a["detail"]["reviewer_id"]
            for a in timeout_audits
            if "reviewer_id" in a.get("detail", {}) and a.get("sequence_id", 0) >= latest_dispatch_seq
        ]

        # 5. Generate and write authoritative admin_override.json (PRD v2.5 D-1/D-2)
        override_data = {
            "version": "1.0",
            "override_id": f"ovr-{task_id}-{rnd}",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "task_id": task_id,
            "checkpoint_ref": ref,
            "review_round": rnd,
            "admin_identity": "admin@macao.local",
            "trigger": "consensus_deadlock",
            "choice": choice_enum.value,
            "exempt_issue_ids": [],
            "note": note
        }
        is_valid_ovr, err_ovr = validate_admin_override(override_data)
        if not is_valid_ovr:
            raise ValueError(f"Generated admin_override is invalid: {err_ovr}")

        ovr_file = self.root / ".macao" / "admin_override.json"
        ovr_file.parent.mkdir(parents=True, exist_ok=True)
        with open(ovr_file, "w", encoding="utf-8") as f:
            json.dump(override_data, f, indent=2, ensure_ascii=False)

        # Register authoritative admin_override artifact in store
        self.store.register_artifact(
            task_id=task_id,
            kind="admin_override",
            checkpoint_ref=ref,
            review_round=rnd,
            path=".macao/admin_override.json"
        )

        # 6. Perform FSM transition (archives admin_override.json & reviews to .macao/archive/)
        change = self.fsm.transition(task_id, target_state, trigger_id, override_data)

        # 7. For RETRY_REVIEW (E9), clean obsolete reviews and active vote_result from active directory and re-dispatch fresh requests (PRD §3.3 E9 / P1-NEW-6 / P2-NEW-4)
        if choice_enum == OverrideChoice.RETRY_REVIEW:
            reviews_dir = self.root / ".macao" / ".reviews"
            if reviews_dir.exists():
                for rev_file in reviews_dir.glob("*.review.yml"):
                    try:
                        rev_file.unlink()
                    except Exception:
                        pass
            # Clean active vote_result.json from .macao/ so crash reconcile does not read stale E9 override (P2-NEW-4)
            active_vote = self.root / ".macao" / "vote_result.json"
            if active_vote.exists():
                try:
                    active_vote.unlink()
                except Exception:
                    pass
            # Re-dispatch review requests to reviewers with fresh deadline
            self.dispatch_review_requests(task_id)

        # 8. Broadcast notification using standard Schema AEPType.STATE_CHANGED
        self.msg_bus.publish(
            msg_type=AEPType.STATE_CHANGED,
            from_agent="human_admin",
            to_agent="all",
            payload={
                "task_id": task_id,
                "state": target_state.value,
                "to_state": target_state.value,
                "detail": f"Override resolved: choice={choice_enum.value}, note={note}"
            }
        )

        return change
