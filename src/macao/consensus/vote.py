"""Vote Aggregator and vote_result.json Generator (PRD §2.3)."""

import os
import json
import yaml
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from macao.core.types import Decision, Resolution
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
        write_to_disk: bool = True
    ) -> Dict[str, Any]:
        """
        Calculates consensus decision and produces schema-valid vote_result.json.
        """
        votes_list = []
        input_artifacts = []
        issues_to_fix = []

        for r in reviews:
            data = r["data"]
            rev_id = data["reviewer"]["id"]
            vote_val = data["vote"]
            op_data = data.get("opinion", {})
            issues_list = op_data.get("feedback", {}).get("categories", [])

            votes_list.append({
                "reviewer": rev_id,
                "vote": vote_val,
                "confidence": float(op_data.get("confidence", 0.9)),
                "issues_count": len(issues_list)
            })

            input_artifacts.append({
                "kind": "review_manifest",
                "path": r["file_path"],
                "sha256": r["sha256"],
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

        decision, breakdown, confidence = ConsensusEngine.evaluate(votes_list, configured_reviewers)

        resolution_type = Resolution.AUTOMATIC.value
        if human_resolution:
            resolution_type = Resolution.HUMAN_OVERRIDE.value
            if human_resolution == "APPROVED":
                decision = Decision.APPROVED
            elif human_resolution in ("REWORK", "REWORK_REQUIRED"):
                decision = Decision.REWORK_REQUIRED
            elif human_resolution in ("RETRY", "RETRY_REVIEW"):
                decision = Decision.RETRY_REVIEW
            elif human_resolution in ("CANCEL", "CANCELLED"):
                decision = Decision.CANCELLED
            else:
                decision = Decision.APPROVED

        next_action_map = {
            Decision.APPROVED: "MERGE",
            Decision.REWORK_REQUIRED: "REWORK",
            Decision.RETRY_REVIEW: "RETRY_REVIEW"
        }
        next_action = next_action_map.get(decision)

        result: Dict[str, Any] = {
            "version": "1.0",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "checkpoint_ref": checkpoint_ref,
            "executor": executor_id,
            "review_round": review_round,
            "reviewers_total": configured_reviewers,
            "reviewers_responded": len(reviews),
            "votes": votes_list,
            "input_artifacts": input_artifacts,
            "consensus_rule": "2/3_majority",
            "vote_breakdown": breakdown,
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

        # PRD §3.3 E3 Rule: If decision is DEADLOCK, DO NOT write to disk
        if decision == Decision.DEADLOCK:
            return result

        if write_to_disk:
            out_file = self.root / ".macao" / "vote_result.json"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

        is_valid, err = validate_vote_result(result)
        if not is_valid:
            raise ValueError(f"Generated vote_result is invalid: {err}")

        return result
