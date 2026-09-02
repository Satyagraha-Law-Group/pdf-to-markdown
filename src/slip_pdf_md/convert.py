"""Level A orchestration: hash, route, convert, write Markdown, update registry."""

from __future__ import annotations

import shutil
from pathlib import Path

from slip_pdf_md.citations import repair_citations
from slip_pdf_md.cleaning import collapse_leaders, demote_running_headers
from slip_pdf_md.engines import get_engine
from slip_pdf_md.naming import iso_calcutta, now_calcutta
from slip_pdf_md.paths import DUPLICATES, READY, SlipPaths
from slip_pdf_md.runlog import append_record, build_record
from slip_pdf_md.registry import (
    STATUS_DONE,
    STATUS_NEEDS_REVIEW,
    STATUS_PROCESSING,
    Registry,
    sha256_file,
)

FRONT_MATTER_KEYS = (
    "document_type",
    "source_file",
    "source_sha256",
    "processing_status",
    "engine",
    "page_count",
    "converted_at",
)


def yaml_front_matter(meta: dict) -> str:
    lines = ["---"]
    for key in FRONT_MATTER_KEYS:
        value = meta[key]
        if isinstance(value, str) and (":" in value or value == "" or " " in value):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{key}: "{escaped}"')
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def render_markdown(
    *,
    source_file: str,
    sha256: str,
    status: str,
    engine: str,
    pages: list[str],
    repair: bool,
) -> str:
    bodies = [collapse_leaders(p or "") for p in pages]
    bodies = demote_running_headers(bodies)
    if repair:
        bodies = [repair_citations(b) for b in bodies]
    chunks = []
    for idx, body in enumerate(bodies, start=1):
        if body.strip():
            chunks.append(f"## Page {idx}\n\n{body.strip()}")
        else:
            chunks.append(f"## Page {idx}\n\n_No extractable text on this page._")
    if not chunks:
        chunks.append(
            "# Empty PDF\n\nNo extractable text or OCR text was found in this document."
        )
    meta = {
        "document_type": "legal_pdf",
        "source_file": source_file,
        "source_sha256": sha256,
        "processing_status": status,
        "engine": engine,
        "page_count": len(pages),
        "converted_at": iso_calcutta(),
    }
    return yaml_front_matter(meta) + "\n\n".join(chunks) + "\n"


def _unique_dest(folder: Path, name: str) -> Path:
    dest = folder / name
    if not dest.exists():
        return dest
    stem = Path(name).stem
    suffix = Path(name).suffix
    n = 2
    while True:
        candidate = folder / f"{stem}-dup{n}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def _write_sidecar(dest_pdf: Path, row: dict, inbound_name: str) -> Path:
    sidecar = Path(str(dest_pdf) + ".sidecar.md")
    canonical = row.get("output_path") or "(not yet converted)"
    sidecar.write_text(
        "\n".join(
            [
                "# Duplicate PDF (SHA-256 identity)",
                "",
                "Satyagraha Law Group — PDF to Markdown (SLIP).",
                "This file was **not** converted again. Filename is not identity.",
                "",
                f"- duplicate_filename: `{inbound_name}`",
                f"- sha256: `{row['sha256']}`",
                f"- original_filename: `{row['original_filename']}`",
                f"- original_status: `{row['status']}`",
                f"- canonical_markdown: `{canonical}`",
                f"- seen_at: `{iso_calcutta()}`",
                "",
                "The duplicate bytes were kept. The tool does not delete duplicates.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return sidecar


def _safe_move(src: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = _unique_dest(dest_dir, src.name)
    shutil.move(str(src), str(dest))
    return dest


def _safe_copy(src: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = _unique_dest(dest_dir, src.name)
    shutil.copy2(str(src), str(dest))
    return dest



def convert_pdf(
    pdf_path: Path,
    paths: SlipPaths,
    registry: Registry,
    *,
    engine_name: str = "pymupdf",
    repair_citations_flag: bool = False,
    move_raw: bool = True,
    batch_id: str | None = None,
) -> dict:
    pdf_path = Path(pdf_path)
    started = now_calcutta()
    result = _convert_pdf_impl(
        pdf_path,
        paths,
        registry,
        engine_name=engine_name,
        repair_citations_flag=repair_citations_flag,
        move_raw=move_raw,
    )
    completed = now_calcutta()
    record = build_record(
        started=started,
        completed=completed,
        pdf_name=pdf_path.name,
        result=result,
        engine_name=engine_name,
        batch_id=batch_id,
    )
    append_record(paths, record)
    result["started_at"] = record["started_at"]
    result["completed_at"] = record["completed_at"]
    result["duration_ms"] = record["duration_ms"]
    result["token_usage"] = record["token_usage"]
    return result

def _convert_pdf_impl(
    pdf_path: Path,
    paths: SlipPaths,
    registry: Registry,
    *,
    engine_name: str = "pymupdf",
    repair_citations_flag: bool = False,
    move_raw: bool = True,
) -> dict:
    pdf_path = Path(pdf_path)
    sha = sha256_file(pdf_path)
    existing = registry.get(sha)

    if existing and existing["status"] == STATUS_DONE:
        registry.see(pdf_path, routed_to=DUPLICATES, sha256=sha)
        copied = _safe_copy(pdf_path, paths.duplicates)
        sidecar = _write_sidecar(copied, existing, pdf_path.name)
        if move_raw and pdf_path.exists() and (paths.raw in pdf_path.parents or pdf_path.parent == paths.raw):
            try:
                _safe_move(pdf_path, paths.processed)
            except Exception:
                pass
        return {
            "sha256": sha,
            "status": STATUS_DONE,
            "duplicate": True,
            "sidecar": str(sidecar),
            "output": existing.get("output_path"),
        }

    routed = READY if registry.should_convert(sha) else DUPLICATES
    row = registry.see(pdf_path, routed_to=routed, sha256=sha)

    if not registry.should_convert(sha):
        copied = _safe_copy(pdf_path, paths.duplicates)
        sidecar = _write_sidecar(copied, row, pdf_path.name)
        return {
            "sha256": sha,
            "status": row["status"],
            "duplicate": True,
            "sidecar": str(sidecar),
            "output": row.get("output_path"),
        }

    registry.set_status(sha, STATUS_PROCESSING)
    paths.ready.mkdir(parents=True, exist_ok=True)
    ready_copy = _safe_copy(pdf_path, paths.ready)

    engine = get_engine(engine_name)
    try:
        result = engine.convert(ready_copy)
    except Exception as exc:
        note = paths.needs_review / f"{pdf_path.stem}.error.md"
        paths.needs_review.mkdir(parents=True, exist_ok=True)
        note.write_text(
            f"# NEEDS_REVIEW\n\nConversion raised: `{exc}`\n\nSource: `{pdf_path.name}`\nSHA-256: `{sha}`\n",
            encoding="utf-8",
        )
        registry.set_status(
            sha,
            STATUS_NEEDS_REVIEW,
            engine=engine_name,
            output_path=str(note),
            last_error=str(exc),
        )
        return {
            "sha256": sha,
            "status": STATUS_NEEDS_REVIEW,
            "duplicate": False,
            "output": str(note),
            "error": str(exc),
        }

    status = STATUS_NEEDS_REVIEW if result.needs_review else STATUS_DONE
    markdown = render_markdown(
        source_file=pdf_path.name,
        sha256=sha,
        status=status,
        engine=result.engine,
        pages=result.pages,
        repair=repair_citations_flag,
    )
    if status == STATUS_DONE:
        dest_dir = paths.clean
    else:
        dest_dir = paths.needs_review
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{pdf_path.stem}.md"
    if dest.exists():
        dest = dest_dir / f"{pdf_path.stem}-{sha[:12]}.md"
    dest.write_text(markdown, encoding="utf-8")
    registry.set_status(
        sha,
        status,
        engine=result.engine,
        page_count=result.page_count,
        output_path=str(dest),
        last_error="; ".join(result.warnings) if result.warnings else None,
    )
    if move_raw and pdf_path.exists() and (paths.raw in pdf_path.parents or pdf_path.parent == paths.raw):
        try:
            _safe_move(pdf_path, paths.processed)
        except Exception:
            pass
    return {
        "sha256": sha,
        "status": status,
        "duplicate": False,
        "output": str(dest),
        "page_count": result.page_count,
        "unrecovered_tables": result.unrecovered_tables,
        "warnings": result.warnings,
    }


def convert_vault(
    paths: SlipPaths,
    registry: Registry,
    *,
    engine_name: str = "pymupdf",
    repair_citations_flag: bool = False,
) -> list[dict]:
    pdfs = sorted(paths.raw.rglob("*.pdf")) + sorted(paths.raw.rglob("*.PDF"))
    # de-dupe case-insensitive glob on Windows
    seen = set()
    unique = []
    for pdf in pdfs:
        key = str(pdf.resolve()).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(pdf)
    results = []
    for pdf in unique:
        results.append(
            convert_pdf(
                pdf,
                paths,
                registry,
                engine_name=engine_name,
                repair_citations_flag=repair_citations_flag,
            )
        )
    return results
