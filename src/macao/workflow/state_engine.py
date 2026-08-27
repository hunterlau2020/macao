"""Three-Layer State Recognition Engine with Scoped Artifact Reading (PRD §3.2)."""

import os
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Set

from macao.core.types import AgentState
from macao.core.schema import validate_dev_manifest, validate_review_manifest, validate_vote_result
from macao.consensus.engine import ConsensusEngine


class StateRecognitionEngine:
    """Recognizes FSM state transitions based on Layer 1 explicit signals and scope filtering."""

    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)

    def recognize_state(
        self,
        current_state: AgentState,
        checkpoint_ref: Optional[str],
        review_round: int,
        configured_reviewers: int = 2,
        max_rework_rounds: int = 3
    ) -> Tuple[Optional[AgentState], Optional[str], Dict[str, Any]]:
        """
        Scoped State Recognition (PRD §3.2):

        Returns:
            (target_state, transition_source, meta_dict)
        """
        # Layer 1a: Development Artifact .dev.yml (Only accepted in CODING or REWORK)
        if current_state in (AgentState.CODING, AgentState.REWORK):
            dev_path = self.root / ".macao" / ".dev.yml"
            if dev_path.exists():
                try:
                    with open(dev_path, "r", encoding="utf-8") as f:
                        dev_data = yaml.safe_load(f)

                    is_valid, _ = validate_dev_manifest(dev_data)
                    if (is_valid and
                        dev_data.get("signal") == "EXPLICIT" and
                        dev_data.get("status") == "ready_for_review" and
                        dev_data.get("review_round", 1) == review_round):

                        commit = dev_data.get("development", {}).get("git", {}).get("latest_commit")
                        qm = dev_data.get("development", {}).get("quality_metrics", {})
                        tests_ok = (qm.get("tests_passed") is True or qm.get("tests_exempt") is True)

                        if commit and tests_ok:
                            return (
                                AgentState.READY_FOR_REVIEW,
                                "E1_PRODUCED",
                                {"latest_commit": commit, "review_round": review_round}
                            )
                except Exception:
                    pass

        # Layer 1b: WAITING_REVIEW -> CONSENSUS_CHECK (When valid unique reviewer reviews >= minimum quorum)
        elif current_state == AgentState.WAITING_REVIEW and checkpoint_ref:
            reviews_dir = self.root / ".macao" / ".reviews"
            if reviews_dir.exists():
                valid_reviewers: Set[str] = set()
                for rev_file in reviews_dir.glob("*.review.yml"):
                    try:
                        with open(rev_file, "r", encoding="utf-8") as f:
                            rdata = yaml.safe_load(f)
                        is_valid, _ = validate_review_manifest(rdata)
                        if (is_valid and
                            rdata.get("checkpoint_ref") == checkpoint_ref and
                            rdata.get("review_round") == review_round):

                            rev_id = rdata.get("reviewer", {}).get("id")
                            if rev_id:
                                valid_reviewers.add(rev_id)
                    except Exception:
                        continue

                quorum = ConsensusEngine.calculate_minimum_quorum(configured_reviewers)
                if len(valid_reviewers) >= quorum:
                    return (
                        AgentState.CONSENSUS_CHECK,
                        "E3",
                        {"valid_reviews_count": len(valid_reviewers), "minimum_quorum": quorum}
                    )

        # Layer 1c: CONSENSUS_CHECK -> MERGING, REWORK, WAITING_REVIEW, or CANCELLED (Only from vote_result.json)
        elif current_state == AgentState.CONSENSUS_CHECK and checkpoint_ref:
            vote_file = self.root / ".macao" / "vote_result.json"
            if vote_file.exists():
                try:
                    with open(vote_file, "r", encoding="utf-8") as f:
                        vdata = json.load(f)
                    is_valid, _ = validate_vote_result(vdata)
                    if (is_valid and
                        vdata.get("checkpoint_ref") == checkpoint_ref and
                        vdata.get("review_round") == review_round):

                        decision = vdata.get("decision")
                        if decision == "APPROVED":
                            return AgentState.MERGING, "E4", vdata
                        elif decision == "REWORK_REQUIRED":
                            if review_round < max_rework_rounds:
                                return AgentState.REWORK, "E5", vdata
                            else:
                                # Max rework rounds reached -> request human override
                                return None, "MAX_REWORK_REACHED", vdata
                        elif decision == "RETRY_REVIEW":
                            return AgentState.WAITING_REVIEW, "E9", vdata
                        elif decision == "CANCELLED":
                            return AgentState.CANCELLED, "E10", vdata
                except Exception:
                    pass

        # No explicit signal triggered -> HOLD state
        return None, "HOLD", {}
