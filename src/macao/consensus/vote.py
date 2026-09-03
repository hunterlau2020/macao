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
        write_to_disk: bool = True,
        timed_out_reviewers: Optional[List[str]] = None,
        task_id: Optional[str] = None,
        reviewer_weights: Optional[Dict[str, int]] = None,
        policy: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculates consensus decision and produces schema-valid vote_result.json.
        Validates schema before writing to disk (Fail-closed).
        Persists timed out reviewers as ABSTAIN in votes and breakdown.
        """
        votes_list = []
        input_artifacts = []
        issues_to_fix = []

        valid_reviews = []
        for r in reviews:
            rev_id = r["data"]["reviewer"]["id"]
            if timed_out_reviewers and rev_id in timed_out_reviewers:
                continue
            valid_reviews.append(r)

        for r in valid_reviews:
            data = r["data"]
            rev_id = data["reviewer"]["id"]
            vote_val = data.get("vote") or data.get("opinion", {}).get("vote")
            if not vote_val:
                continue

            op_data = data.get("opinion", {})
            issues_list = op_data.get("feedback", {}).get("categories", [])
            w = int(reviewer_weights.get(rev_id, data.get("reviewer", {}).get("vote_weight", 1))) if reviewer_weights else int(data.get("reviewer", {}).get("vote_weight", 1))

            votes_list.append({
                "reviewer": rev_id,
                "vote": vote_val,
                "weight": max(1, w),
                "source": "manifest",
                "confidence": float(op_data.get("confidence", 0.9)),
                "issues_count": len(issues_list)
            })

            input_artifacts.append({
                "reviewer": rev_id,
                "kind": "review_manifest",
                "path": r["file_path"],
                "sha256": r.get("sha256", hashlib.sha256(b"").hexdigest()),
                "evidence_commit": checkpoint_ref,
                "message_id": f"msg-rev-{rev_id}"
            })

            for idx, cat in enumerate(issues_list):
                issues_to_fix.append({
                    "id": f"issue-{rev_id}-{idx+1}",
                    "reviewer": rev_id,
                    "type": cat.get("type", "logic"),
                    "severity": cat.get("severity", "major"),
                    "description": cat.get("issue", "")
                })

        # Include timed out reviewers as ABSTAIN (PRD §2.2 / §3.3 / P1-1 / P1-3)
        if timed_out_reviewers:
            for to_rev in timed_out_reviewers:
                if not any(v["reviewer"] == to_rev for v in votes_list):
                    w = int(reviewer_weights.get(to_rev, 1)) if reviewer_weights else 1
                    votes_list.append({
                        "reviewer": to_rev,
                        "vote": Vote.ABSTAIN.value,
                        "weight": max(1, w),
                        "source": "timeout",
                        "confidence": 0.0,
                        "issues_count": 0
                    })

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
                "rule": "weighted_2/3_v1",
                "configured_seats": configured_reviewers,
                "configured_weight": total_configured_weight,
                "seat_quorum_required": seat_quorum,
                "weight_quorum_required": weight_quorum,
                "decision_threshold_numerator": 2,
                "decision_threshold_denominator": 3,
                "minimum_winning_seats": min_winning_seats,
                "dictator_cap_enabled": dictator_cap_enabled,
                "max_single_weight_share_numerator": 2,
                "max_single_weight_share_denominator": 3
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
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

        return result
