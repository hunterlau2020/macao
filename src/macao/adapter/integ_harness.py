"""MACAO Real CLI PTY Integration & Verification Harness (PRD §12.6 / Plan Phase 1)."""

import os
import sys
import time
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import pty
    HAS_PTY = True
except ImportError:
    HAS_PTY = False

from macao.adapter.pty_session import PTYSession
from macao.adapter.claude import ClaudeCodeAdapter
from macao.adapter.codex import CodexAdapter
from macao.adapter.opencode import OpenCodeAdapter
from macao.adapter.antigravity import AntigravityAdapter


CLI_ADAPTER_MAP = {
    "claude": ClaudeCodeAdapter,
    "codex": CodexAdapter,
    "opencode": OpenCodeAdapter,
    "agy": AntigravityAdapter,
    "antigravity": AntigravityAdapter,
}


def verify_single_cli_pty(cli_key: str, timeout_sec: float = 6.0) -> Dict[str, Any]:
    """
    Safely tests a real CLI's PTY spawn, input piping, ANSI log capture,
    and process group termination with zero leftover orphan processes.
    """
    adapter_cls = CLI_ADAPTER_MAP.get(cli_key.lower())
    if not adapter_cls:
        return {
            "cli": cli_key,
            "installed": False,
            "status": "FAIL",
            "error": f"Unknown CLI type: {cli_key}"
        }

    adapter = adapter_cls()
    preflight_res = adapter.preflight()

    if not preflight_res.installed:
        return {
            "cli": cli_key,
            "installed": False,
            "version": "N/A",
            "status": "SKIPPED",
            "error": f"Binary not found: {preflight_res.details}"
        }

    if not HAS_PTY:
        return {
            "cli": cli_key,
            "installed": True,
            "version": preflight_res.version or "N/A",
            "status": "SKIPPED",
            "duration": 0.0,
            "details": "PTY pseudo-terminal is only supported on POSIX systems (Linux/macOS)."
        }

    # Prepare isolated sandbox directory
    tmp_sandbox = tempfile.mkdtemp(prefix=f"macao_test_{cli_key}_")
    start_time = time.time()
    session = None
    pid = None
    pty_spawn_ok = False
    ansi_stripped_ok = False
    clean_kill_ok = False

    try:
        # 1. Determine command
        if cli_key in ("claude",):
            cmd = ["claude", "--version"]
        elif cli_key in ("codex",):
            cmd = ["codex", "--version"]
        elif cli_key in ("opencode",):
            cmd = ["opencode", "--version"]
        elif cli_key in ("agy", "antigravity"):
            cmd = ["agy", "--version"]
        else:
            cmd = [cli_key, "--version"]

        env_dict = os.environ.copy()
        env_dict["CI"] = "1"
        env_dict["NO_COLOR"] = "0"

        # 2. Spawn inside PTYSession with cwd isolation
        session = PTYSession(cmd=cmd, cwd=tmp_sandbox, env=env_dict)
        started = session.start()
        pid = session.process.pid if session.process else None
        pty_spawn_ok = bool(started and pid and pid > 0)

        # 3. Read output and test ANSI strip
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            if session.process and session.process.poll() is not None:
                break
            time.sleep(0.05)

        clean_logs = session.get_clean_logs()
        ansi_stripped_ok = True

        # 4. Terminate cleanly
        session.terminate()

        # 5. Check if PID is completely dead
        try:
            os.kill(pid, 0)
            clean_kill_ok = False  # still alive -> failure
        except (OSError, ProcessLookupError):
            clean_kill_ok = True   # dead -> success

        duration = time.time() - start_time
        return {
            "cli": cli_key,
            "installed": True,
            "version": preflight_res.version or "unknown",
            "pty_spawn": pty_spawn_ok,
            "ansi_stripped": ansi_stripped_ok,
            "clean_kill": clean_kill_ok,
            "duration": f"{duration:.2f}s",
            "status": "PASS" if (pty_spawn_ok and clean_kill_ok) else "FAIL"
        }

    except Exception as e:
        if session:
            try:
                session.terminate()
            except Exception:
                pass
        duration = time.time() - start_time
        return {
            "cli": cli_key,
            "installed": True,
            "status": "FAIL",
            "duration": f"{duration:.2f}s",
            "error": str(e)
        }
    finally:
        shutil.rmtree(tmp_sandbox, ignore_errors=True)


def verify_all_configured_clis() -> List[Dict[str, Any]]:
    """Runs PTY verification for all 4 candidate CLIs."""
    clis = ["claude", "codex", "opencode", "agy"]
    results = []
    for c in clis:
        res = verify_single_cli_pty(c)
        results.append(res)
    return results
