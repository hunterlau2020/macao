"""MACAO Agent Adapters Package."""

from macao.adapter.base import AgentAdapter, CapabilityManifest
from macao.adapter.pty_session import PTYSession
from macao.adapter.claude import ClaudeCodeAdapter
from macao.adapter.codex import CodexAdapter
from macao.adapter.opencode import OpenCodeAdapter
from macao.adapter.antigravity import AntigravityAdapter
from macao.adapter.kimi import KimiAdapter
from macao.adapter.cursor import CursorAgentAdapter
from macao.adapter.session_locator import SessionLocator

__all__ = [
    "AgentAdapter",
    "CapabilityManifest",
    "PTYSession",
    "ClaudeCodeAdapter",
    "CodexAdapter",
    "OpenCodeAdapter",
    "AntigravityAdapter",
    "CursorAgentAdapter",
    "KimiAdapter",
    "MockAgentAdapter",
    "SessionLocator",
]
