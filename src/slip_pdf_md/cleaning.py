"""Mechanical Layer-1 cleaning: leaders, running headers, OCR noise."""

from __future__ import annotations

import re
from collections import Counter

LEADER_RE = re.compile(r"(?:[ \t]*[.\u2022\u2026]){3,}|[.]{3,}|[\u2026]{2,}|-{4,}")
RUNNING_SKIP_RE = re.compile(r"^## Page\s+\d+", re.I)


def normalize_text(value: str) -> str:
    cleaned = value.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = cleaned.replace("\x00", "")
    cleaned = cleaned.replace(" .", ".").replace(" ,", ",").replace(" ;", ";")
    lines = []
    for line in cleaned.split("\n"):
        stripped = " ".join(line.strip().split())
        if stripped and not re.fullmatch(r"[-_=]{3,}", stripped):
            lines.append(stripped)
    return "\n".join(lines)


def collapse_leaders(text: str) -> str:
    return LEADER_RE.sub("  ", text)


def is_likely_ocr_noise(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if re.fullmatch(r"[-_=#*@/\\|~`.,;:()'\"\[\]{}]+", stripped):
        return True
    letters = sum(ch.isalpha() for ch in stripped)
    symbols = sum(not (ch.isalnum() or ch.isspace()) for ch in stripped)
    if letters < 2 and symbols > 0:
        return True
    if symbols and len(stripped) > 8:
        ratio = symbols / len(stripped)
        if ratio > 0.45:
            return True
    return False


def clean_ocr_text(value: str) -> str:
    cleaned = normalize_text(value)
    cleaned = re.sub(r"(?<=\w)-\s+(?=\w)", "", cleaned)
    cleaned = re.sub(r" {2,}", " ", cleaned)
    filtered = []
    for line in cleaned.splitlines():
        if not is_likely_ocr_noise(line):
            filtered.append(line.strip())
    cleaned = "\n".join(filtered)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return collapse_leaders(cleaned).strip()


def _candidate_header(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or RUNNING_SKIP_RE.match(stripped):
        return None
    if stripped.startswith("<!--") or stripped.startswith("|"):
        return None
    if stripped.startswith(">"):
        return None
    if len(stripped) > 80:
        return None
    return stripped


def demote_running_headers(pages: list[str], min_pages: int = 3) -> list[str]:
    """Wrap lines that repeat at the start or end of many pages in HTML comments."""
    if len(pages) < min_pages:
        return pages
    top_counter: Counter[str] = Counter()
    bottom_counter: Counter[str] = Counter()
    tops: list[str | None] = []
    bottoms: list[str | None] = []
    for page in pages:
        lines = [ln for ln in page.splitlines() if ln.strip()]
        top = _candidate_header(lines[0]) if lines else None
        bottom = _candidate_header(lines[-1]) if len(lines) > 1 else None
        tops.append(top)
        bottoms.append(bottom)
        if top:
            top_counter[top] += 1
        if bottom:
            bottom_counter[bottom] += 1

    top_hits = {text for text, n in top_counter.items() if n >= min_pages}
    bottom_hits = {text for text, n in bottom_counter.items() if n >= min_pages}
    if not top_hits and not bottom_hits:
        return pages

    rewritten = []
    for page, top, bottom in zip(pages, tops, bottoms):
        lines = page.splitlines()
        out: list[str] = []
        consumed_top = False
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if not consumed_top and top and stripped == top and top in top_hits:
                out.append(f"<!-- running header: {stripped} -->")
                consumed_top = True
                continue
            if idx == len(lines) - 1 and bottom and stripped == bottom and bottom in bottom_hits:
                out.append(f"<!-- running footer: {stripped} -->")
                continue
            out.append(line)
        rewritten.append("\n".join(out))
    return rewritten
