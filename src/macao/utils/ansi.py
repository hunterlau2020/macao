"""ANSI Escape Code Stripping Utility (PRD §12.6)."""

import re

# Comprehensive ANSI escape sequence pattern
ANSI_ESCAPE_RE = re.compile(
    r"""
    \x1B  # ESC
    (?:   # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |     # or [ for CSI, followed by a sequence of bytes
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    |     # OSC (Operating System Command) sequences
        \]
        [^\x07\x1B]*
        (?: \x07 | \x1B\\ )
    )
    """,
    re.VERBOSE,
)


def strip_ansi(text: str) -> str:
    """Removes all ANSI escape sequences, colors, and cursor controls from text."""
    if not text:
        return ""
    return ANSI_ESCAPE_RE.sub("", text)
