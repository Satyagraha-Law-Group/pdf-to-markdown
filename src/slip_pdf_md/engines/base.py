"""Engine adapter interface. IBM Docling (and others) plug in here later."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class ConversionResult:
    pages: list[str]
    page_count: int
    engine: str
    warnings: list[str] = field(default_factory=list)
    unrecovered_tables: int = 0
    needs_review: bool = False


class EngineAdapter(Protocol):
    name: str

    def convert(self, pdf_path: Path) -> ConversionResult:
        ...
