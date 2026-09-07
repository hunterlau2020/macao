"""MACAO Sensitive Credential & Secrets Redaction Utility (PRD §14 / Security)."""

import re
from typing import Optional, List, Tuple

# Structured rules: (compiled_regex, replacement_template)
SECRET_RULE_SPECS: List[Tuple[re.Pattern, str]] = [
    # 1. OpenAI / Anthropic / general API keys (e.g. sk-..., ant-..., sk-ant-...)
    (re.compile(r"\b(sk-[a-zA-Z0-9_-]{16,}|ant-[a-zA-Z0-9_-]{16,}|sk-ant-[a-zA-Z0-9_-]{16,})\b", re.IGNORECASE), "******"),
    # 2. GitHub personal access tokens
    (re.compile(r"\b(ghp_[a-zA-Z0-9]{20,}|gho_[a-zA-Z0-9]{20,}|github_pat_[a-zA-Z0-9_]{30,})\b"), "******"),
    # 3. AWS Access Key IDs (AKIA...)
    (re.compile(r"\b(AKIA[0-9A-Z]{16})\b"), "******"),
    # 4. Google API Keys (AIza...)
    (re.compile(r"\b(AIza[0-9A-Za-z\-_]{35})\b"), "******"),
    # 5. JWT tokens (eyJ...)
    (re.compile(r"\b(eyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,})\b"), "******"),
    # 6. Slack tokens
    (re.compile(r"\b(xox[baprs]-[a-zA-Z0-9-]{20,})\b"), "******"),
    # 7. Generic high entropy hex tokens with dots (e.g. 7372de6c...KVqd4ZEnkNIhN5N6)
    (re.compile(r"\b([0-9a-fA-F]{24,}\.[a-zA-Z0-9_-]{10,})\b"), "******"),
    # 8. Bearer authorization tokens
    (re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{15,}", re.IGNORECASE), r"\g<1>******"),
    # 9. Passwords in URLs: e.g. postgres://user:password@host:port/db
    (re.compile(r"(://[^:\s]+:)([^@\s/]+)(@)"), r"\g<1>******\g<3>"),
    # 10. Passwords/Tokens in key-value format (e.g. password=xyz, api_key: "xyz", token="xyz", secret="xyz")
    (re.compile(r"((?:password|api_key|token|secret|access_token|auth_token)\s*[:=]\s*['\"]?)([^'\"\s,;&]+)(['\"]?)", re.IGNORECASE), r"\g<1>******\g<3>"),
    # 11. Environment variable tokens (e.g. AWS_SECRET_ACCESS_KEY=xyz, GITHUB_TOKEN=xyz, *_TOKEN=xyz)
    (re.compile(r"([A-Z0-9_]*(?:TOKEN|SECRET|KEY|PASSWORD|AUTH)\s*=\s*['\"]?)([^'\"\s,;&]+)(['\"]?)", re.IGNORECASE), r"\g<1>******\g<3>"),
    # 12. Private Key PEM blocks
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z ]*PRIVATE KEY-----"), "******"),
]

# For backwards compatibility
SECRET_PATTERNS = [rule[0] for rule in SECRET_RULE_SPECS]


def mask_secrets(text: Optional[str], mask_replacement: str = "******") -> str:
    """
    Deterministically redacts sensitive tokens, credentials, and API keys
    from transcripts, log messages, and error traces before persistence.
    """
    if not text:
        return ""

    redacted = text
    for pat, rep in SECRET_RULE_SPECS:
        if rep == "******" and mask_replacement != "******":
            rep_target = mask_replacement
        elif "******" in rep:
            rep_target = rep.replace("******", mask_replacement)
        else:
            rep_target = rep
        redacted = pat.sub(rep_target, redacted)

    return redacted
