"""Unit and Integration tests for Phase 3 Components (LiveDispatcher, Daemon, Wizard, LiveRunner)."""

import os
import unittest
import tempfile
import yaml
from pathlib import Path

from macao.core.types import AgentState, Decision, Vote
from macao.core.schema import SchemaValidator, validate_review_manifest
from macao.workflow.live_dispatcher import ReviewExtractor, LiveAgentDispatcher
from macao.workflow.daemon import OrchestratorDaemon
from macao.workflow.live_runner import LiveWorkflowRunner
from macao.cli.wizard import probe_available_clis, detect_git_context, detect_ci_command, ensure_gitignore_isolation, generate_smart_config


class TestPhase3Engine(unittest.TestCase):

    def test_review_extractor_markdown_fenced_yaml(self):
        """Verify ReviewExtractor successfully parses YAML wrapped in markdown fences."""
        raw_output = """
Here is my review of the changes:
```yaml
version: "1.0"
checkpoint_ref: "4e38ed6a"
review_round: 1
reviewer:
  id: "codex"
  cli: "codex"
vote: "YES_APPROVE"
opinion:
  status: "APPROVED"
  confidence: 0.98
  feedback:
    summary: "Code quality is excellent."
```
Let me know if you need anything else!
"""
        is_val, manifest, err = ReviewExtractor.extract_and_validate(raw_output, "codex", "4e38ed6a", 1)
        self.assertTrue(is_val, f"Extraction failed: {err}")
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest["vote"], "YES_APPROVE")
        self.assertEqual(manifest["opinion"]["status"], "APPROVED")

    def test_review_extractor_self_heals_omitted_metadata(self):
        """Verify ReviewExtractor automatically injects missing baseline fields and harmonizes opinion/vote."""
        raw_output = """
```yaml
opinion:
  status: "APPROVED"
  confidence: 0.90
  feedback:
    summary: "Looks good"
```
"""
        is_val, manifest, err = ReviewExtractor.extract_and_validate(raw_output, "opencode", "abc1234", 2)
        self.assertTrue(is_val, f"Self-healing extraction failed: {err}")
        self.assertEqual(manifest["reviewer"]["id"], "opencode")
        self.assertEqual(manifest["checkpoint_ref"], "abc1234")
        self.assertEqual(manifest["review_round"], 2)
        self.assertEqual(manifest["vote"], "YES_APPROVE")

    def test_review_extractor_rejects_missing_vote_and_status(self):
        """Verify ReviewExtractor strictly fails closed on arbitrary/non-review YAML."""
        non_review_samples = [
            "```yaml\nnote: I ran out of context\n```",
            "```yaml\nmodel: gemini-2.0-pro\ntemperature: 0.2\n```",
            "```yaml\nfoo: 1\n```",
            "```yaml\n{}\n```",
            "This change is UNSAFE and must not be merged."
        ]
        for sample in non_review_samples:
            is_val, manifest, err = ReviewExtractor.extract_and_validate(sample, "codex", "abc1234", 1)
            self.assertFalse(is_val, f"Expected sample to fail extraction: {sample}")
            self.assertIsNone(manifest)

    def test_review_extractor_rejects_mismatched_context(self):
        """Verify ReviewExtractor rejects YAML containing wrong checkpoint_ref, round, or reviewer ID."""
        # 1. Mismatched checkpoint_ref
        mismatched_ref = """
```yaml
checkpoint_ref: "stale-commit-999"
vote: "YES_APPROVE"
opinion:
  status: "APPROVED"
```
"""
        is_val, _, _ = ReviewExtractor.extract_and_validate(mismatched_ref, "codex", "expected-ref-111", 1)
        self.assertFalse(is_val)

        # 2. Mismatched review_round
        mismatched_round = """
```yaml
review_round: 99
vote: "YES_APPROVE"
opinion:
  status: "APPROVED"
```
"""
        is_val, _, _ = ReviewExtractor.extract_and_validate(mismatched_round, "codex", "expected-ref-111", 1)
        self.assertFalse(is_val)

        # 3. Mismatched reviewer ID
        mismatched_reviewer = """
```yaml
reviewer:
  id: "opencode"
vote: "YES_APPROVE"
opinion:
  status: "APPROVED"
```
"""
        is_val, _, _ = ReviewExtractor.extract_and_validate(mismatched_reviewer, "codex", "expected-ref-111", 1)
        self.assertFalse(is_val)

    def test_wizard_probes_and_smart_config(self):
        """Verify setup wizard auto-discovery functions work correctly without raising exceptions."""
        clis = probe_available_clis()
        self.assertIsInstance(clis, list)

        with tempfile.TemporaryDirectory() as tmpdir:
            proj = Path(tmpdir)
            (proj / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
            ci = detect_ci_command(proj)
            self.assertEqual(ci, "pytest -q")

            cfg = generate_smart_config(proj, executor_cli="opencode", executor_model="GLM 5.3 max")
            self.assertEqual(cfg["team"]["executor"]["model"], "GLM 5.3 max")
            self.assertEqual(cfg["merge"]["ci_gate_command"], "pytest -q")

            # Verify .gitignore isolation injection
            added = ensure_gitignore_isolation(proj)
            self.assertTrue(added)
            gi_content = (proj / ".gitignore").read_text(encoding="utf-8")
            self.assertIn(".macao/worktrees/", gi_content)
            self.assertIn(".macao/.reviews/", gi_content)

            # Second call is idempotent
            added_again = ensure_gitignore_isolation(proj)
            self.assertFalse(added_again)

    def test_daemon_scanner_single_tick_idle(self):
        """Verify daemon scanner handles empty/idle state gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            daemon = OrchestratorDaemon(tmpdir)
            res = daemon.scan_once()
            self.assertIsNone(res["active_task"])
            self.assertEqual(res["action_taken"], "NONE")

    def test_daemon_active_task_timeout_degradation(self):
        """Verify daemon scans active WAITING_REVIEW task, identifies timeout, and records ABSTAIN."""
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            proj = Path(tmpdir)
            # Init git repo
            subprocess.run(["git", "init", "-b", "main"], cwd=str(proj), check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=str(proj), check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(proj), check=True)
            (proj / "README.md").write_text("initial", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=str(proj), check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=str(proj), check=True, capture_output=True)

            # Config with 0s timeout
            cfg_yaml = """
project:
  name: "daemon-test"
  repository:
    workspace_path: "."
    remote_name: "origin"
    default_branch: "main"
team:
  executor: { id: "dev", cli: "opencode", adapter: "pty-wrapper" }
  reviewers:
    - { id: "rev1", cli: "opencode", adapter: "pty-wrapper" }
    - { id: "rev2", cli: "codex", adapter: "pty-wrapper" }
timeouts:
  per_reviewer: "0s"
"""
            (proj / "macao.yaml").write_text(cfg_yaml, encoding="utf-8")

            daemon = OrchestratorDaemon(str(proj))
            # Start a task and move to WAITING_REVIEW
            task = daemon.orchestrator.start_task("Timeout Test", "desc")
            t_id = task["task_id"]

            (proj / "code.py").write_text("print(1)", encoding="utf-8")
            subprocess.run(["git", "add", "code.py"], cwd=str(proj), check=True)
            subprocess.run(["git", "commit", "-m", "add code"], cwd=str(proj), check=True, capture_output=True)
            head = daemon.orchestrator.git.get_head_commit()

            (proj / ".macao").mkdir(parents=True, exist_ok=True)
            (proj / ".macao" / ".dev.yml").write_text(yaml.safe_dump({
                "version": "1.0", "status": "ready_for_review", "signal": "EXPLICIT",
                "review_round": 1, "executor": {"id": "dev", "cli": "opencode"},
                "development": {"git": {"latest_commit": head}, "quality_metrics": {"tests_passed": True}}
            }), encoding="utf-8")

            daemon.orchestrator.check_development_checkpoint(t_id)
            daemon.orchestrator.dispatch_review_requests(t_id)

            # Task is now in WAITING_REVIEW
            curr_task = daemon.store.get_task(t_id)
            self.assertEqual(curr_task["state"], AgentState.WAITING_REVIEW.value)

            # Run daemon scanner
            res = daemon.scan_once()
            self.assertEqual(res["action_taken"], "TIMEOUT_DEGRADATION")
            self.assertIn("rev1", res["timed_out_reviewers"])
            self.assertIn("rev2", res["timed_out_reviewers"])

            # Verify audit events
            audits = daemon.store.get_audit_events_by_type(t_id, "REVIEWER_TIMEOUT_ABSTAIN")
            self.assertEqual(len(audits), 2)

    def test_live_workflow_runner_end_to_end_cycle(self):
        """Verify Phase 3 LiveWorkflowRunner executes complete lifecycle cleanly."""
        runner = LiveWorkflowRunner()
        try:
            res = runner.run_live_cycle()
            self.assertEqual(res["status"], "PASS")
            self.assertEqual(res["final_state"], AgentState.DONE.value)
            self.assertEqual(len(res["steps"]), 7)
            self.assertGreater(res["archived_count"], 0)
        finally:
            runner.cleanup()


if __name__ == "__main__":
    unittest.main()
