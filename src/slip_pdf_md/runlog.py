"""Append-only conversion run log: start, finish, token usage.

Local engines (PyMuPDF / Tesseract) use zero LLM tokens. We still record:
- llm_input_tokens / llm_output_tokens (0 for slip-pdf-md convert)
- markdown_tokens_estimate: output size, chars/4
- equivalent_internal_vision_tokens_estimate: what an internal
  vision-LLM conversion of the same page count would have cost, using
  the 150 dpi high-detail tiling estimate of 1,105 input tokens/page
  plus markdown_tokens_estimate output tokens.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from slip_pdf_md.naming import iso_calcutta, now_calcutta, three_word_filename
from slip_pdf_md.paths import SlipPaths

VISION_TOKENS_PER_PAGE = 1105  # 150 dpi, 512px tiles, high-detail formula
CHARS_PER_TOKEN = 4


def estimate_markdown_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN)


def logs_dir(paths: SlipPaths) -> Path:
    folder = paths.registry_dir / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def jsonl_path(paths: SlipPaths) -> Path:
    return logs_dir(paths) / "runs.jsonl"


def markdown_log_path(paths: SlipPaths) -> Path:
    return logs_dir(paths) / "Conversion-Run-Log.md"


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
    md_tokens = estimate_markdown_tokens(text)
    pages = int(result.get("page_count") or 0)
    if pages == 0 and text:
        pages = text.count("## Page ")
    llm_in = int(result.get("llm_input_tokens") or 0)
    llm_out = int(result.get("llm_output_tokens") or 0)
    vision_in = pages * VISION_TOKENS_PER_PAGE if pages else 0
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
        "token_usage": {
            "llm_input_tokens": llm_in,
            "llm_output_tokens": llm_out,
            "llm_total_tokens": llm_in + llm_out,
            "markdown_tokens_estimate": md_tokens,
            "equivalent_internal_vision_input_tokens": vision_in,
            "equivalent_internal_total_tokens": vision_in + md_tokens,
            "notes": (
                "slip-pdf-md convert uses local PyMuPDF/Tesseract; "
                "llm_* are 0 unless a future LLM engine is selected. "
                f"equivalent_internal_vision_input_tokens = page_count * {VISION_TOKENS_PER_PAGE} "
                "(150 dpi high-detail tile estimate)."
            ),
        },
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
                "`llm_*` tokens are actual LLM usage (0 for the local engine).",
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
        "See `Conversion-Run-Log.md` and `runs.jsonl` for per-file rows.",
        "",
    ]
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest
