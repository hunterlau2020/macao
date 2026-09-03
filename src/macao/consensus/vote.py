"""Vote Aggregator and vote_result.json Generator (PRD §2.3)."""

import os
import json
import yaml
import hashlib
import datetime
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from macao.core.types import Decision, Resolution, Vote
from macao.consensus.engine import ConsensusEngine
from macao.core.schema import validate_review_manifest, validate_vote_result


class VoteAggregator:
    """Collects .review.yml files, applies consensus rules, and generates vote_result.json."""

    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)

    def collect_reviews(
        self,
        checkpoint_ref: str,
        review_round: int,
        allowed_reviewer_ids: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """Scans .macao/.reviews/ for valid .review.yml files matching ref and round, deduplicated by reviewer_id."""
        reviews_dir = self.root / ".macao" / ".reviews"
        if not reviews_dir.exists():
            return []

        collected_by_reviewer: Dict[str, Dict[str, Any]] = {}
        for file_path in sorted(reviews_dir.glob("*.review.yml")):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f)

                is_valid, _ = validate_review_manifest(content)
                if not is_valid:
                    continue

                if (content.get("checkpoint_ref") == checkpoint_ref and
                    content.get("review_round") == review_round):

                    reviewer_id = content.get("reviewer", {}).get("id")
                    if not reviewer_id:
                        continue
                    if allowed_reviewer_ids is not None and reviewer_id not in allowed_reviewer_ids:
                        continue

                    with open(file_path, "rb") as f_bin:
                        sha256 = hashlib.sha256(f_bin.read()).hexdigest()

                    # Deduplicate by reviewer_id (keep valid review)
                    collected_by_reviewer[reviewer_id] = {
                        "file_path": str(file_path.relative_to(self.root)),
                        "data": content,
                        "sha256": sha256,
                        "reviewer_id": reviewer_id
                    }
            except Exception:
                continue

        return list(collected_by_reviewer.values())

    def generate_vote_result(
        self,
        checkpoint_ref: str,
        executor_id: str,
        review_round: int,
        configured_reviewers: int,
        reviews: List[Dict[str, Any]],
        human_resolution: Optional[str] = None,
        timed_out_reviewers: Optional[List[str]] = None,
        write_to_disk: bool = True,
        task_id: Optional[str] = None,
        reviewer_weights: Optional[Dict[str, int]] = None,
        policy: Optional[Dict[str, Any]] = None,
        timeout_metadata: Optional[Dict[str, Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes a standardized, deterministic vote_result.json structure (PRD §2.3 / §11.2 / D-1).
        Supports pure integer weighted consensus evaluation and records cryptographic hashes.
        """
        votes_list = []
        input_artifacts = []
        issues_to_fix = []

        for rev in reviews:
            rev_data = rev.get("data", {})
            rev_id = rev_data.get("reviewer", {}).get("id", "unknown")
            if timed_out_reviewers and rev_id in timed_out_reviewers:
                continue

            rev_weight = int(reviewer_weights.get(rev_id, rev_data.get("reviewer", {}).get("vote_weight", 1))) if reviewer_weights else int(rev_data.get("reviewer", {}).get("vote_weight", 1))

            vote_val = rev_data.get("vote") or rev_data.get("opinion", {}).get("vote") or Vote.ABSTAIN.value
            confidence_val = float(rev_data.get("opinion", {}).get("confidence", 0.9))

            rev_issues = rev_data.get("issues", [])
            categories = rev_data.get("categories", [])
            op_categories = rev_data.get("opinion", {}).get("feedback", {}).get("categories", [])

            votes_list.append({
                "reviewer": rev_id,
                "vote": vote_val,
                "weight": max(1, rev_weight),
                "source": "manifest",
                "confidence": confidence_val,
                "issues_count": len(rev_issues) + len(categories) + len(op_categories)
            })

            input_artifacts.append({
                "reviewer": rev_id,
                "path": str(rev.get("path", f".macao/.reviews/r{review_round}/{rev_id}.review.yml")),
                "evidence_commit": checkpoint_ref,
                "sha256": rev.get("sha256", "0" * 64)
            })

            for itm in rev_issues:
                issues_to_fix.append({
                    "id": itm.get("id"),
                    "reviewer": rev_id,
                    "type": itm.get("type", "logic"),
                    "severity": itm.get("severity", "major"),
                    "description": itm.get("description", "")
                })
            for cat in categories:
                issues_to_fix.append({
                    "id": cat.get("id"),
                    "reviewer": rev_id,
                    "type": cat.get("type", "logic"),
                    "severity": cat.get("severity", "major"),
                    "description": cat.get("issue", "")
                })
            for cat in op_categories:
                issues_to_fix.append({
                    "id": cat.get("id"),
                    "reviewer": rev_id,
                    "type": cat.get("type", "logic"),
                    "severity": cat.get("severity", "major"),
                    "description": cat.get("issue", "")
                })

        # Include timed out reviewers as ABSTAIN (PRD §2.2 / §3.3 / P1-1 / P1-3 / D-3)
        if timed_out_reviewers:
            for to_rev in timed_out_reviewers:
                if not any(v["reviewer"] == to_rev for v in votes_list):
                    w = int(reviewer_weights.get(to_rev, 1)) if reviewer_weights else 1
                    t_meta = (timeout_metadata or {}).get(to_rev, {})
                    entry = {
                        "reviewer": to_rev,
                        "vote": Vote.ABSTAIN.value,
                        "weight": max(1, w),
                        "source": "timeout",
                        "confidence": 0.0,
                        "issues_count": 0
                    }
                    if "deadline" in t_meta:
                        entry["deadline"] = t_meta["deadline"]
                    if "last_ping_at" in t_meta:
                        entry["last_ping_at"] = t_meta["last_ping_at"]
                    votes_list.append(entry)

        total_configured_weight = None
        if policy and "configured_weight" in policy:
            total_configured_weight = int(policy["configured_weight"])
        elif reviewer_weights:
            total_configured_weight = sum(reviewer_weights.values())
        else:
            total_configured_weight = sum(v.get("weight", 1) for v in votes_list) or configured_reviewers

        decision, breakdown, confidence = ConsensusEngine.evaluate(
            votes_list,
            configured_reviewers=configured_reviewers,
            configured_weight=total_configured_weight,
            policy=policy
        )

        resolution_type = "AUTO_WEIGHTED_CONSENSUS"
        if human_resolution:
            resolution_type = "HUMAN_OVERRIDE"
            hr_upper = str(human_resolution).strip().upper()
            if hr_upper in ("APPROVED", "MERGE", "FORCE_MERGE"):
                decision = Decision.APPROVED
            elif hr_upper in ("REWORK", "REWORK_REQUIRED", "FORCE_REWORK"):
                decision = Decision.REWORK_REQUIRED
            elif hr_upper in ("RETRY", "RETRY_REVIEW"):
                decision = Decision.RETRY_REVIEW
            elif hr_upper in ("CANCEL", "CANCELLED"):
                decision = Decision.CANCELLED
            else:
                raise ValueError(
                    f"Invalid human_resolution '{human_resolution}'. Must be APPROVED, REWORK, RETRY_REVIEW, or CANCEL"
                )

        next_action_map = {
            Decision.APPROVED: "MERGE",
            Decision.REWORK_REQUIRED: "REWORK",
            Decision.RETRY_REVIEW: "RETRY_REVIEW"
        }
        next_action = next_action_map.get(decision)

        pol = policy or {}
        seat_quorum = pol.get("seat_quorum_required", math.ceil(2 * configured_reviewers / 3)) if configured_reviewers > 0 else 1
        weight_quorum = pol.get("weight_quorum_required", math.ceil(2 * total_configured_weight / 3))
        min_winning_seats = pol.get("minimum_winning_seats", 2)
        dictator_cap_enabled = pol.get("dictator_cap_enabled", True)

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        reviewers_responded = len([v for v in votes_list if v.get("source") == "manifest"])
        reviewers_accounted = len(votes_list)

        issues_index = [
            {
                "issue_id": itm.get("id") or f"ISSUE-{idx+1}",
                "reviewer": itm.get("reviewer", "reviewer"),
                "disposition_class": "BLOCKING" if itm.get("severity") in ("critical", "major") else "ADVISORY",
                "severity": itm.get("severity", "minor"),
                "title": itm.get("description") or itm.get("issue") or itm.get("title") or "Review issue"
            }
            for idx, itm in enumerate(issues_to_fix)
        ]
        canonical_issues = json.dumps(issues_index, sort_keys=True, separators=(",", ":")).encode("utf-8")
        issues_index_sha256 = hashlib.sha256(canonical_issues).hexdigest()

        result: Dict[str, Any] = {
            "version": "2.0",
            "generated_at": now_iso,
            "timestamp": now_iso,
            "task_id": task_id or f"task-{checkpoint_ref[:7]}",
            "checkpoint_ref": checkpoint_ref,
            "executor_id": executor_id,
            "executor": executor_id,
            "review_round": review_round,
            "reviewers_total": configured_reviewers,
            "reviewers_responded": reviewers_responded,
            "reviewers_accounted": reviewers_accounted,
            "votes": votes_list,
            "policy_snapshot": {
                "rule": pol.get("consensus_rule", "weighted_2/3_v1"),
                "configured_seats": pol.get("configured_seats", configured_reviewers),
                "configured_weight": total_configured_weight,
                "seat_quorum_required": seat_quorum,
                "weight_quorum_required": weight_quorum,
                "decision_threshold_numerator": pol.get("decision_threshold_numerator", 2),
                "decision_threshold_denominator": pol.get("decision_threshold_denominator", 3),
                "minimum_winning_seats": min_winning_seats,
                "dictator_cap_enabled": dictator_cap_enabled,
                "max_single_weight_share_numerator": pol.get("max_single_weight_share_numerator", 2),
                "max_single_weight_share_denominator": pol.get("max_single_weight_share_denominator", 3)
            },
            "consensus_rule": "weighted_2/3_v1",
            "vote_breakdown": {
                "approve": breakdown.get("approve", breakdown.get("yes_approve", 0)),
                "reject": breakdown.get("reject", breakdown.get("no_approve", 0)),
                "abstain": breakdown.get("abstain", 0),
                "effective_votes": breakdown.get("effective_votes", 0),
                "effective_seats": breakdown.get("effective_seats", 0),
                "effective_weight": breakdown.get("effective_weight", 0),
                "approve_seats": breakdown.get("approve_seats", 0),
                "approve_weight": breakdown.get("approve_weight", 0),
                "reject_seats": breakdown.get("reject_seats", 0),
                "reject_weight": breakdown.get("reject_weight", 0),
                "abstain_seats": breakdown.get("abstain_seats", 0),
                "abstain_weight": breakdown.get("abstain_weight", 0),
                "effective_rate": breakdown.get("effective_rate", 1.0),
                "yes_approve": breakdown.get("yes_approve", 0),
                "no_approve": breakdown.get("no_approve", 0)
            },
            "input_artifacts": input_artifacts,
            "issues_index": issues_index,
            "issues_index_sha256": issues_index_sha256,
            "requires_disposition": len(issues_to_fix) > 0,
            "decision": decision.value,
            "decision_confidence": confidence,
            "resolution": resolution_type,
            "summary": {
                "critical_issues": sum(1 for i in issues_to_fix if i.get("severity") == "critical"),
                "major_issues": sum(1 for i in issues_to_fix if i.get("severity") == "major"),
                "minor_issues": sum(1 for i in issues_to_fix if i.get("severity") == "minor"),
                "action": f"Action: {next_action or 'CANCEL'}"
            }
        }

        if next_action:
            result["next_step"] = {
                "action": next_action,
                "issues_to_fix": issues_to_fix
            }

        # Fail-closed: validate schema first before writing to disk
        is_valid, err = validate_vote_result(result)
        if not is_valid:
            raise ValueError(f"Generated vote_result is invalid: {err}")

        if write_to_disk:
            out_file = self.root / ".macao" / "vote_result.json"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            # Immutability guard (D-1 / Codex P1-4):
            # If vote_result.json already exists for identical task_id, checkpoint_ref, and review_round,
            # verify consistency and reuse existing canonical record without overwriting.
            if out_file.exists():
                try:
                    with open(out_file, "r", encoding="utf-8") as existing_f:
                        existing_data = json.load(existing_f)
                    if (existing_data.get("checkpoint_ref") == checkpoint_ref and
                        existing_data.get("review_round") == review_round and
                        existing_data.get("task_id") == result.get("task_id")):
                        if existing_data.get("decision") == result.get("decision"):
                            return existing_data
                        else:
                            raise ValueError(
                                f"Immutable vote_result.json conflict: existing decision '{existing_data.get('decision')}' "
                                f"differs from newly calculated '{result.get('decision')}' for ref {checkpoint_ref} r{review_round}"
                            )
                except json.JSONDecodeError:
                    pass

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

        return result
