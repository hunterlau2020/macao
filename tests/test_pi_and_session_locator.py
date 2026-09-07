"""Unit tests for Pi Coding Agent Adapter and multi-session locator (PRD §12, §14)."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from macao.adapter.pi import PiAdapter
from macao.adapter.session_locator import SessionLocator, _sanitize_session_name
from macao.core.types import ExecutionMode


class TestPiAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = PiAdapter("test-pi", {"mode": "sandbox", "workspace_path": "/tmp"})

    def test_capabilities(self):
        caps = self.adapter.capabilities()
        self.assertTrue(caps.can_execute)
        self.assertTrue(caps.can_review)
        self.assertEqual(caps.execution_mode, ExecutionMode.SANDBOXED)

    def test_resolve_binary(self):
        with patch("shutil.which", return_value="/custom/bin/pi"):
            self.assertEqual(self.adapter._resolve_binary(), "/custom/bin/pi")

    def test_preflight_not_found(self):
        with patch.object(self.adapter, "_resolve_binary", return_value=None):
            res = self.adapter.preflight()
            self.assertFalse(res.installed)
            self.assertIn("not found", res.details)

    def test_preflight_success(self):
        mock_proc = MagicMock()
        mock_proc.stdout = "0.85.1\n"
        with patch.object(self.adapter, "_resolve_binary", return_value="/bin/pi"), \
             patch("subprocess.run", return_value=mock_proc):
            res = self.adapter.preflight()
            self.assertTrue(res.installed)
            self.assertEqual(res.version, "0.85.1")

    def test_inject_task_reviewer_format(self):
        self.adapter.is_running = True
        self.adapter.session = MagicMock()
        payload = {
            "checkpoint_ref": "c1234",
            "review_round": 2,
            "diff": "--- a/file.py\n+++ b/file.py"
        }
        self.adapter.inject_task(payload)
        self.adapter.session.write_input.assert_called_once()
        prompt = self.adapter.session.write_input.call_args[0][0]
        self.assertIn("REVIEW_REQUEST:", prompt)
        self.assertIn("c1234", prompt)
        self.assertIn("review round: 2", prompt)
        self.assertIn(".review.yml", prompt)


class TestSessionLocator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "demo-repo"
        self.project_path.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sanitize_session_name(self):
        self.assertEqual(_sanitize_session_name(None, "abc12345"), "abc12345")
        self.assertEqual(_sanitize_session_name("", "xyz98765"), "xyz98765")
        self.assertEqual(_sanitize_session_name("  simple test  "), "simple test")
        
        # Test masking API keys
        sensitive = "Bearer sk-1234567890abcdef1234567890"
        masked = _sanitize_session_name(sensitive)
        self.assertNotIn("sk-1234567890abcdef", masked)
        self.assertIn("******", masked)

    def test_pi_session_discovery_and_names(self):
        fake_pi_base = Path(self.temp_dir) / ".pi" / "agent" / "sessions"
        sanitized_dir = "--" + str(self.project_path).strip("/").replace("/", "-") + "--"
        session_folder = fake_pi_base / sanitized_dir
        session_folder.mkdir(parents=True)

        # Session 1: with session_info name
        s1_file = session_folder / "2026-09-07T10-00-00_sid1.jsonl"
        with open(s1_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "session", "id": "sid1", "cwd": str(self.project_path)}) + "\n")
            f.write(json.dumps({"type": "session_info", "name": "qwen-review-eng"}) + "\n")

        # Session 2: fallback to first user prompt
        s2_file = session_folder / "2026-09-07T09-00-00_sid2.jsonl"
        with open(s2_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "session", "id": "sid2", "cwd": str(self.project_path)}) + "\n")
            f.write(json.dumps({
                "type": "message",
                "message": {"role": "user", "content": [{"type": "text", "text": "Implement feature X"}]}
            }) + "\n")

        # Mock Path.home() to point to our temp_dir
        with patch("pathlib.Path.home", return_value=Path(self.temp_dir)):
            sessions = SessionLocator.list_sessions("pi", self.project_path)
            self.assertEqual(len(sessions), 2)
            self.assertEqual(sessions[0]["session_name"], "qwen-review-eng")
            self.assertEqual(sessions[1]["session_name"], "Implement feature X")

            # Test find_session with default (most recent)
            latest = SessionLocator.find_session("pi", self.project_path)
            self.assertIsNotNone(latest)
            self.assertEqual(latest["session_id"], "sid1")
            self.assertEqual(latest["total_sessions"], 2)

            # Test find_session with specific ref
            matched = SessionLocator.find_session("pi", self.project_path, session_ref="sid2")
            self.assertIsNotNone(matched)
            self.assertEqual(matched["session_id"], "sid2")
            self.assertEqual(matched["session_name"], "Implement feature X")


if __name__ == "__main__":
    unittest.main()
