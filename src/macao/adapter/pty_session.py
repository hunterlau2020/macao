"""PTY Session Management, Process Group Signals, and Output Capture (PRD §12.6)."""

import os
import pty
import select
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import List, Optional, Tuple

from macao.utils.ansi import strip_ansi


class PTYSession:
    """Manages a spawned CLI process inside a pseudo-terminal (PTY)."""

    def __init__(self, cmd: List[str], cwd: str = ".", env: Optional[dict] = None):
        self.cmd = cmd
        self.cwd = str(Path(cwd).resolve())
        self.env = env or os.environ.copy()
        self.process: Optional[subprocess.Popen] = None
        self.master_fd: Optional[int] = None
        self.logs: List[str] = []
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> bool:
        """Starts process in a new session with PTY and sets process group."""
        try:
            master, slave = pty.openpty()
            self.master_fd = master

            self.process = subprocess.Popen(
                self.cmd,
                stdin=slave,
                stdout=slave,
                stderr=slave,
                cwd=self.cwd,
                env=self.env,
                preexec_fn=os.setsid,  # Create new process group
                close_fds=True,
            )
            os.close(slave)

            self._stop_event.clear()
            self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self._reader_thread.start()
            return True
        except Exception as e:
            self.logs.append(f"[PTY Error] Failed to start {self.cmd}: {e}")
            return False

    def _read_output(self) -> None:
        """Background thread reading master PTY fd."""
        while not self._stop_event.is_set() and self.master_fd is not None:
            try:
                r, _, _ = select.select([self.master_fd], [], [], 0.2)
                if r:
                    data = os.read(self.master_fd, 4096)
                    if not data:
                        break
                    text = data.decode("utf-8", errors="replace")
                    cleaned = strip_ansi(text)
                    self.logs.append(cleaned)
            except (OSError, ValueError):
                break

    def write_input(self, text: str) -> bool:
        """Sends input string to CLI stdin."""
        if self.master_fd is not None:
            try:
                if not text.endswith("\n"):
                    text += "\n"
                os.write(self.master_fd, text.encode("utf-8"))
                return True
            except OSError:
                return False
        return False

    def get_clean_logs(self, tail_lines: int = 300) -> str:
        """Returns the tail lines of clean text logs."""
        full_text = "".join(self.logs)
        lines = full_text.splitlines()
        return "\n".join(lines[-tail_lines:])

    def terminate(self, grace_period_sec: float = 2.0) -> bool:
        """Gracefully terminates process group (SIGTERM -> SIGKILL)."""
        self._stop_event.set()
        if self.process is not None and self.process.poll() is None:
            try:
                pgid = os.getpgid(self.process.pid)
                os.killpg(pgid, signal.SIGTERM)
                
                # Wait grace period
                start_t = time.time()
                while time.time() - start_t < grace_period_sec:
                    if self.process.poll() is not None:
                        break
                    time.sleep(0.1)

                if self.process.poll() is None:
                    os.killpg(pgid, signal.SIGKILL)
            except Exception:
                pass

        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None

        return True
