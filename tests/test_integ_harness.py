"""Unit and Integration tests for Real CLI PTY Integration Harness (PRD §12.6)."""

import os
import unittest
from macao.adapter.integ_harness import verify_single_cli_pty, verify_all_configured_clis


class TestRealCLIIntegHarness(unittest.TestCase):

    def test_verify_single_cli_pty_claude(self):
        """Verify Claude Code PTY lifecycle in sandbox."""
        res = verify_single_cli_pty("claude")
        self.assertIn(res["status"], ("PASS", "SKIPPED"))
        if res["status"] == "PASS":
            self.assertTrue(res.get("pty_spawn", False))
            self.assertTrue(res.get("clean_kill", False))

    def test_verify_single_cli_pty_codex(self):
        """Verify Codex PTY lifecycle in sandbox."""
        res = verify_single_cli_pty("codex")
        self.assertIn(res["status"], ("PASS", "SKIPPED"))
        if res["status"] == "PASS":
            self.assertTrue(res.get("pty_spawn", False))
            self.assertTrue(res.get("clean_kill", False))

    def test_verify_single_cli_pty_opencode(self):
        """Verify OpenCode PTY lifecycle in sandbox."""
        res = verify_single_cli_pty("opencode")
        self.assertIn(res["status"], ("PASS", "SKIPPED"))
        if res["status"] == "PASS":
            self.assertTrue(res.get("pty_spawn", False))
            self.assertTrue(res.get("clean_kill", False))

    def test_verify_single_cli_pty_agy(self):
        """Verify Google Antigravity (agy) PTY lifecycle in sandbox."""
        res = verify_single_cli_pty("agy")
        self.assertIn(res["status"], ("PASS", "SKIPPED"))
        if res["status"] == "PASS":
            self.assertTrue(res.get("pty_spawn", False))
            self.assertTrue(res.get("clean_kill", False))

    def test_verify_all_clis(self):
        """Verify batch real CLI verification runs and returns 4 results."""
        results = verify_all_configured_clis()
        self.assertEqual(len(results), 4)
        for r in results:
            self.assertIn(r["status"], ("PASS", "SKIPPED"))


if __name__ == "__main__":
    unittest.main()
