"""Unit tests verifying P0 and P1 rectifications from 4-expert review of 906b17e."""

import os
import unittest
import tempfile
import subprocess
from pathlib import Path

from macao.core.config import ConfigManager
from macao.core.types import AgentState, ExecutionMode
from macao.adapter.mock import MockAgentAdapter
from macao.workflow.orchestrator import Orchestrator
from macao.merge.controller import MergeController
from macao.utils.git_utils import GitManager
from macao.workflow.e2e_runner import ControlledE2ERunner


class TestP0P1Rectification(unittest.TestCase):

    def test_config_keys_penetration_and_require_signoff_fail_closed(self):
        """P0-1: Verify config keys penetration to Orchestrator and signoff fail-closed gate."""
        tmpdir = tempfile.mkdtemp()
        try:
            cfg_file = Path(tmpdir) / "macao.yaml"
            cfg_content = """project:
  name: "test-signoff"
  repository:
    workspace_path: "."
    remote_name: "origin"
    default_branch: "main"

team:
  executor:
    id: "claude-code"
    cli: "claude-code"
    adapter: "claude-hook"
  reviewers:
    - id: "codex"
      cli: "codex"
      adapter: "pty-wrapper"
    - id: "opencode"
      cli: "opencode"
      adapter: "pty-wrapper"

policy:
  consensus_rule: "2/3_majority"
  min_effective_votes: 2
  max_rework_rounds: 5
  review_strategy: "delta_plus_focus"

merge:
  strategy: "ff_only"
  ci_gate_command: "pytest tests"
  require_human_signoff: true
  rebase_before_merge: false
"""
            cfg_file.write_text(cfg_content, encoding="utf-8")
            config = ConfigManager.load_config(str(cfg_file))

            # 1. Verify ConfigManager extracted normalized keys
            self.assertTrue(config["require_signoff"])
            self.assertEqual(config["max_rework_rounds"], 5)
            self.assertEqual(config["ci_gate_command"], "pytest tests")
            self.assertEqual(config["remote_name"], "origin")
            self.assertEqual(config["target_branch"], "main")
            self.assertEqual(config["reviewer_ids"], ["codex", "opencode"])

            # 2. Verify Orchestrator initialized with these exact keys
            orchestrator = Orchestrator(project_root=tmpdir, config=config)
            self.assertTrue(orchestrator.config["require_signoff"])
            self.assertEqual(orchestrator.config["max_rework_rounds"], 5)
            self.assertEqual(orchestrator.config["ci_gate_command"], "pytest tests")
            self.assertEqual(orchestrator.config["reviewer_ids"], ["codex", "opencode"])

            # 3. Verify merge is blocked when require_signoff is True without human signoff
            orchestrator.store.create_task("task-signoff", "Signoff Task", "feat", "main")
            orchestrator.store.update_task_state("task-signoff", AgentState.MERGING, checkpoint_ref="dummy-ref")
            ok, msg, _ = orchestrator.execute_merge("task-signoff")
            self.assertFalse(ok)
            self.assertIn("Human signoff required", msg)
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_merge_controller_non_git_fail_closed(self):
        """P1-2: Verify MergeController returns False (fail-closed) on non-git directory."""
        tmpdir = tempfile.mkdtemp()
        try:
            from macao.storage.store import StateStore
            store = StateStore(os.path.join(tmpdir, "state.db"))
            store.create_task("task-nogit", "Non Git Task", "feat", "main")
            store.update_task_state("task-nogit", AgentState.MERGING, checkpoint_ref="c-123")

            ctrl = MergeController(store, project_root=tmpdir)
            ok, msg, _ = ctrl.execute_merge_pipeline("task-nogit", require_signoff=False)
            self.assertFalse(ok)
            self.assertIn("not a valid git repository", msg)
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_git_utils_fail_closed_and_no_dummy_data(self):
        """P1-3 & P1-6: Verify worktree creation fail-closed on non-git and no fake diff files."""
        tmpdir = tempfile.mkdtemp()
        try:
            git = GitManager(tmpdir)
            # Fail-closed on worktree creation
            with self.assertRaises(RuntimeError) as ctx:
                git.create_isolated_worktree("codex", "task-1", 1, "c-123")
            self.assertIn("not a valid git repository", str(ctx.exception))

            # No fake dummy diff fallback
            changed = git.get_changed_files("main", "feat")
            self.assertEqual(changed, [])
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_e2e_runner_truthful_evidence_and_archive(self):
        """P0-2: Verify E2E runner executes with 3 reviewers, votes_yes=3, and non-empty archive."""
        runner = ControlledE2ERunner()
        try:
            res = runner.run_e2e_cycle()
            self.assertEqual(res["status"], "PASS")
            self.assertEqual(res["final_state"], "DONE")
            self.assertEqual(res["decision"], "APPROVED")
            self.assertTrue(res["merge_exact_match"])

            # Verify step 3 dispatched to 3 reviewers
            step3 = [s for s in res["steps"] if s.get("step") == "3. Worktree Dispatch"][0]
            self.assertEqual(step3["reviewers_count"], 3)
            self.assertEqual(step3["reviewers"], ["codex", "opencode", "antigravity"])

            # Verify step 4 consensus has votes_yes=3, effective_votes=3
            step4 = [s for s in res["steps"] if s.get("step") == "4. Consensus Evaluation"][0]
            self.assertEqual(step4["votes_yes"], 3)
            self.assertEqual(step4["effective_votes"], 3)

            # Verify physical archive persisted
            self.assertGreaterEqual(res["archived_count"], 4)
            self.assertIn(".dev.yml", res["archived_files"])
            self.assertIn("vote_result.json", res["archived_files"])
        finally:
            runner.cleanup()


if __name__ == "__main__":
    unittest.main()
