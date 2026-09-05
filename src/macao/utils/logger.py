"""MACAO Centralized Logging Subsystem.

Provides structured file logging to .macao/logs/macao.log with rotation,
plus console logging configurable via MACAO_LOG_LEVEL (default INFO).
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict

_LOGGERS: Dict[str, logging.Logger] = {}


def setup_logger(name: str = "macao", project_root: str = ".", level: Optional[str] = None) -> logging.Logger:
    """Configures and returns a logger instance with rotating file and optional console handlers."""
    cache_key = f"{name}:{project_root}"
    if cache_key in _LOGGERS:
        return _LOGGERS[cache_key]

    env_level = os.environ.get("MACAO_LOG_LEVEL", "INFO").upper()
    resolved_level = getattr(logging, (level or env_level).upper(), logging.INFO)

    logger = logging.getLogger(f"{name}_{abs(hash(project_root)) % 100000}")
    logger.setLevel(resolved_level)
    logger.propagate = False

    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        fmt = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 1. File Handler: .macao/logs/macao.log
        try:
            log_dir = Path(project_root) / ".macao" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "macao.log"
            file_handler = RotatingFileHandler(
                str(log_file),
                maxBytes=10 * 1024 * 1024,  # 10 MB per log file
                backupCount=5,
                encoding="utf-8"
            )
            file_handler.setLevel(resolved_level)
            file_handler.setFormatter(fmt)
            logger.addHandler(file_handler)
        except Exception:
            pass

        # 2. Console stream handler if explicitly requested
        if os.environ.get("MACAO_LOG_CONSOLE") == "1" or os.environ.get("MACAO_DEBUG") == "1":
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(resolved_level)
            console_handler.setFormatter(fmt)
            logger.addHandler(console_handler)

    _LOGGERS[cache_key] = logger
    return logger


def get_logger(name: str = "macao", project_root: str = ".") -> logging.Logger:
    """Returns a logger instance for the specified component and project root."""
    return setup_logger(name, project_root=project_root)
