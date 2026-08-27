"""MACAO Agent Adapters Package."""

from macao.adapter.base import AgentAdapter, CapabilityManifest
from macao.adapter.pty_session import PTYSession
from macao.adapter.claude import ClaudeCodeAdapter
from macao.adapter.codex import CodexAdapter
from macao.adapter.opencode import OpenCodeAdapter
from macao.adapter.antigravity import AntigravityAdapter
from macao.adapter.kimi import KimiAdapter
from macao.adapter.mock import MockAgentAdapter

__all__ = [
    "AgentAdapter",
    "CapabilityManifest",
    "PTYSession",
    "ClaudeCodeAdapter",
    "CodexAdapter",
    "OpenCodeAdapter",
    "AntigravityAdapter",
    "KimiAdapter",
    "MockAgentAdapter",
]
