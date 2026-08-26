"""Unit tests for SchemaValidator and docs/schemas/."""

import unittest
from macao.core.schema import (
    validate_dev_manifest,
    validate_review_manifest,
    validate_vote_result,
    validate_review_context,
    validate_aep_envelope,
    validate_config,
)


class TestSchemaValidation(unittest.TestCase):

    def test_dev_manifest_schema(self):
        valid_dev = {
            "version": "1.0",
            "timestamp": "2026-08-27T00:00:00Z",
            "executor": {"id": "cc-ds4", "role": "executor", "cli": "claude-code"},
            "development": {
                "description": "Refactor database pool",
                "artifacts": [{"path": "src/db.py"}],
                "quality_metrics": {"tests_passed": True},
                "git": {"latest_commit": "a1b2c3d"}
            },
            "review_round": 1,
            "status": "ready_for_review",
            "signal": "EXPLICIT"
        }
        is_valid, err = validate_dev_manifest(valid_dev)
        self.assertTrue(is_valid, f"Expected valid dev manifest, got: {err}")

        invalid_dev = dict(valid_dev)
        invalid_dev.pop("signal")
        is_valid, _ = validate_dev_manifest(invalid_dev)
        self.assertFalse(is_valid)

    def test_review_manifest_schema(self):
        valid_rev = {
            "version": "1.0",
            "timestamp": "2026-08-27T00:00:00Z",
            "reviewer": {"id": "cc-glm", "cli": "codex"},
            "checkpoint_ref": "a1b2c3d",
            "review_round": 1,
            "opinion": {"status": "APPROVED", "confidence": 0.95},
            "vote": "YES_APPROVE"
        }
        is_valid, err = validate_review_manifest(valid_rev)
        self.assertTrue(is_valid, f"Expected valid review manifest, got: {err}")

        conflict_rev = dict(valid_rev)
        conflict_rev["vote"] = "NO_APPROVE"
        is_valid, _ = validate_review_manifest(conflict_rev)
        self.assertFalse(is_valid)

    def test_vote_result_schema(self):
        valid_vote = {
            "version": "1.0",
            "timestamp": "2026-08-27T00:00:00Z",
            "checkpoint_ref": "a1b2c3d",
            "executor": "cc-ds4",
            "review_round": 1,
            "reviewers_total": 2,
            "reviewers_responded": 2,
            "votes": [{"reviewer": "cc-glm", "vote": "YES_APPROVE"}],
            "input_artifacts": [{"kind": "review", "path": "p.yml", "sha256": "abc", "message_id": "m1"}],
            "consensus_rule": "2/3_majority",
            "vote_breakdown": {"approve": 2, "reject": 0, "abstain": 0},
            "decision": "APPROVED",
            "resolution": "automatic"
        }
        is_valid, err = validate_vote_result(valid_vote)
        self.assertTrue(is_valid, f"Expected valid vote_result, got: {err}")

    def test_aep_envelope_schema(self):
        msg = {
            "protocol": "AEP/1.0",
            "message_id": "msg-20260827-001",
            "timestamp": "2026-08-27T00:00:00Z",
            "type": "DEVELOPMENT_STARTED",
            "from": "macao",
            "to": "cc-ds4",
            "payload": {"task": "test"}
        }
        is_valid, err = validate_aep_envelope(msg)
        self.assertTrue(is_valid, f"Expected valid AEP envelope, got: {err}")


if __name__ == "__main__":
    unittest.main()
