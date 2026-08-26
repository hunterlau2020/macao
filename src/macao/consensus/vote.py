"""Vote Aggregator and vote_result.json Generator (PRD §2.3)."""

import os
import json
import yaml
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from macao.core.types import Decision, Resolution
from macao.consensus.engine import ConsensusEngine
from macao.core.schema import validate_review_manifest, validate_vote_result


class VoteAggregator:
    """Collects .review.yml files, applies consensus rules, and generates vote_result.json."""

    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)

    def collect_reviews(self, checkpoint_ref: str, review_round: int) -> List[Dict[str, Any]]:
        """Scans .macao/.reviews/ for valid .review.yml files matching ref and round."""
        reviews_dir = self.root / ".macao" / ".reviews"
        if not reviews_dir.exists():
            return []

        collected = []
        for file_path in reviews_dir.glob("*.review.yml"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                
                is_valid, _ = validate_review_manifest(content)
                if not is_valid:
                    continue

                if (content.get("checkpoint_ref") == checkpoint_ref and 
                    content.get("review_round") == review_round):
                    
                    with open(file_path, "rb") as f_bin:
                        sha256 = hashlib.sha256(f_bin.read()).hexdigest()

                    collected.append({
                        "file_path": str(file_path.relative_to(self.root)),
                        "data": content,
                        "sha256": sha256
                    })
            except Exception:
                continue

        return collected

    def generate_vote_result(
        self,
        checkpoint_ref: str,
        executor_id: str,
        review_round: int,
        configured_reviewers: int,
        reviews: List[Dict[str, Any]],
        human_resolution: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synthesizes vote_result.json payload."""
        votes_list = []
        input_artifacts = []
        issues_to_fix = []

        for r in reviews:
            data = r["data"]
            reviewer_id = data.get("reviewer", {}).get("id", "unknown")
            vote_val = data.get("vote")
            confidence = data.get("opinion", {}).get("confidence", 0.9)
            feedback = data.get("opinion", {}).get("feedback", {})

            # Count issues if structured
            categories = feedback.get("categories", [])
            issues_count = len(categories)

            votes_list.append({
                "reviewer": reviewer_id,
                "vote": vote_val,
                "confidence": confidence,
                "issues_count": issues_count
            })

            input_artifacts.append({
                "kind": "review",
                "path": r["file_path"],
                "sha256": r["sha256"],
                "message_id": f"msg-local-{reviewer_id}"
            })

            # Extract issues
            for idx, cat in enumerate(categories, 1):
                issues_to_fix.append({
                    "id": f"{reviewer_id}/{idx}",
                    "type": cat.get("type", "logic"),
                    "severity": cat.get("severity", "major"),
                    "description": cat.get("issue", "")
                })

        decision, breakdown, confidence = ConsensusEngine.evaluate(votes_list, configured_reviewers)
        
        # Override decision if specified by human
        resolution_type = Resolution.AUTOMATIC.value
        if human_resolution:
            resolution_type = Resolution.HUMAN_OVERRIDE.value
            if human_resolution == "APPROVED":
                decision = Decision.APPROVED
            elif human_resolution == "REWORK":
                decision = Decision.REWORK_REQUIRED

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
            "decision": decision.value if decision != Decision.DEADLOCK else "REWORK_REQUIRED",
            "decision_confidence": confidence,
            "resolution": resolution_type,
            "summary": {
                "critical_issues": sum(1 for i in issues_to_fix if i.get("severity") == "critical"),
                "major_issues": sum(1 for i in issues_to_fix if i.get("severity") == "major"),
                "minor_issues": sum(1 for i in issues_to_fix if i.get("severity") == "minor"),
                "action": "Proceed to merge" if decision == Decision.APPROVED else "Send REWORK_REQUEST to executor"
            },
            "next_step": {
                "action": "MERGE" if decision == Decision.APPROVED else "REWORK",
                "issues_to_fix": issues_to_fix
            }
        }

        # Write to disk
        out_file = self.root / ".macao" / "vote_result.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        return result
