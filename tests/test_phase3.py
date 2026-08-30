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

    def test_wizard_probes_and_smart_config(self):
        """Verify setup wizard auto-discovery functions work correctly without raising exceptions."""
        clis = probe_available_clis()
        self.assertIsInstance(clis, list)
        self.assertTrue(len(clis) > 0)

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

    def test_live_workflow_runner_end_to_end_cycle(self):
        """Verify Phase 3 LiveWorkflowRunner executes complete lifecycle cleanly."""
        runner = LiveWorkflowRunner()
        try:
            res = runner.run_live_cycle()
            self.assertEqual(res["status"], "PASS")
            self.assertEqual(res["final_state"], AgentState.DONE.value)
            self.assertEqual(len(res["steps"]), 7)
        finally:
            runner.cleanup()


if __name__ == "__main__":
    unittest.main()
