#!/usr/bin/env python3
"""Reproduce executor dispatch and acceptance-criteria gaps without external CLI.

Issues: P1-e06d44c-02 (CLI composition root has no executor adapter) and
P2-e06d44c-01 (five executor adapters drop ``acceptance_criteria`` if wired).
Target commit: e06d44cb31a0dbcbe199e6bb124430e9701e087f.  Prerequisites:
Python 3.10+ and MACAO dependencies; run with PYTHONPATH=src.  No network or
vendor CLI is used.  Last executed: 2026-09-09 Asia/Taipei.
"""

import shutil
import tempfile
from pathlib import Path

from macao.adapter.antigravity import AntigravityAdapter
from macao.adapter.claude import ClaudeCodeAdapter
from macao.adapter.codex import CodexAdapter
from macao.adapter.kimi import KimiAdapter
from macao.adapter.opencode import OpenCodeAdapter
from macao.cli.main import DEFAULT_CONFIG_TEMPLATE, get_orchestrator
from macao.storage.db import reset_db_manager


class CaptureSession:
    """Minimal PTY substitute: records the prompt sent by an adapter."""

    def __init__(self):
        self.prompts = []

    def write_input(self, prompt):
        self.prompts.append(prompt)
        return True


def main():
    root = Path(tempfile.mkdtemp(prefix="macao-e06d44c-composition-"))
    try:
        (root / "macao.yaml").write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
        reset_db_manager()
        production_orchestrator = get_orchestrator(str(root))
        assert production_orchestrator.executor is None
    finally:
        reset_db_manager()
        shutil.rmtree(root, ignore_errors=True)

    criterion = "MUST_REACH_EXECUTOR"
    payload = {
        "task_description": "Implement the requested change.",
        "acceptance_criteria": [criterion],
    }
    adapters = [
        ("claude", ClaudeCodeAdapter("claude", {"role": "executor"})),
        ("codex", CodexAdapter("codex", {"role": "executor"})),
        ("opencode", OpenCodeAdapter("opencode", {"role": "executor"})),
        ("antigravity", AntigravityAdapter("agy", {"role": "executor"})),
        ("kimi", KimiAdapter("kimi", {"role": "executor"})),
    ]

    lost = []
    for name, adapter in adapters:
        session = CaptureSession()
        adapter.session = session
        adapter.is_running = True
        assert adapter.inject_task(payload), f"{name} did not accept production payload"
        prompt = session.prompts[-1]
        if criterion not in prompt:
            lost.append(name)

    expected = {"claude", "codex", "opencode", "antigravity", "kimi"}
    assert set(lost) == expected, f"unexpected criterion delivery result: {lost}"
    print("REPRODUCED: CLI composition root has no executor; acceptance_criteria lost by " + ", ".join(lost))


if __name__ == "__main__":
    main()
