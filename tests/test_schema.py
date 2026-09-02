"""Unit tests for SchemaValidator, docs/schemas/ and src/macao/schemas/."""

import glob
import json
import os
import unittest
import yaml

from macao.core.schema import (
    SchemaValidator,
    validate_dev_manifest,
    validate_review_manifest,
    validate_vote_result,
    validate_review_context,
    validate_aep_envelope,
    validate_config,
    validate_review_disposition,
    validate_admin_override,
)


class TestSchemaValidation(unittest.TestCase):

    def test_dev_manifest_schema(self):
        valid_dev = {
            "version": "1.0",
            "timestamp": "2026-09-01T00:00:00Z",
            "task_id": "task-123",
            "checkpoint_ref": "a1b2c3d",
            "review_round": 1,
            "executor": {"id": "cc-ds4", "role": "executor", "cli": "claude-code"},
            "full_document": {
                "path": "docs/reviews/task-123.md",
                "evidence_commit": "a1b2c3d",
                "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            },
            "development": {
                "description": "Refactor database pool",
                "artifacts": [{"path": "src/db.py"}],
                "quality_metrics": {"tests_passed": True},
                "git": {"latest_commit": "a1b2c3d"}
            },
            "status": "ready_for_review",
            "signal": "EXPLICIT"
        }
        is_valid, err = validate_dev_manifest(valid_dev)
        self.assertTrue(is_valid, f"Expected valid dev manifest, got: {err}")

        invalid_dev = dict(valid_dev)
        invalid_dev.pop("signal")
        is_valid, _ = validate_dev_manifest(invalid_dev)
        self.assertFalse(is_valid)

    def test_review_manifest_schema_and_interlocking(self):
        valid_rev = {
            "version": "1.0",
            "timestamp": "2026-09-01T00:00:00Z",
            "reviewer": {"id": "codex", "cli": "codex"},
            "checkpoint_ref": "a1b2c3d",
            "review_round": 1,
            "opinion": {"status": "APPROVED", "confidence": 0.95},
            "vote": "YES_APPROVE",
            "items": []
        }
        is_valid, err = validate_review_manifest(valid_rev)
        self.assertTrue(is_valid, f"Expected valid review manifest, got: {err}")

        # Interlocking test 1: BLOCKING issue + YES_APPROVE must fail
        invalid_yes = dict(valid_rev)
        invalid_yes["items"] = [{"issue_id": "c/1", "disposition_class": "BLOCKING", "severity": "critical", "title": "t"}]
        is_valid, _ = validate_review_manifest(invalid_yes)
        self.assertFalse(is_valid, "YES_APPROVE with BLOCKING item must fail schema")

        # Interlocking test 2: NO_APPROVE with no BLOCKING items must fail
        invalid_no = dict(valid_rev)
        invalid_no["opinion"] = {"status": "CHANGES_REQUESTED", "confidence": 0.9}
        invalid_no["vote"] = "NO_APPROVE"
        invalid_no["items"] = []
        is_valid, _ = validate_review_manifest(invalid_no)
        self.assertFalse(is_valid, "NO_APPROVE with empty items must fail schema")

        # Interlocking test 3: ABSTAIN without abstain_reason must fail
        invalid_abstain = dict(valid_rev)
        invalid_abstain["opinion"] = {"status": "ABSTAINED", "confidence": 0.0}
        invalid_abstain["vote"] = "ABSTAIN"
        is_valid, _ = validate_review_manifest(invalid_abstain)
        self.assertFalse(is_valid, "ABSTAIN without abstain_reason must fail schema")

    def test_vote_result_schema_v25_strict_decision(self):
        valid_vote = {
            "version": "1.0",
            "timestamp": "2026-09-01T00:00:00Z",
            "checkpoint_ref": "a1b2c3d",
            "review_round": 1,
            "reviewers_total": 2,
            "reviewers_responded": 2,
            "reviewers_accounted": 2,
            "votes": [
                {"reviewer": "codex", "vote": "YES_APPROVE", "weight": 1},
                {"reviewer": "kimi", "vote": "YES_APPROVE", "weight": 1}
            ],
            "policy_snapshot": {
                "rule": "weighted_2/3_v1",
                "configured_seats": 2,
                "configured_weight": 2,
                "seat_quorum_required": 2,
                "weight_quorum_required": 2,
                "decision_threshold_numerator": 2,
                "decision_threshold_denominator": 3,
                "minimum_winning_seats": 2,
                "dictator_cap_enabled": True
            },
            "vote_breakdown": {
                "effective_seats": 2,
                "effective_weight": 2,
                "approve_seats": 2,
                "approve_weight": 2,
                "reject_seats": 0,
                "reject_weight": 0,
                "abstain_seats": 0,
                "abstain_weight": 0
            },
            "input_artifacts": [{"path": ".macao/.reviews/codex.review.yml"}],
            "issues_index": [],
            "issues_index_sha256": "3a7b1c4e9f0d2a8b5c6e7f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c",
            "requires_disposition": False,
            "decision": "APPROVED",
            "resolution": "AUTO_WEIGHTED_CONSENSUS"
        }
        is_valid, err = validate_vote_result(valid_vote)
        self.assertTrue(is_valid, f"Expected valid vote_result, got: {err}")

        # Negative test: RETRY_REVIEW or CANCELLED as machine decision must be rejected
        invalid_retry = dict(valid_vote)
        invalid_retry["decision"] = "RETRY_REVIEW"
        is_valid, _ = validate_vote_result(invalid_retry)
        self.assertFalse(is_valid, "RETRY_REVIEW must be rejected as machine decision in vote_result")

        invalid_cancelled = dict(valid_vote)
        invalid_cancelled["decision"] = "CANCELLED"
        is_valid, _ = validate_vote_result(invalid_cancelled)
        self.assertFalse(is_valid, "CANCELLED must be rejected as machine decision in vote_result")

    def test_review_disposition_schema(self):
        valid_disp = {
            "version": "1.0",
            "task_id": "task-123",
            "checkpoint_ref": "a1b2c3d",
            "review_round": 1,
            "executor": {"id": "cc-ds4"},
            "full_document": {
                "path": "docs/reviews/disp.md",
                "evidence_commit": "a1b2c3d",
                "sha256": "abc"
            },
            "issues_index_sha256": "3a7b1c4e9f0d2a8b5c6e7f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c",
            "disposition_status": "FINAL",
            "dispositions": [
                {
                    "issue_id": "codex/1",
                    "disposition_type": "ADOPTED",
                    "requires_new_checkpoint": True,
                    "rationale": "Fixed code"
                }
            ]
        }
        is_valid, err = validate_review_disposition(valid_disp)
        self.assertTrue(is_valid, f"Expected valid review disposition, got: {err}")

        # Negative test: FINAL with unresolved NEEDS_ADMIN must fail
        invalid_disp = dict(valid_disp)
        invalid_disp["dispositions"] = [
            {
                "issue_id": "codex/1",
                "disposition_type": "NEEDS_ADMIN",
                "requires_new_checkpoint": False,
                "rationale": "Pending admin"
            }
        ]
        is_valid, _ = validate_review_disposition(invalid_disp)
        self.assertFalse(is_valid, "FINAL disposition with NEEDS_ADMIN must fail schema")

    def test_admin_override_schema(self):
        valid_ovr = {
            "override_id": "ovr-1",
            "timestamp": "2026-09-01T00:00:00Z",
            "task_id": "task-123",
            "checkpoint_ref": "a1b2c3d",
            "review_round": 1,
            "admin_identity": "admin@macao.local",
            "trigger": "consensus_deadlock",
            "choice": "APPROVED"
        }
        is_valid, err = validate_admin_override(valid_ovr)
        self.assertTrue(is_valid, f"Expected valid admin override, got: {err}")

    def test_aep_envelope_schema(self):
        msg = {
            "protocol": "AEP/1.1",
            "message_id": "msg-20260901-001",
            "timestamp": "2026-09-01T00:00:00Z",
            "type": "DEVELOPMENT_STARTED",
            "from": "macao",
            "to": "cc-ds4",
            "payload": {
                "task_id": "task-123",
                "specification_summary": "Implement feature X",
                "acceptance_criteria": ["All unit tests pass"]
            }
        }
        is_valid, err = validate_aep_envelope(msg)
        self.assertTrue(is_valid, f"Expected valid AEP envelope, got: {err}")

    def test_all_fixtures_conformance(self):
        """Verify all valid fixtures pass and all invalid fixtures are rejected."""
        sv = SchemaValidator()
        schema_map = {
            "dev.yml": "dev_manifest",
            "review.yml": "review_manifest",
            "vote_result.json": "vote_result",
            "disposition.yml": "review_disposition",
            "admin_override.json": "admin_override",
            "aep_review_request.json": "aep_envelope",
            "review_context_full.json": "review_context",
            "review_context_minimal.json": "review_context",
            "macao_config.yaml": "macao_config",
            "macao_config_local_only.yaml": "macao_config",
        }
        for vf in sorted(glob.glob("docs/schemas/fixtures/valid/*")):
            fname = os.path.basename(vf)
            s_name = schema_map[fname]
            with open(vf) as f:
                content = yaml.safe_load(f) if vf.endswith((".yml", ".yaml")) else json.load(f)
            valid, err = sv.validate(s_name, content)
            self.assertTrue(valid, f"Valid fixture {fname} failed {s_name} validation: {err}")

        invalid_map = {
            "admin_override_invalid_choice.json": "admin_override",
            "aep_unknown_type.json": "aep_envelope",
            "aep_type_a_empty_payload.json": "aep_envelope",
            "aep_type_b_empty_payload.json": "aep_envelope",
            "aep_payload_oversized.json": "aep_envelope",
            "context_missing_refs.json": "review_context",
            "dev_missing_core_fields.yml": "dev_manifest",
            "disposition_deferred_with_new_checkpoint.yml": "review_disposition",
            "disposition_final_with_needs_admin.yml": "review_disposition",
            "disposition_rejected_with_new_checkpoint.yml": "review_disposition",
            "macao_config_missing_policy.yaml": "macao_config",
            "macao_config_minimum_seats_one.yaml": "macao_config",
            "macao_config_dictator_cap_false.yaml": "macao_config",
            "review_abstain_invalid.yml": "review_manifest",
            "review_status_vote_conflict.yml": "review_manifest",
            "vote_result_cancelled_decision.json": "vote_result",
        }
        for ivf in sorted(glob.glob("docs/schemas/fixtures/invalid/*")):
            fname = os.path.basename(ivf)
            s_name = invalid_map[fname]
            with open(ivf) as f:
                content = yaml.safe_load(f) if ivf.endswith((".yml", ".yaml")) else json.load(f)
            valid, err = sv.validate(s_name, content)
            self.assertFalse(valid, f"Invalid fixture {fname} was expected to fail {s_name} but passed!")


if __name__ == "__main__":
    unittest.main()
