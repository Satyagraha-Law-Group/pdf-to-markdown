"""Append-only conversion run log: start, finish, token usage.

Local engines (PyMuPDF / Tesseract) use zero LLM tokens. We still record:
- llm_input_tokens / llm_output_tokens (0 for slip-pdf-md convert)
- markdown_tokens_estimate: output size, chars/4
- equivalent_internal_vision_tokens_estimate: what an internal
  vision-LLM conversion of the same page count would have cost, using
  the 150 dpi high-detail tiling estimate of 1,105 input tokens/page
  plus markdown_tokens_estimate output tokens.
Mistral OCR is billed per page, not tokens; pages_processed is logged
under token_usage.mistral_pages_processed.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from slip_pdf_md.naming import (
    iso_calcutta,
    now_calcutta,
    resolve_generated_path,
    three_word_filename,
)
from slip_pdf_md.paths import SlipPaths

VISION_TOKENS_PER_PAGE = 1105  # 150 dpi, 512px tiles, high-detail formula
CHARS_PER_TOKEN = 4


TOKEN_USAGE_KEYS = (
    "llm_input_tokens",
    "llm_output_tokens",
    "llm_total_tokens",
    "markdown_tokens_estimate",
    "equivalent_internal_vision_input_tokens",
    "equivalent_internal_total_tokens",
    "mistral_pages_processed",
)


def estimate_markdown_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN)


def engine_token_note(engine_name: str) -> str:
    if str(engine_name).lower().startswith("mistral"):
        return (
            "mistral OCR is billed per page, not chat tokens; llm_* stay 0. "
            "mistral_pages_processed is the OCR page count returned by the API. "
            f"equivalent_internal_vision_input_tokens = page_count * {VISION_TOKENS_PER_PAGE}."
        )
    return (
        "slip-pdf-md convert uses local PyMuPDF/Tesseract; "
        "llm_* are 0 unless a future LLM engine is selected. "
        f"equivalent_internal_vision_input_tokens = page_count * {VISION_TOKENS_PER_PAGE} "
        "(150 dpi high-detail tile estimate)."
    )


def build_token_usage(
    *,
    markdown_text: str = "",
    page_count: int = 0,
    engine_name: str = "pymupdf",
    llm_input_tokens: int = 0,
    llm_output_tokens: int = 0,
    mistral_pages_processed: int | None = None,
    include_notes: bool = True,
) -> dict[str, Any]:
    """Token usage for one PDF-to-markdown convert of this file."""
    pages = int(page_count or 0)
    text = markdown_text or ""
    if pages == 0 and text:
        pages = text.count("## Page ")
    md_tokens = estimate_markdown_tokens(text) if text else 0
    llm_in = int(llm_input_tokens or 0)
    llm_out = int(llm_output_tokens or 0)
    vision_in = pages * VISION_TOKENS_PER_PAGE if pages else 0
    usage: dict[str, Any] = {
        "llm_input_tokens": llm_in,
        "llm_output_tokens": llm_out,
        "llm_total_tokens": llm_in + llm_out,
        "markdown_tokens_estimate": md_tokens,
        "equivalent_internal_vision_input_tokens": vision_in,
        "equivalent_internal_total_tokens": vision_in + md_tokens,
        "mistral_pages_processed": mistral_pages_processed,
    }
    if include_notes:
        usage["notes"] = engine_token_note(engine_name)
    return usage


def dumps_token_usage(usage: dict[str, Any] | str | None) -> str | None:
    """Compact JSON for the token_usage column. Notes stay in the run log."""
    if usage is None:
        return None
    if isinstance(usage, str):
        text = usage.strip()
        return text or None
    stored = {key: usage.get(key) for key in TOKEN_USAGE_KEYS}
    return json.dumps(stored, ensure_ascii=False, separators=(",", ":"))


def parse_token_usage(raw: str | dict | None) -> dict[str, Any]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def token_usage_summary(raw: str | dict | None) -> str:
    data = parse_token_usage(raw)
    if not data:
        return ""
    return (
        f"md={data.get('markdown_tokens_estimate', '')} "
        f"llm={data.get('llm_total_tokens', '')} "
        f"equiv={data.get('equivalent_internal_total_tokens', '')}"
    )


def logs_dir(paths: SlipPaths) -> Path:
    folder = paths.registry_dir / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def jsonl_path(paths: SlipPaths) -> Path:
    return resolve_generated_path(
        logs_dir(paths),
        "Conversion",
        "Runs",
        "Journal",
        "jsonl",
        legacy_names=("runs.jsonl",),
    )


def markdown_log_path(paths: SlipPaths) -> Path:
    return resolve_generated_path(
        logs_dir(paths),
        "Conversion",
        "Run",
        "Log",
        "md",
        legacy_names=("Conversion-Run-Log.md",),
    )


def _read_output_text(output: str | None) -> str:
    if not output:
        return ""
    path = Path(output)
    if path.is_file() and path.suffix.lower() in {".md", ".txt", ".html"}:
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return ""
    return ""


def build_record(
    *,
    started: datetime,
    completed: datetime,
    pdf_name: str,
    result: dict[str, Any],
    engine_name: str,
    batch_id: str | None = None,
) -> dict[str, Any]:
    output = result.get("output")
    text = _read_output_text(output)
    pages = int(result.get("page_count") or 0)
    usage = result.get("token_usage") or build_token_usage(
        markdown_text=text,
        page_count=pages,
        engine_name=engine_name,
        llm_input_tokens=int(result.get("llm_input_tokens") or 0),
        llm_output_tokens=int(result.get("llm_output_tokens") or 0),
        mistral_pages_processed=result.get("mistral_pages_processed"),
        include_notes=True,
    )
    pages = int(usage.get("page_count") or pages or 0)
    if pages == 0:
        pages = int(result.get("page_count") or 0)
        if pages == 0 and text:
            pages = text.count("## Page ")
    duration_ms = int((completed - started).total_seconds() * 1000)
    status = result.get("status") or "UNKNOWN"
    if result.get("duplicate"):
        status_label = "DUPLICATE"
    else:
        status_label = status
    return {
        "started_at": iso_calcutta(started),
        "completed_at": iso_calcutta(completed),
        "duration_ms": duration_ms,
        "source_file": pdf_name,
        "sha256": result.get("sha256"),
        "status": status_label,
        "duplicate": bool(result.get("duplicate")),
        "engine": engine_name,
        "page_count": pages,
        "output": output,
        "batch_id": batch_id,
        "token_usage": usage,
    }


def _ensure_markdown_header(path: Path) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    path.write_text(
        "\n".join(
            [
                "# Conversion Run Log",
                "",
                "Satyagraha Law Group — PDF to Markdown (SLIP).",
                "",
                "Each convert writes one row. Times are Asia/Calcutta.",
                "`llm_*` tokens are actual LLM usage (0 for the local engine and for Mistral OCR).",
                "`markdown_tokens_estimate` is the size of the output Markdown (chars/4).",
                "`equivalent_internal_total_tokens` is the estimated cost of converting",
                f"the same PDF internally with a vision LLM ({VISION_TOKENS_PER_PAGE} input tokens/page + markdown output).",
                "",
                "| started_at | completed_at | duration_ms | source_file | status | pages | llm_total | md_tokens_est | equivalent_internal_total |",
                "|---|---|---|---|---|---|---|---|---|",
                "",
            ]
        ),
        encoding="utf-8",
    )


def append_record(paths: SlipPaths, record: dict[str, Any]) -> Path:
    line = json.dumps(record, ensure_ascii=False)
    jsonl = jsonl_path(paths)
    with jsonl.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")

    md = markdown_log_path(paths)
    _ensure_markdown_header(md)
    tok = record["token_usage"]
    source = str(record.get("source_file") or "").replace("|", "/")
    row = (
        f"| {record['started_at']} | {record['completed_at']} | {record['duration_ms']} "
        f"| `{source}` | {record['status']} | {record['page_count']} "
        f"| {tok['llm_total_tokens']} | {tok['markdown_tokens_estimate']} "
        f"| {tok['equivalent_internal_total_tokens']} |"
    )
    with md.open("a", encoding="utf-8") as handle:
        handle.write(row + "\n")
    return jsonl


def write_batch_summary(paths: SlipPaths, records: list[dict[str, Any]]) -> Path | None:
    if not records:
        return None
    started = min(r["started_at"] for r in records)
    completed = max(r["completed_at"] for r in records)
    moment = now_calcutta()
    name = three_word_filename("Conversion", "Batch", "Summary", ext="md", moment=moment)
    dest = logs_dir(paths) / name
    llm = sum(r["token_usage"]["llm_total_tokens"] for r in records)
    md_tok = sum(r["token_usage"]["markdown_tokens_estimate"] for r in records)
    equiv = sum(r["token_usage"]["equivalent_internal_total_tokens"] for r in records)
    lines = [
        "# Conversion Batch Summary",
        "",
        "Satyagraha Law Group — PDF to Markdown (SLIP).",
        "",
        f"- started_at: `{started}`",
        f"- completed_at: `{completed}`",
        f"- files: {len(records)}",
        f"- llm_total_tokens: {llm}",
        f"- markdown_tokens_estimate: {md_tok}",
        f"- equivalent_internal_total_tokens: {equiv}",
        "",
        "See the Conversion-Run-Log and Conversion-Runs-Journal files for per-file rows.",
        "",
    ]
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest
