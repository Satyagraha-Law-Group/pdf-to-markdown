"""Per-session convert summary for the lawyer (markdown, three-word name)."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from slip_pdf_md.branding import (
    footer_markdown,
    header_markdown,
    with_single_footer,
)
from slip_pdf_md.naming import iso_calcutta, now_calcutta, three_word_filename
from slip_pdf_md.paths import SlipPaths
from slip_pdf_md.runlog import logs_dir


def _user_block() -> list[str]:
    return [
        f"- name: `{os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown'}`",
        f"- computer: `{os.environ.get('COMPUTERNAME') or os.environ.get('HOSTNAME') or 'unknown'}`",
        "- organization: Satyagraha Law Group",
    ]


def write_session_summary(
    paths: SlipPaths,
    results: list[dict[str, Any]],
    *,
    engine: str,
    started: datetime,
    completed: datetime | None = None,
) -> Path:
    completed = completed or now_calcutta()
    dest = logs_dir(paths) / three_word_filename("Session", "Convert", "Summary", ext="md", moment=completed)
    done = [r for r in results if r.get("status") == "DONE" and not r.get("duplicate")]
    dups = [r for r in results if r.get("duplicate")]
    review = [r for r in results if r.get("status") == "NEEDS_REVIEW"]
    duration_ms = int((completed - started).total_seconds() * 1000)
    in_bytes = 0
    out_bytes = 0
    pages = 0
    for row in results:
        src = row.get("source_path") or ""
        if src and Path(src).is_file():
            try:
                in_bytes += Path(src).stat().st_size
            except OSError:
                pass
        elif row.get("input_bytes"):
            in_bytes += int(row["input_bytes"] or 0)
        out = row.get("output")
        if out and Path(str(out)).is_file():
            try:
                out_bytes += Path(str(out)).stat().st_size
            except OSError:
                pass
        pages += int(row.get("page_count") or 0)

    lines = [
        header_markdown(),
        "# Session Convert Summary",
        "",
        "## User",
        "",
        *_user_block(),
        "",
        "## Clock",
        "",
        f"- tool_start: `{iso_calcutta(started)}`",
        f"- tool_finish: `{iso_calcutta(completed)}`",
        f"- duration_ms: `{duration_ms}`",
        f"- engine: `{engine}`",
        "",
        "## Totals",
        "",
        f"- files_in_session: {len(results)}",
        f"- converted_done: {len(done)}",
        f"- duplicates: {len(dups)}",
        f"- needs_review: {len(review)}",
        f"- input_bytes: {in_bytes}",
        f"- output_bytes: {out_bytes}",
        f"- pages: {pages}",
        "",
        "## Files processed",
        "",
        "| file | status | pages | token_usage | output |",
        "| --- | --- | ---: | --- | --- |",
    ]
    from slip_pdf_md.runlog import token_usage_summary
    for row in results:
        mark = "DUP" if row.get("duplicate") else row.get("status")
        name = row.get("source_file") or Path(str(row.get("source_path") or row.get("output") or "")).name
        tok = token_usage_summary(row.get("token_usage"))
        lines.append(
            f"| `{name}` | {mark} | {row.get('page_count') or ''} | {tok} | `{row.get('output') or row.get('sidecar') or ''}` |"
        )
    lines += [
        "",
        "The Conversion-Run-Log next to this file has per-file token rows.",
        "GUBERNATIO and documents both store a token_usage column for that convert.",
        "",
        footer_markdown(),
    ]
    dest.write_text(with_single_footer("\n".join(lines)), encoding="utf-8")
    return dest


def format_lawyer_recap(results: list[dict[str, Any]], session_path: Path) -> str:
    done = sum(1 for r in results if r.get("status") == "DONE" and not r.get("duplicate"))
    dups = sum(1 for r in results if r.get("duplicate"))
    review = sum(1 for r in results if r.get("status") == "NEEDS_REVIEW")
    return (
        f"Session finished. converted={done} duplicates={dups} needs_review={review}\n"
        f"Summary: {session_path}"
    )
