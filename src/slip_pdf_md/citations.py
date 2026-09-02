"""Conservative OCR citation repairs. Never rewrite prose with an LLM."""

from __future__ import annotations

import re

# ATR -> AIR but ATTRIBUTE must remain ATTRIBUTE. Word-boundary handles that
# because ATTRIBUTE does not contain a standalone ATR token.
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bATR\b"), "AIR"),
    (re.compile(r"L\]"), "LJ"),
    (re.compile(r"AIL\)"), "All."),
    (re.compile(r"Caleutta"), "Calcutta"),
    (re.compile(r"Jnarkhand"), "Jharkhand"),
    (re.compile(r"I71-B"), "171-B"),
]


def repair_citations(text: str) -> str:
    repaired = text
    for pattern, replacement in _PATTERNS:
        repaired = pattern.sub(replacement, repaired)
    return repaired
