"""Sample-page OCR recall against finished Markdown."""

from __future__ import annotations

import re
from pathlib import Path

import fitz

from slip_pdf_md.engines.pymupdf_engine import ocr_page_text

TOKEN_RE = re.compile(r"[A-Za-z0-9]{2,}")
DEFAULT_THRESHOLD = 0.90


def alnum_tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in TOKEN_RE.finditer(text or "")}


def token_recall(reference: str, candidate: str) -> float:
    ref = alnum_tokens(reference)
    if not ref:
        return 1.0
    hit = len(ref & alnum_tokens(candidate))
    return hit / len(ref)


def score_markdown_against_pdf(
    pdf_path: Path,
    markdown: str,
    *,
    sample_pages: tuple[int, ...] | None = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> dict:
    pdf_path = Path(pdf_path)
    doc = fitz.open(pdf_path)
    try:
        n = doc.page_count
        if sample_pages is None:
            if n <= 2:
                indices = tuple(range(n))
            else:
                indices = (0, n // 2, n - 1)
        else:
            indices = tuple(i for i in sample_pages if 0 <= i < n)
        page_scores = []
        ocr_bits = []
        for i in indices:
            ocr = ocr_page_text(doc[i])
            ocr_bits.append(ocr)
            page_scores.append(
                {
                    "page": i + 1,
                    "ocr_tokens": len(alnum_tokens(ocr)),
                    "recall": round(token_recall(ocr, markdown), 4),
                }
            )
    finally:
        doc.close()
    combined = "\n".join(ocr_bits)
    overall = token_recall(combined, markdown)
    return {
        "overall_recall": round(overall, 4),
        "threshold": threshold,
        "passed": overall >= threshold,
        "page_scores": page_scores,
    }
