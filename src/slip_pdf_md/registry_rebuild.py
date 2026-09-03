"""Rebuild registry.sqlite from Markdown front matter when the database is gone."""

from __future__ import annotations

import re
from pathlib import Path

from slip_pdf_md.paths import CLEAN, DUPLICATES, NEEDS_REVIEW, SlipPaths
from slip_pdf_md.registry import STATUS_DONE, STATUS_NEEDS_REVIEW, Registry, sha256_file

FRONT_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def _front_matter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    meta = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta


def rebuild_from_vault(paths: SlipPaths, *, dest: Path | None = None) -> dict:
    dest = Path(dest) if dest is not None else paths.registry_path
    if dest.exists():
        dest.replace(dest.with_name(dest.name + ".before-rebuild"))
    registry = Registry(dest, restore_if_missing=False)
    added = 0
    skipped = 0
    for folder, status, routed in (
        (paths.clean, STATUS_DONE, CLEAN),
        (paths.needs_review, STATUS_NEEDS_REVIEW, NEEDS_REVIEW),
    ):
        if not folder.is_dir():
            continue
        for md in folder.glob("*.md"):
            if md.name.endswith(".sidecar.md"):
                continue
            meta = _front_matter(md.read_text(encoding="utf-8", errors="replace"))
            sha = (meta.get("source_sha256") or "").strip()
            if len(sha) < 32:
                skipped += 1
                continue
            name = meta.get("source_file") or md.stem + ".pdf"
            fake = Path(name)
            row = registry.see(fake, routed_to=routed, sha256=sha)
            if row["status"] == "NEW":
                added += 1
            pages = meta.get("page_count")
            try:
                page_count = int(pages) if pages not in (None, "") else None
            except ValueError:
                page_count = None
            registry.set_status(
                sha,
                status,
                engine=meta.get("engine"),
                page_count=page_count,
                output_path=str(md),
            )
    sidecar_hits = 0
    if paths.duplicates.is_dir():
        for sidecar in paths.duplicates.glob("*.sidecar.md"):
            text = sidecar.read_text(encoding="utf-8", errors="replace")
            sha = ""
            inbound = sidecar.name.replace(".pdf.sidecar.md", ".pdf")
            for line in text.splitlines():
                if line.strip().startswith("- sha256:"):
                    sha = line.split(":", 1)[1].strip().strip("`")
                if line.strip().startswith("- duplicate_filename:"):
                    inbound = line.split(":", 1)[1].strip().strip("`")
            if len(sha) >= 32:
                registry.see(Path(inbound), routed_to=DUPLICATES, sha256=sha)
                sidecar_hits += 1
    hashed_pdfs = 0
    for folder, routed in (
        (paths.processed, "60_90_PROCESSED"),
        (paths.duplicates, DUPLICATES),
        (paths.raw, "0_01_RAW_PDF"),
    ):
        if not folder.is_dir():
            continue
        for pdf in folder.rglob("*.pdf"):
            sha = sha256_file(pdf)
            registry.see(pdf, routed_to=routed, sha256=sha)
            hashed_pdfs += 1
    health = registry.health()
    registry.close()
    return {
        "registry": str(dest),
        "documents_added": added,
        "markdown_skipped": skipped,
        "sidecar_sightings": sidecar_hits,
        "pdfs_hashed": hashed_pdfs,
        "documents": health["documents"],
        "sightings": health["sightings"],
        "gubernatio": health.get("gubernatio", 0),
    }
