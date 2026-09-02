from __future__ import annotations

from slip_pdf_md.engines.base import ConversionResult, EngineAdapter
from slip_pdf_md.engines.pymupdf_engine import PyMuPdfTesseractEngine

REGISTRY: dict[str, type] = {
    "pymupdf": PyMuPdfTesseractEngine,
    "pymupdf+tesseract": PyMuPdfTesseractEngine,
}


def get_engine(name: str = "pymupdf") -> EngineAdapter:
    key = (name or "pymupdf").strip().lower()
    try:
        cls = REGISTRY[key]
    except KeyError as exc:
        known = ", ".join(sorted(REGISTRY))
        raise ValueError(f"unknown engine {name!r}. known: {known}") from exc
    return cls()


__all__ = ["ConversionResult", "EngineAdapter", "get_engine", "REGISTRY"]
