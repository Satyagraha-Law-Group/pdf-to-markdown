"""Level A orchestration: hash, route, convert, write Markdown, update registry."""

from __future__ import annotations

import shutil
from pathlib import Path

from slip_pdf_md.citations import repair_citations
from slip_pdf_md.cleaning import collapse_leaders, demote_running_headers
from slip_pdf_md.engines import get_engine
from slip_pdf_md.fidelity import score_markdown_against_pdf
from slip_pdf_md.key_lease import (
    api_key_fingerprint,
    api_provider,
    current_remote_key,
    is_dummy_key,
    sentinel_path,
    uses_remote_api,
)
from slip_pdf_md.naming import iso_calcutta, now_calcutta
from slip_pdf_md.paths import DUPLICATES, READY, SlipPaths
from slip_pdf_md.progress import emit
from slip_pdf_md.registry import (
    CLOSED_STATUSES,
    EXTRACTED_STATUSES,
    STATUS_AWAITING_APPROVAL,
    STATUS_DONE,
    STATUS_NEEDS_REVIEW,
    STATUS_PROCESSING,
    Registry,
    format_duplicate_notice,
    sha256_file,
)
from slip_pdf_md.runlog import (
    append_record,
    build_record,
    build_token_usage,
    dumps_token_usage,
)
from slip_pdf_md.splitting import (
    MAX_BYTES_PER_PART,
    MAX_PAGES_PER_PART,
    needs_split,
    split_pdf,
    stem_folder_name,
)

FRONT_MATTER_KEYS = (
    "document_type",
    "source_file",
    "source_sha256",
    "processing_status",
    "engine",
    "page_count",
    "converted_at",
    "token_usage",
)


def yaml_front_matter(meta: dict) -> str:
    lines = ["---"]
    for key in FRONT_MATTER_KEYS:
        if key not in meta or meta[key] is None:
            continue
        value = meta[key]
        if isinstance(value, dict):
            value = dumps_token_usage(value)
        if isinstance(value, str) and (":" in value or value == "" or " " in value or "{" in value):
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
    token_usage: dict | str | None = None,
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
    if token_usage:
        meta["token_usage"] = token_usage
    return yaml_front_matter(meta) + "\n\n".join(chunks) + "\n"


def _unique_dest(folder: Path, name: str, sha: str | None = None) -> Path:
    dest = folder / name
    if not dest.exists():
        return dest
    stem = Path(name).stem
    suffix = Path(name).suffix
    if sha:
        candidate = folder / f"{stem}-{sha[:8]}{suffix}"
        if not candidate.exists():
            return candidate
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


def _safe_move(src: Path, dest_dir: Path, sha: str | None = None) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = _unique_dest(dest_dir, src.name, sha=sha)
    shutil.move(str(src), str(dest))
    return dest


def _safe_copy(src: Path, dest_dir: Path, sha: str | None = None) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = _unique_dest(dest_dir, src.name, sha=sha)
    shutil.copy2(str(src), str(dest))
    return dest


def _under(path: Path, folder: Path) -> bool:
    path = Path(path)
    folder = Path(folder)
    try:
        path.resolve().relative_to(folder.resolve())
        return True
    except ValueError:
        return folder in path.parents or path.parent == folder



def convert_pdf(
    pdf_path: Path,
    paths: SlipPaths,
    registry: Registry,
    *,
    engine_name: str = "pymupdf",
    repair_citations_flag: bool = False,
    move_raw: bool = True,
    batch_id: str | None = None,
    force: bool = False,
    progress=None,
    audit=None,
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
        force=force,
        progress=progress,
        audit=audit,
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
    force: bool = False,
    progress=None,
    audit=None,
) -> dict:
    pdf_path = Path(pdf_path)
    inbound_name = pdf_path.name

    def _p(frac: float, msg: str) -> None:
        if progress:
            progress(frac, msg)
        else:
            emit(frac, msg)

    def _log(step: str, detail: str = "", sha: str = "") -> None:
        if audit is not None:
            audit.step(inbound_name, sha, step, detail)

    input_bytes = pdf_path.stat().st_size if pdf_path.is_file() else 0
    _p(0.02, f"hashing {inbound_name}")
    sha = sha256_file(pdf_path)
    _log("hashed", f"bytes={input_bytes}", sha=sha)
    existing = registry.get(sha)
    in_raw = _under(pdf_path, paths.raw)
    in_ready = _under(pdf_path, paths.ready)

    def _dup_return(row: dict, dest_pdf: Path, sidecar: Path) -> dict:
        row = dict(row)
        row["sha256"] = sha
        _log("duplicate", f"first_seen_as={row.get('original_filename')}", sha=sha)
        return {
            "sha256": sha,
            "status": row.get("status") or STATUS_DONE,
            "duplicate": True,
            "sidecar": str(sidecar),
            "output": row.get("output_path"),
            "source_file": inbound_name,
            "source_path": str(dest_pdf),
            "input_bytes": input_bytes,
            "moved_to": None,
            "routed_to": str(dest_pdf),
            "original_filename": row.get("original_filename"),
            "first_seen_at": row.get("first_seen_at"),
            "converted_at": row.get("converted_at"),
            "page_count": row.get("page_count"),
            "engine": row.get("engine"),
            "sightings": registry.count_sightings(sha),
            "duplicate_notice": format_duplicate_notice(
                row,
                inbound_name=inbound_name,
                sidecar=str(sidecar),
                sightings=registry.count_sightings(sha),
            ),
        }

    if not force and not registry.gubernatio_should_convert(sha):
        gub_row = registry.gubernatio_done_row(sha) or existing or {}
        row = registry.see(pdf_path, routed_to=DUPLICATES, sha256=sha)
        if row.get("status") not in EXTRACTED_STATUSES:
            sync = gub_row.get("status")
            if sync not in EXTRACTED_STATUSES:
                sync = STATUS_AWAITING_APPROVAL
            registry.set_status(
                sha,
                sync,
                engine=gub_row.get("engine"),
                page_count=gub_row.get("page_count"),
                output_path=gub_row.get("output_path"),
            )
            row = registry.get(sha) or row
        dest_dir = paths.bucket(paths.duplicates)
        if pdf_path.exists() and (in_raw or in_ready):
            parked = _safe_move(pdf_path, dest_dir, sha=sha)
        else:
            parked = _safe_copy(pdf_path, dest_dir, sha=sha)
        sidecar = _write_sidecar(parked, row, inbound_name)
        _log("moved_to_duplicates", str(parked), sha=sha)
        _p(1.0, f"duplicate {inbound_name}")
        return _dup_return(row, parked, sidecar)

    if not force:
        routed = READY if registry.gubernatio_should_convert(sha) else DUPLICATES
        row = registry.see(pdf_path, routed_to=routed, sha256=sha)
        if not registry.gubernatio_should_convert(sha):
            dest_dir = paths.bucket(paths.duplicates)
            if pdf_path.exists() and (in_raw or in_ready):
                parked = _safe_move(pdf_path, dest_dir, sha=sha)
            else:
                parked = _safe_copy(pdf_path, dest_dir, sha=sha)
            sidecar = _write_sidecar(parked, row, inbound_name)
            _log("moved_to_duplicates", str(parked), sha=sha)
            return _dup_return(row, parked, sidecar)
    else:
        registry.see(pdf_path, routed_to=READY, sha256=sha)

    lease_fp = None
    lease_sentinel = None
    if uses_remote_api(engine_name):
        key = current_remote_key(engine_name, vault_root=paths.root)
        if key and not is_dummy_key(key):
            lease_fp = api_key_fingerprint(key)
            lease_sentinel = sentinel_path(paths.registry_dir)
            got = registry.acquire_key_lease(
                fingerprint=lease_fp,
                sentinel=lease_sentinel,
                sha256=sha,
                filename=inbound_name,
                api_provider=api_provider(engine_name),
            )
            if not got.get("ok"):
                _log(
                    "key_lease_halt",
                    f"host={got.get('holder_host')} agent={got.get('holder_agent')} until={got.get('expires_at')}",
                    sha=sha,
                )
                _p(1.0, "HALTED mistral key lease held")
                return {
                    "sha256": sha,
                    "status": "HALTED",
                    "duplicate": False,
                    "error": "mistral key lease held",
                    "source_file": inbound_name,
                    "input_bytes": input_bytes,
                    "lease": got,
                    "sentinel": got.get("sentinel"),
                }
            _log("key_lease_acquire", f"until={got.get('expires_at')}", sha=sha)

    work = pdf_path
    if in_raw and pdf_path.exists() and move_raw:
        _p(0.06, "moving RAW to READY_FOR_DOCLING")
        stem_home = paths.bucket(paths.ready) / stem_folder_name(inbound_name)
        stem_home.mkdir(parents=True, exist_ok=True)
        work = _safe_move(pdf_path, stem_home, sha=sha)
        _log("moved_to_ready", str(work), sha=sha)
        in_ready = True
        in_raw = False

    registry.set_status(sha, STATUS_PROCESSING)
    _log("processing", f"engine={engine_name} work={work}", sha=sha)

    jobs = [work]
    parts_dir = work.parent / "parts" if work.parent.name != "parts" else work.parent
    split_happened = False
    if work.exists() and needs_split(
        work, max_pages=MAX_PAGES_PER_PART, max_bytes=MAX_BYTES_PER_PART
    ):
        _p(0.08, "splitting oversized PDF at READY")
        jobs = split_pdf(
            work,
            parts_dir,
            max_pages=MAX_PAGES_PER_PART,
            max_bytes=MAX_BYTES_PER_PART,
        )
        split_happened = True
        _log(
            "split",
            f"parts={len(jobs)} max_pages={MAX_PAGES_PER_PART} max_mb={MAX_BYTES_PER_PART // (1024 * 1024)}",
            sha=sha,
        )

    engine = get_engine(engine_name)
    engine.on_progress = lambda frac, msg: _p(0.12 + max(0.0, min(1.0, frac)) * 0.70, msg)
    _p(0.10, f"engine {engine_name} jobs={len(jobs)}")
    part_pages: list[list[str]] = []
    part_warnings: list[str] = []
    last_result = None
    try:
        for job_index, job in enumerate(jobs, 1):
            _log("convert_part", f"{job_index}/{len(jobs)} {job.name}", sha=sha)
            last_result = engine.convert(job)
            if lease_fp:
                registry.heartbeat_key_lease(
                    fingerprint=lease_fp, sha256=sha, filename=inbound_name
                )
            part_pages.append(list(last_result.pages))
            part_warnings.extend(list(last_result.warnings))
        result = last_result
        if result is None:
            raise RuntimeError("no convert jobs")
        if split_happened:
            flat_pages: list[str] = []
            for pages in part_pages:
                flat_pages.extend(pages)
            result.pages = flat_pages
            result.page_count = len(flat_pages)
            result.warnings = part_warnings
            result.needs_review = bool(result.needs_review)
    except Exception as exc:
        _log("convert_error", str(exc), sha=sha)
        note_dir = paths.bucket(paths.needs_review)
        note = note_dir / f"{Path(inbound_name).stem}.error.md"
        note.write_text(
            f"# NEEDS_REVIEW\n\nConversion raised: `{exc}`\n\nSource: `{inbound_name}`\nSHA-256: `{sha}`\n",
            encoding="utf-8",
        )
        if in_ready and work.exists():
            try:
                _safe_move(work, note_dir, sha=sha)
            except Exception:
                pass
        registry.set_status(
            sha,
            STATUS_NEEDS_REVIEW,
            engine=engine_name,
            output_path=str(note),
            last_error=str(exc),
        )
        if lease_fp and lease_sentinel is not None:
            try:
                registry.release_key_lease(
                    fingerprint=lease_fp,
                    sentinel=lease_sentinel,
                    sha256=sha,
                    filename=inbound_name,
                )
                _log("key_lease_release", str(lease_sentinel), sha=sha)
            except Exception:
                pass
        return {
            "sha256": sha,
            "status": STATUS_NEEDS_REVIEW,
            "duplicate": False,
            "output": str(note),
            "error": str(exc),
            "source_file": inbound_name,
            "input_bytes": input_bytes,
        }

    status = STATUS_NEEDS_REVIEW if result.needs_review else STATUS_AWAITING_APPROVAL
    markdown = render_markdown(
        source_file=inbound_name,
        sha256=sha,
        status=status,
        engine=result.engine,
        pages=result.pages,
        repair=repair_citations_flag,
    )
    warnings = list(result.warnings)
    fidelity_src = work if work.exists() else pdf_path
    fidelity = score_markdown_against_pdf(fidelity_src, markdown)
    if not fidelity["passed"]:
        status = STATUS_NEEDS_REVIEW
        warnings.append(
            f"fidelity_recall={fidelity['overall_recall']} < {fidelity['threshold']}"
        )
        markdown = render_markdown(
            source_file=inbound_name,
            sha256=sha,
            status=status,
            engine=result.engine,
            pages=result.pages,
            repair=repair_citations_flag,
        )
    dest_dir = paths.needs_review if status == STATUS_NEEDS_REVIEW else paths.clean
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{Path(inbound_name).stem}.md"
    if dest.exists() and not force:
        dest = dest_dir / f"{Path(inbound_name).stem}-{sha[:12]}.md"
    engine_usage = getattr(result, "usage", None) or {}
    token_usage = build_token_usage(
        markdown_text=markdown,
        page_count=result.page_count,
        engine_name=result.engine,
        llm_input_tokens=engine_usage.get("llm_input_tokens") or 0,
        llm_output_tokens=engine_usage.get("llm_output_tokens") or 0,
        mistral_pages_processed=engine_usage.get("mistral_pages_processed"),
        include_notes=False,
    )
    markdown = render_markdown(
        source_file=inbound_name,
        sha256=sha,
        status=status,
        engine=result.engine,
        pages=result.pages,
        repair=repair_citations_flag,
        token_usage=token_usage,
    )
    dest.write_text(markdown, encoding="utf-8")
    if not fidelity["passed"]:
        note = paths.needs_review / f"{Path(inbound_name).stem}.fidelity.md"
        note.write_text(
            "# NEEDS_REVIEW — fidelity gate\n\n"
            f"overall_recall: {fidelity['overall_recall']}\n"
            f"threshold: {fidelity['threshold']}\n"
            f"pages: {fidelity['page_scores']}\n"
            f"markdown: `{dest}`\n",
            encoding="utf-8",
        )
    registry.set_status(
        sha,
        status,
        engine=result.engine,
        page_count=result.page_count,
        output_path=str(dest),
        last_error="; ".join(warnings) if warnings else None,
        token_usage=dumps_token_usage(token_usage),
    )
    from slip_pdf_md.catalog import api_key_type_for, markdown_page_count
    registry.record_process_run(
        filename=inbound_name,
        sha256=sha,
        pdf_page_count=result.page_count,
        markdown_page_count=markdown_page_count(str(dest)),
        api_key_type=api_key_type_for(result.engine),
        api_provider=result.engine,
        status=status,
        approved=status in CLOSED_STATUSES,
        token_usage=dumps_token_usage(token_usage),
        output_path=str(dest),
        source="convert",
    )
    _log("converted", f"status={status} markdown={dest}", sha=sha)
    moved_to = None
    if split_happened and status in EXTRACTED_STATUSES:
        if parts_dir.exists() and parts_dir.name == "parts":
            shutil.rmtree(parts_dir, ignore_errors=True)
        _log("deleted_parts", f"count={len(jobs)}", sha=sha)
    ready_home = work.parent if work.exists() else None
    if in_ready and work.exists():
        try:
            stem = stem_folder_name(inbound_name)
            if status in EXTRACTED_STATUSES:
                _p(0.97, "moving original PDF to PROCESSED / Stem")
                dest_home = paths.bucket(paths.processed) / stem
                dest_home.mkdir(parents=True, exist_ok=True)
                parked = _safe_move(work, dest_home, sha=sha)
                moved_to = str(parked)
                _log("moved_to_processed", moved_to, sha=sha)
            else:
                dest_home = paths.bucket(paths.needs_review) / stem
                dest_home.mkdir(parents=True, exist_ok=True)
                parked = _safe_move(work, dest_home, sha=sha)
                moved_to = str(parked)
                _log("moved_to_needs_review", moved_to, sha=sha)
        except Exception:
            moved_to = None
    if ready_home is not None:
        try:
            if ready_home.is_dir() and not any(ready_home.iterdir()):
                ready_home.rmdir()
        except OSError:
            pass
    if lease_fp and lease_sentinel is not None:
        try:
            registry.release_key_lease(
                fingerprint=lease_fp,
                sentinel=lease_sentinel,
                sha256=sha,
                filename=inbound_name,
            )
            _log("key_lease_release", str(lease_sentinel), sha=sha)
        except Exception:
            pass
    _p(1.0, f"finished {inbound_name} [{status}]")
    return {
        "sha256": sha,
        "status": status,
        "duplicate": False,
        "output": str(dest),
        "page_count": result.page_count,
        "unrecovered_tables": result.unrecovered_tables,
        "warnings": warnings,
        "fidelity": fidelity,
        "llm_input_tokens": (getattr(result, "usage", None) or {}).get("llm_input_tokens") or 0,
        "llm_output_tokens": (getattr(result, "usage", None) or {}).get("llm_output_tokens") or 0,
        "mistral_pages_processed": (getattr(result, "usage", None) or {}).get("mistral_pages_processed"),
        "token_usage": token_usage,
        "source_file": inbound_name,
        "source_path": str(work),
        "input_bytes": input_bytes,
        "moved_to": moved_to,
    }


def convert_vault(
    paths: SlipPaths,
    registry: Registry,
    *,
    engine_name: str = "pymupdf",
    repair_citations_flag: bool = False,
    force: bool = False,
    audit=None,
) -> list[dict]:
    from slip_pdf_md.auditcontrol import collect_sequential_pdfs
    from slip_pdf_md.progress import make_file_progress

    unique = collect_sequential_pdfs(paths)
    results = []
    total = len(unique)
    for index, pdf in enumerate(unique, 1):
        results.append(
            convert_pdf(
                pdf,
                paths,
                registry,
                engine_name=engine_name,
                repair_citations_flag=repair_citations_flag,
                force=force,
                progress=make_file_progress(index, total),
                audit=audit,
            )
        )
    return results
