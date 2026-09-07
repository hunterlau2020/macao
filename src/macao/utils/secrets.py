"""MACAO Sensitive Credential & Secrets Redaction Utility (PRD §14 / Security)."""

import re
from typing import Optional

# Comprehensive patterns for common secrets and tokens
SECRET_PATTERNS = [
    # OpenAI / Anthropic / general API keys (e.g. sk-..., ant-..., key-...)
    re.compile(r"\b(sk-[a-zA-Z0-9_-]{16,}|ant-[a-zA-Z0-9_-]{16,})\b", re.IGNORECASE),
    # GitHub personal access tokens
    re.compile(r"\b(ghp_[a-zA-Z0-9]{20,}|gho_[a-zA-Z0-9]{20,}|github_pat_[a-zA-Z0-9_]{30,})\b"),
    # Slack tokens
    re.compile(r"\b(xox[baprs]-[a-zA-Z0-9-]{20,})\b"),
    # Generic high entropy hex tokens with dots (e.g. 7372de6c...KVqd4ZEnkNIhN5N6)
    re.compile(r"\b([0-9a-fA-F]{24,}\.[a-zA-Z0-9_-]{10,})\b"),
    # Bearer authorization tokens
    re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{15,}", re.IGNORECASE),
    # Passwords in URLs: e.g. postgres://user:password@host:port/db
    re.compile(r"(://[^:\s]+:)([^@\s/]+)(@)"),
    # Passwords in key-value format (e.g. password=xyz, password: "xyz")
    re.compile(r"(password\s*[:=]\s*['\"]?)([^'\"\s,;&]+)(['\"]?)", re.IGNORECASE),
    # Private Key PEM blocks
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z ]*PRIVATE KEY-----"),
]


def mask_secrets(text: Optional[str], mask_replacement: str = "******") -> str:
    """
    Deterministically redacts sensitive tokens, credentials, and API keys
    from transcripts, log messages, and error traces before persistence.
    """
    if not text:
        return ""

    redacted = text
    for pat in SECRET_PATTERNS:
        if pat.pattern.startswith("(Bearer"):
            redacted = pat.sub(r"\1" + mask_replacement, redacted)
        elif pat.pattern.startswith("(://"):
            redacted = pat.sub(r"\1" + mask_replacement + r"\3", redacted)
        elif pat.pattern.startswith("(password"):
            redacted = pat.sub(r"\1" + mask_replacement + r"\3", redacted)
        else:
            redacted = pat.sub(mask_replacement, redacted)

    return redacted
