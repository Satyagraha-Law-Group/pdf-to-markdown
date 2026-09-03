"""SLIP folder contract. Do not rename pipeline directories."""

from __future__ import annotations

import os
from pathlib import Path

from slip_pdf_md.naming import resolve_generated_path

SLIP_DIR_NAMES = (
    "0_01_RAW_PDF",
    "10_02_READY_FOR_DOCLING",
    "20_03_CLEAN_MARKDOWN",
    "30_04_CASE_BRIEFS",
    "40_05_PROJECT_BRIEFS",
    "50_90_DUPLICATES",
    "60_90_PROCESSED",
    "70_99_NEEDS_REVIEW",
    "90_00_PROJECT_TOOLING",
    "Convert-PDF-TO-MARKDOWN-01",
)

RAW = SLIP_DIR_NAMES[0]
READY = SLIP_DIR_NAMES[1]
CLEAN = SLIP_DIR_NAMES[2]
CASE_BRIEFS = SLIP_DIR_NAMES[3]
PROJECT_BRIEFS = SLIP_DIR_NAMES[4]
DUPLICATES = SLIP_DIR_NAMES[5]
PROCESSED = SLIP_DIR_NAMES[6]
NEEDS_REVIEW = SLIP_DIR_NAMES[7]
TOOLING = SLIP_DIR_NAMES[8]
TOOL_DIR = SLIP_DIR_NAMES[9]


class SlipPaths:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    @property
    def raw(self) -> Path:
        return self.root / RAW

    @property
    def ready(self) -> Path:
        return self.root / READY

    @property
    def clean(self) -> Path:
        return self.root / CLEAN

    @property
    def case_briefs(self) -> Path:
        return self.root / CASE_BRIEFS

    @property
    def project_briefs(self) -> Path:
        return self.root / PROJECT_BRIEFS

    @property
    def duplicates(self) -> Path:
        return self.root / DUPLICATES

    @property
    def processed(self) -> Path:
        return self.root / PROCESSED

    @property
    def needs_review(self) -> Path:
        return self.root / NEEDS_REVIEW

    @property
    def tooling(self) -> Path:
        return self.root / TOOLING

    @property
    def tool(self) -> Path:
        return self.root / TOOL_DIR

    @property
    def registry_dir(self) -> Path:
        return self.tooling / "pdf-to-markdown"

    @property
    def registry_path(self) -> Path:
        """Living SHA-256 registry. Three-word name, stamp is first-created time."""
        folder = self.registry_dir
        folder.mkdir(parents=True, exist_ok=True)
        live = resolve_generated_path(
            folder,
            "Document",
            "Hash",
            "Registry",
            "sqlite",
            legacy_names=("registry.sqlite",),
        )
        old_bak = folder / "registry.sqlite.bak"
        new_bak = live.with_suffix(".bak")
        if old_bak.is_file() and not new_bak.exists():
            old_bak.rename(new_bak)
        return live


    def date_bucket(self, moment=None) -> str:
        """Calcutta calendar day, sortable (2026-09-03)."""
        from slip_pdf_md.naming import now_calcutta
        moment = moment or now_calcutta()
        return moment.strftime("%Y-%m-%d")

    def bucket(self, folder, moment=None) -> Path:
        dest = Path(folder) / self.date_bucket(moment)
        dest.mkdir(parents=True, exist_ok=True)
        return dest

    def all_dirs(self) -> list[Path]:
        return [
            self.raw,
            self.ready,
            self.clean,
            self.case_briefs,
            self.project_briefs,
            self.duplicates,
            self.processed,
            self.needs_review,
            self.tooling,
            self.tool,
            self.registry_dir,
        ]


def looks_like_slip_root(path: Path) -> bool:
    path = Path(path)
    return (path / RAW).is_dir() or path.name == "SLIP_DOCUMENT_PROCESSING"


def discover_slip_root(explicit: str | Path | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("SLIP_VAULT")
    if env:
        return Path(env).expanduser().resolve()
    here = Path.cwd().resolve()
    for candidate in [here, *here.parents]:
        if looks_like_slip_root(candidate):
            return candidate
        nested = candidate / "SLIP_DOCUMENT_PROCESSING"
        if looks_like_slip_root(nested):
            return nested
    return here
