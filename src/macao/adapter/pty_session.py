"""PTY Session Management, Process Group Signals, and Output Capture (PRD §12.6)."""

import os
import sys
import select
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import List, Optional, Tuple

from macao.utils.ansi import strip_ansi

try:
    import pty
except ImportError:
    pty = None


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
        if pty is None:
            raise RuntimeError("PTY is not supported on this platform (requires POSIX / pty module).")

        try:
            master, slave = pty.openpty()
            self.master_fd = master

            preexec = os.setsid if hasattr(os, "setsid") else None

            self.process = subprocess.Popen(
                self.cmd,
                stdin=slave,
                stdout=slave,
                stderr=slave,
                cwd=self.cwd,
                env=self.env,
                preexec_fn=preexec,  # Create new process group
                close_fds=True,
            )
            os.close(slave)

            self._stop_event.clear()
            self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._reader_thread.start()
            return True
        except Exception as e:
            self.logs.append(f"[PTY Error] Failed to spawn process: {e}")
            if self.master_fd is not None:
                try:
                    os.close(self.master_fd)
                except OSError:
                    pass
                self.master_fd = None
            return False

    def _read_loop(self) -> None:
        """Reads raw bytes from PTY master and strips ANSI codes."""
        if self.master_fd is None:
            return

        buffer = ""
        while not self._stop_event.is_set():
            try:
                r, _, _ = select.select([self.master_fd], [], [], 0.1)
                if self.master_fd in r:
                    data = os.read(self.master_fd, 4096)
                    if not data:
                        break
                    text = data.decode("utf-8", errors="replace")
                    buffer += text
                    lines = buffer.split("\n")
                    buffer = lines[-1]
                    for line in lines[:-1]:
                        clean_line = strip_ansi(line.strip("\r"))
                        if clean_line:
                            self.logs.append(clean_line)
            except (OSError, ValueError):
                break

        if buffer:
            clean_line = strip_ansi(buffer.strip("\r"))
            if clean_line:
                self.logs.append(clean_line)

    def send_input(self, text: str) -> bool:
        """Injects text input into PTY slave stdin."""
        if self.master_fd is None or self.process is None:
            return False
        try:
            payload = (text + "\n").encode("utf-8")
            os.write(self.master_fd, payload)
            return True
        except OSError:
            return False

    def write_input(self, text: str) -> bool:
        """Alias for send_input."""
        return self.send_input(text)

    def get_clean_logs(self, tail_lines: Optional[int] = None) -> List[str]:
        """Returns captured output logs, optionally tailed."""
        if tail_lines is not None and tail_lines > 0:
            return list(self.logs)[-tail_lines:]
        return list(self.logs)

    def terminate(self, timeout_sec: float = 3.0) -> None:
        """Terminates process group cleanly using SIGTERM then SIGKILL (PRD §12.6)."""
        self._stop_event.set()
        if self.process is None:
            return

        pid = self.process.pid
        pgid = None
        if hasattr(os, "getpgid"):
            try:
                pgid = os.getpgid(pid)
            except OSError:
                pass

        # Try SIGTERM to process group
        try:
            if pgid and hasattr(os, "killpg") and hasattr(signal, "SIGTERM"):
                os.killpg(pgid, signal.SIGTERM)
            else:
                self.process.terminate()
        except OSError:
            pass

        # Wait for exit
        start_t = time.time()
        while time.time() - start_t < timeout_sec:
            if self.process.poll() is not None:
                break
            time.sleep(0.1)

        # Force SIGKILL to process group if still alive
        if self.process.poll() is None:
            try:
                if pgid and hasattr(os, "killpg") and hasattr(signal, "SIGKILL"):
                    os.killpg(pgid, signal.SIGKILL)
                else:
                    self.process.kill()
            except OSError:
                pass

        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None
