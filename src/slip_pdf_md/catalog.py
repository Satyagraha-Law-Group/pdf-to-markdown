"""Canonical test-run, process-run, and error-code catalogs.

These tables live in the Document-Hash-Registry sqlite next to GUBERNATIO.
Future tests upsert TEST_CASES first. Reports are generated from the tables,
not from a one-off pytest memory dump. Convert writes PROCESS_RUNS (day, file,
PDF pages, markdown pages, API key type, approval status). ERROR_CODES is the
classified error book; new features register a code here.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from slip_pdf_md.branding import (
    footer_markdown,
    header_markdown,
    html_wrap,
    with_single_footer,
)
from slip_pdf_md.naming import (
    iso_calcutta,
    now_calcutta,
    resolve_generated_path,
)

PREFIX = {
    "smoke": "SMO",
    "unit": "UNT",
    "functionality": "FUN",
    "integration": "INT",
    "system": "SYS",
    "uat": "UAT",
    "security": "SEC",
    "integrity": "FID",
    "regression": "REG",
    "performance": "PER",
}

CATALOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS TEST_CASES (
    case_id        TEXT PRIMARY KEY,
    function_name  TEXT NOT NULL UNIQUE,
    source_file    TEXT,
    category       TEXT NOT NULL,
    title          TEXT NOT NULL,
    description    TEXT NOT NULL,
    first_seen_at  TEXT NOT NULL,
    last_seen_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_test_cases_category ON TEST_CASES(category);

CREATE TABLE IF NOT EXISTS TEST_RUNS (
    run_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    run_day              TEXT NOT NULL,
    started_at           TEXT NOT NULL,
    finished_at          TEXT,
    host                 TEXT,
    agent                TEXT,
    total                INTEGER,
    passed               INTEGER,
    failed               INTEGER,
    skipped              INTEGER,
    report_summary_path  TEXT,
    report_detailed_path TEXT
);
CREATE INDEX IF NOT EXISTS idx_test_runs_day ON TEST_RUNS(run_day);

CREATE TABLE IF NOT EXISTS TEST_RESULTS (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id         INTEGER NOT NULL,
    case_id        TEXT NOT NULL,
    function_name  TEXT,
    result         TEXT NOT NULL,
    duration_ms    INTEGER
);
CREATE INDEX IF NOT EXISTS idx_test_results_run ON TEST_RESULTS(run_id);

CREATE TABLE IF NOT EXISTS PROCESS_RUNS (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    run_day              TEXT NOT NULL,
    seen_at              TEXT NOT NULL,
    filename             TEXT NOT NULL,
    sha256               TEXT,
    pdf_page_count       INTEGER,
    markdown_page_count  INTEGER,
    api_key_type         TEXT,
    api_provider         TEXT,
    status               TEXT,
    approved             INTEGER NOT NULL DEFAULT 0,
    token_usage          TEXT,
    output_path          TEXT,
    source               TEXT
);
CREATE INDEX IF NOT EXISTS idx_process_runs_day ON PROCESS_RUNS(run_day);
CREATE INDEX IF NOT EXISTS idx_process_runs_sha ON PROCESS_RUNS(sha256);

CREATE TABLE IF NOT EXISTS ERROR_CODES (
    error_code            TEXT PRIMARY KEY,
    error_type            TEXT NOT NULL,
    error_category        TEXT NOT NULL,
    error_message         TEXT NOT NULL,
    suggested_resolution  TEXT NOT NULL,
    source_module         TEXT,
    first_seen_at         TEXT NOT NULL,
    last_updated_at       TEXT NOT NULL
);
"""

SEED_ERRORS = [
    ("SLIP-E-001", "registry", "HIGH",
     "Live sqlite failed integrity_check and the sibling backup could not repair it.",
     "Run slip-pdf-md registry restore --vault PATH. If both copies are gone, rebuild from markdown front matter.",
     "registry"),
    ("SLIP-E-002", "secrets", "HIGH",
     "A remote-API convert was requested but no API key is available.",
     "Put the key in gitignored SECRETS.txt or the environment. Local Tesseract needs no key.",
     "secrets"),
    ("SLIP-E-003", "security", "HIGH",
     "A raw API key was offered to GUBERNATIO. Only a SHA-256 fingerprint is stored.",
     "Pass api_key_fingerprint(key), never the secret. Confirm SECRETS.txt is gitignored.",
     "key_lease"),
    ("SLIP-E-004", "lease", "HIGH",
     "Convert HALTed because the same API-key fingerprint is already in use.",
     "Wait until the other agent finishes, or use a different key. Abandoned leases free after 15 minutes. RAW is unmoved.",
     "key_lease"),
    ("SLIP-E-005", "fidelity", "HIGH",
     "Markdown failed the fidelity gate against the PDF. Status is NEEDS_REVIEW.",
     "Open the NEEDS_REVIEW note. Repair citations or reconvert with the other engine. Do not treat the file as approved.",
     "fidelity"),
    ("SLIP-E-006", "convert", "HIGH",
     "Conversion raised an exception. The PDF is routed to NEEDS_REVIEW.",
     "Read the .error.md next to the file. Fix the engine or the PDF and convert again.",
     "convert"),
    ("SLIP-E-007", "lease", "HIGH",
     "The key-lease sentinel file could not be created exclusively.",
     "Confirm the sentinel name is exactly SLG-pdf_to_md_file_naming_convention.text next to the sqlite, not inside it.",
     "key_lease"),
    ("SLIP-E-008", "approve", "HIGH",
     "Approve was called on a document whose status cannot be closed.",
     "Only AWAITING_APPROVAL or NEEDS_REVIEW may be approved. Check GUBERNATIO for the current status.",
     "registry"),
    ("SLIP-E-010", "duplicate", "MEDIUM",
     "This PDF bytes were already extracted. The inbound file is parked in DUPLICATES.",
     "Use the canonical markdown. Do not reconvert unless a lawyer passes --force and chooses an engine.",
     "convert"),
    ("SLIP-E-011", "split", "MEDIUM",
     "The PDF exceeded 100 pages or 100 MB and was split at READY.",
     "This is expected. Confirm one merged markdown and that part PDFs were deleted after a clean convert.",
     "splitting"),
    ("SLIP-E-012", "lease", "MEDIUM",
     "An expired RUNNING lease was treated as free so the next convert could proceed.",
     "No action if the previous agent finished. If two converts overlapped, inspect GUBERNATIO lease rows.",
     "key_lease"),
    ("SLIP-E-013", "output", "MEDIUM",
     "The destination markdown already existed; a SHA-prefixed filename was used.",
     "Open the SHA-prefixed file. Consider --force only after a lawyer chooses the engine.",
     "convert"),
    ("SLIP-E-014", "tables", "MEDIUM",
     "One or more tables were not recovered into markdown pipe tables.",
     "Inspect the page. Use Mistral for scans, or repair with the table-recovery playbook.",
     "tables"),
    ("SLIP-E-015", "engine", "MEDIUM",
     "Tesseract is not installed. Scanned pages will not OCR on the local engine.",
     "Install Tesseract, or convert with Mistral AI (the PDF is uploaded).",
     "doctor"),
    ("SLIP-E-016", "backup", "MEDIUM",
     "The live registry was missing and was restored from the sibling .bak.",
     "Confirm Document-Hash-Registry-vN-stamp.sqlite and its .bak both exist after the restore.",
     "registry"),
    ("SLIP-E-020", "empty", "LOW",
     "A PDF page had no extractable text after OCR.",
     "Confirm the scan is readable. Reconvert with the other engine if the page should have text.",
     "convert"),
    ("SLIP-E-021", "naming", "LOW",
     "A generated artifact did not match the three-word filename convention.",
     "Use Word1-Word2-Word3-vN-DD-MM-YYYY-HH-MI-SS. Do not rename pipeline folders.",
     "naming"),
    ("SLIP-E-022", "wiki", "LOW",
     "A documentation wiki link does not resolve to a file.",
     "Add the file or the WIKI_CATALOG entry, then re-run the user-guide integrity check.",
     "wiki_graph"),
]


def calcutta_day() -> str:
    return now_calcutta().strftime("%Y-%m-%d")


def markdown_page_count(output_path: str | None) -> int:
    if not output_path:
        return 0
    path = Path(output_path)
    if not path.is_file():
        return 0
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return 0
    return text.count("## Page ")


def api_key_type_for(engine_name: str | None) -> str:
    name = (engine_name or "").lower()
    if name.startswith("mistral"):
        return "mistral"
    if "pymupdf" in name or "tesseract" in name or name in {"local", ""}:
        return "local_tesseract"
    return name or "unknown"


def ensure_catalog(conn: sqlite3.Connection) -> None:
    conn.executescript(CATALOG_SCHEMA)
    conn.commit()
    seed_errors(conn)


def seed_errors(conn: sqlite3.Connection) -> None:
    now = iso_calcutta()
    for code, typ, cat, msg, fix, module in SEED_ERRORS:
        row = conn.execute("SELECT error_code FROM ERROR_CODES WHERE error_code = ?", (code,)).fetchone()
        if row is None:
            conn.execute(
                """
                INSERT INTO ERROR_CODES (
                    error_code, error_type, error_category, error_message,
                    suggested_resolution, source_module, first_seen_at, last_updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (code, typ, cat, msg, fix, module, now, now),
            )
        else:
            conn.execute(
                """
                UPDATE ERROR_CODES
                   SET error_type = ?, error_category = ?, error_message = ?,
                       suggested_resolution = ?, source_module = ?, last_updated_at = ?
                 WHERE error_code = ?
                """,
                (typ, cat, msg, fix, module, now, code),
            )
    conn.commit()


def register_error(
    conn: sqlite3.Connection,
    *,
    error_code: str,
    error_type: str,
    error_category: str,
    error_message: str,
    suggested_resolution: str,
    source_module: str | None = None,
) -> None:
    cat = error_category.upper()
    if cat not in {"HIGH", "MEDIUM", "LOW"}:
        raise ValueError("error_category must be HIGH, MEDIUM, or LOW")
    now = iso_calcutta()
    row = conn.execute("SELECT error_code FROM ERROR_CODES WHERE error_code = ?", (error_code,)).fetchone()
    if row is None:
        conn.execute(
            """
            INSERT INTO ERROR_CODES (
                error_code, error_type, error_category, error_message,
                suggested_resolution, source_module, first_seen_at, last_updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (error_code, error_type, cat, error_message, suggested_resolution, source_module, now, now),
        )
    else:
        conn.execute(
            """
            UPDATE ERROR_CODES
               SET error_type = ?, error_category = ?, error_message = ?,
                   suggested_resolution = ?, source_module = ?, last_updated_at = ?
             WHERE error_code = ?
            """,
            (error_type, cat, error_message, suggested_resolution, source_module, now, error_code),
        )
    conn.commit()


def upsert_test_case(
    conn: sqlite3.Connection,
    *,
    function_name: str,
    source_file: str,
    category: str,
    title: str,
    description: str,
) -> str:
    """Insert or refresh a test case. New cases get the next TC-XXX-NNN in that category."""
    now = iso_calcutta()
    row = conn.execute(
        "SELECT case_id FROM TEST_CASES WHERE function_name = ?",
        (function_name,),
    ).fetchone()
    if row is not None:
        conn.execute(
            """
            UPDATE TEST_CASES
               SET source_file = ?, category = ?, title = ?, description = ?, last_seen_at = ?
             WHERE function_name = ?
            """,
            (source_file, category, title, description, now, function_name),
        )
        conn.commit()
        return str(row[0])
    prefix = PREFIX.get(category, "FUN")
    n = conn.execute(
        "SELECT COUNT(*) FROM TEST_CASES WHERE case_id LIKE ?",
        (f"TC-{prefix}-%",),
    ).fetchone()[0]
    case_id = f"TC-{prefix}-{int(n) + 1:03d}"
    conn.execute(
        """
        INSERT INTO TEST_CASES (
            case_id, function_name, source_file, category, title, description,
            first_seen_at, last_seen_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (case_id, function_name, source_file, category, title, description, now, now),
    )
    conn.commit()
    return case_id


def start_test_run(conn: sqlite3.Connection, *, host: str | None = None, agent: str | None = None) -> int:
    import os
    cur = conn.execute(
        """
        INSERT INTO TEST_RUNS (run_day, started_at, host, agent, total, passed, failed, skipped)
        VALUES (?, ?, ?, ?, 0, 0, 0, 0)
        """,
        (
            calcutta_day(),
            iso_calcutta(),
            host or os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME"),
            agent or os.environ.get("SLIP_AGENT") or "Spock",
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def finish_test_run(
    conn: sqlite3.Connection,
    run_id: int,
    *,
    results: list[dict[str, Any]],
    summary_path: str | None = None,
    detailed_path: str | None = None,
) -> None:
    passed = sum(1 for r in results if r.get("result") == "PASS")
    failed = sum(1 for r in results if r.get("result") == "FAIL")
    skipped = sum(1 for r in results if r.get("result") == "SKIP")
    for rec in results:
        conn.execute(
            """
            INSERT INTO TEST_RESULTS (run_id, case_id, function_name, result, duration_ms)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rec.get("id") or rec.get("case_id"),
                rec.get("function_name"),
                rec.get("result") or "NOT RUN",
                rec.get("duration_ms"),
            ),
        )
    conn.execute(
        """
        UPDATE TEST_RUNS
           SET finished_at = ?, total = ?, passed = ?, failed = ?, skipped = ?,
               report_summary_path = ?, report_detailed_path = ?
         WHERE run_id = ?
        """,
        (
            iso_calcutta(),
            len(results),
            passed,
            failed,
            skipped,
            summary_path,
            detailed_path,
            run_id,
        ),
    )
    conn.commit()


def record_process_run(
    conn: sqlite3.Connection,
    *,
    filename: str,
    sha256: str | None,
    pdf_page_count: int | None,
    markdown_page_count: int | None,
    api_key_type: str | None,
    api_provider: str | None,
    status: str | None,
    approved: bool,
    token_usage: str | None,
    output_path: str | None,
    source: str = "convert",
) -> int:
    cur = conn.execute(
        """
        INSERT INTO PROCESS_RUNS (
            run_day, seen_at, filename, sha256, pdf_page_count, markdown_page_count,
            api_key_type, api_provider, status, approved, token_usage, output_path, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            calcutta_day(),
            iso_calcutta(),
            filename,
            sha256,
            pdf_page_count,
            markdown_page_count,
            api_key_type,
            api_provider,
            status,
            1 if approved else 0,
            token_usage,
            output_path,
            source,
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_test_cases(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM TEST_CASES ORDER BY case_id").fetchall()
    return [dict(r) for r in rows]


def list_error_codes(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT * FROM ERROR_CODES
         ORDER BY CASE error_category WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END,
                  error_code
        """
    ).fetchall()
    return [dict(r) for r in rows]


def latest_test_run(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("SELECT * FROM TEST_RUNS ORDER BY run_id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def results_for_run(conn: sqlite3.Connection, run_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT r.*, c.title, c.description, c.category, c.source_file
          FROM TEST_RESULTS r
          LEFT JOIN TEST_CASES c ON c.case_id = r.case_id
         WHERE r.run_id = ?
         ORDER BY r.id
        """,
        (run_id,),
    ).fetchall()
    return [dict(x) for x in rows]


def list_process_runs(conn: sqlite3.Connection, *, day: str | None = None, limit: int = 200) -> list[dict]:
    if day:
        rows = conn.execute(
            "SELECT * FROM PROCESS_RUNS WHERE run_day = ? ORDER BY id DESC LIMIT ?",
            (day, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM PROCESS_RUNS ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def list_test_runs(conn: sqlite3.Connection, *, limit: int = 20) -> list[dict]:
    rows = conn.execute("SELECT * FROM TEST_RUNS ORDER BY run_id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def _esc(text: Any) -> str:
    import html
    return html.escape(str(text or ""), quote=True)


def write_error_catalog(conn: sqlite3.Connection, dest_dir: Path) -> tuple[Path, Path]:
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    md_path = resolve_generated_path(dest_dir, "Error", "Code", "Catalog", "md")
    html_path = md_path.with_suffix(".html")
    rows = list_error_codes(conn)
    lines = [
        header_markdown(),
        "# Error Code Catalog",
        "",
        "Satyagraha Law Group — SLIP PDF to Markdown Ingestion Tool.",
        "Classified errors. New features register a code here before they ship.",
        "",
        f"- written_at: {iso_calcutta()}",
        f"- codes: {len(rows)}",
        "",
        "| Error code | Type | Category | Error message | Suggested resolution |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        msg = (row.get("error_message") or "").replace("|", "/")
        fix = (row.get("suggested_resolution") or "").replace("|", "/")
        lines.append(
            f"| `{row.get('error_code')}` | {row.get('error_type')} | "
            f"**{row.get('error_category')}** | {msg} | {fix} |"
        )
    lines.append(footer_markdown())
    md_path.write_text(with_single_footer("\n".join(lines)), encoding="utf-8")
    body_rows = []
    for row in rows:
        cat = row.get("error_category") or ""
        color = "#8B0000" if cat == "HIGH" else ("#8B4513" if cat == "MEDIUM" else "#000000")
        body_rows.append(
            "<tr>"
            f"<td><code>{_esc(row.get('error_code'))}</code></td>"
            f"<td>{_esc(row.get('error_type'))}</td>"
            f"<td style=\"color:{color};font-weight:bold\">{_esc(cat)}</td>"
            f"<td>{_esc(row.get('error_message'))}</td>"
            f"<td>{_esc(row.get('suggested_resolution'))}</td>"
            "</tr>"
        )
    body = (
        "<h1>Error Code Catalog</h1>"
        "<p>Satyagraha Law Group — SLIP PDF to Markdown Ingestion Tool. Classified errors. "
        "New features register a code here before they ship.</p>"
        f"<p>Written {_esc(iso_calcutta())}. Codes {len(rows)}.</p>"
        "<table><thead><tr><th>Error code</th><th>Type</th><th>Category</th>"
        "<th>Error message</th><th>Suggested resolution</th></tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody></table>"
    )
    html_path.write_text(html_wrap("Error Code Catalog", body), encoding="utf-8")
    return md_path, html_path


def write_test_reports(
    conn: sqlite3.Connection,
    dest_dir: Path,
    *,
    run_id: int | None = None,
) -> dict[str, Path]:
    """Detailed + summary reports generated FROM the catalog tables."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    run = None
    if run_id is not None:
        row = conn.execute("SELECT * FROM TEST_RUNS WHERE run_id = ?", (run_id,)).fetchone()
        run = dict(row) if row else None
    if run is None:
        run = latest_test_run(conn)
    cases = list_test_cases(conn)
    results = results_for_run(conn, int(run["run_id"])) if run else []
    by_id = {r.get("case_id"): r for r in results}
    merged = []
    for case in cases:
        rec = dict(case)
        hit = by_id.get(case["case_id"]) or {}
        rec["result"] = hit.get("result") or "NOT RUN"
        rec["duration_ms"] = hit.get("duration_ms")
        merged.append(rec)
    if not merged and results:
        merged = results

    process = list_process_runs(conn, day=(run or {}).get("run_day") or calcutta_day())
    history = list_test_runs(conn, limit=15)

    summary_md = resolve_generated_path(dest_dir, "Test", "Suite", "Summary", "md")
    detailed_md = resolve_generated_path(dest_dir, "Test", "Suite", "Detailed", "md")
    summary_html = summary_md.with_suffix(".html")
    detailed_html = detailed_md.with_suffix(".html")

    total = len(merged)
    passed = sum(1 for c in merged if c.get("result") == "PASS")
    failed = sum(1 for c in merged if c.get("result") == "FAIL")
    skipped = sum(1 for c in merged if c.get("result") == "SKIP")
    by_cat: dict[str, list] = {}
    for c in merged:
        by_cat.setdefault(c.get("category") or "functionality", []).append(c)

    def cat_table(lines: list[str]) -> None:
        lines += ["| Category | Count | Pass | Fail | Skip |", "| --- | --- | --- | --- | --- |"]
        for cat in PREFIX:
            group = by_cat.get(cat, [])
            if not group:
                continue
            lines.append(
                f"| {cat} | {len(group)} | "
                f"{sum(1 for x in group if x.get('result')=='PASS')} | "
                f"{sum(1 for x in group if x.get('result')=='FAIL')} | "
                f"{sum(1 for x in group if x.get('result')=='SKIP')} |"
            )

    s_lines = [
        header_markdown(),
        "# Test Suite Summary",
        "",
        "Satyagraha Law Group — SLIP PDF to Markdown Ingestion Tool.",
        "Generated from the TEST_CASES / TEST_RUNS catalog (source of truth).",
        "",
        f"- written_at: {iso_calcutta()}",
        f"- run_day: {(run or {}).get('run_day') or calcutta_day()}",
        f"- run_id: {(run or {}).get('run_id') or ''}",
        f"- total: {total}",
        f"- pass: {passed}",
        f"- fail: {failed}",
        f"- skip: {skipped}",
        f"- files_processed_this_day: {len(process)}",
        "",
        "## Totals by category",
        "",
    ]
    cat_table(s_lines)
    s_lines += [
        "",
        "## Recent test runs",
        "",
        "| run_id | day | total | pass | fail | skip |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for h in history:
        s_lines.append(
            f"| {h.get('run_id')} | {h.get('run_day')} | {h.get('total')} | "
            f"{h.get('passed')} | {h.get('failed')} | {h.get('skipped')} |"
        )
    s_lines.append(footer_markdown())
    summary_md.write_text(with_single_footer("\n".join(s_lines)), encoding="utf-8")

    d_lines = [
        header_markdown(),
        "# Test Suite Detailed",
        "",
        "Satyagraha Law Group — SLIP PDF to Markdown Ingestion Tool.",
        "Every test case in TEST_CASES, this run's result, and files processed this day.",
        "",
        f"- written_at: {iso_calcutta()}",
        f"- run_day: {(run or {}).get('run_day') or calcutta_day()}",
        f"- run_id: {(run or {}).get('run_id') or ''}",
        "",
        "## Test cases",
        "",
        "| Test Case Number | Function | Test Case Name | Description | Category | Result |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for c in merged:
        d_lines.append(
            f"| {c.get('case_id') or c.get('id')} | `{c.get('function_name') or ''}` | "
            f"{(c.get('title') or c.get('name') or '').replace('|', '/')} | "
            f"{(c.get('description') or '').replace('|', '/')} | "
            f"{c.get('category')} | {c.get('result')} |"
        )
    d_lines += [
        "",
        "## Files processed (this day)",
        "",
        "Authentic convert metrics: day, filename, PDF pages, markdown pages, API key type, approval status.",
        "",
        "| Day | File | PDF pages | Markdown pages | API key type | Status | Approved | SHA-256 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    if not process:
        d_lines.append("| (none this day) |  |  |  |  |  |  |  |")
    for p in process:
        sha = (p.get("sha256") or "")[:12]
        d_lines.append(
            f"| {p.get('run_day')} | `{p.get('filename')}` | {p.get('pdf_page_count') or ''} | "
            f"{p.get('markdown_page_count') or ''} | {p.get('api_key_type') or ''} | "
            f"{p.get('status') or ''} | {'yes' if p.get('approved') else 'no'} | `{sha}` |"
        )
    d_lines.append(footer_markdown())
    detailed_md.write_text(with_single_footer("\n".join(d_lines)), encoding="utf-8")

    def html_summary() -> str:
        cat_rows = []
        for cat in PREFIX:
            group = by_cat.get(cat, [])
            if not group:
                continue
            cat_rows.append(
                "<tr>"
                f"<td>{_esc(cat)}</td><td>{len(group)}</td>"
                f"<td>{sum(1 for x in group if x.get('result')=='PASS')}</td>"
                f"<td>{sum(1 for x in group if x.get('result')=='FAIL')}</td>"
                f"<td>{sum(1 for x in group if x.get('result')=='SKIP')}</td>"
                "</tr>"
            )
        hist = "".join(
            "<tr>"
            f"<td>{_esc(h.get('run_id'))}</td><td>{_esc(h.get('run_day'))}</td>"
            f"<td>{_esc(h.get('total'))}</td><td>{_esc(h.get('passed'))}</td>"
            f"<td>{_esc(h.get('failed'))}</td><td>{_esc(h.get('skipped'))}</td>"
            "</tr>"
            for h in history
        )
        return (
            "<h1>Test Suite Summary</h1>"
            "<p>Generated from the TEST_CASES / TEST_RUNS catalog (source of truth).</p>"
            f"<p>Written {_esc(iso_calcutta())}. Day {_esc((run or {}).get('run_day'))}. "
            f"Total {total}. Pass {passed}. Fail {failed}. Skip {skipped}. "
            f"Files processed this day {len(process)}.</p>"
            "<h2>Totals by category</h2>"
            "<table><thead><tr><th>Category</th><th>Count</th><th>Pass</th><th>Fail</th><th>Skip</th></tr></thead>"
            f"<tbody>{''.join(cat_rows)}</tbody></table>"
            "<h2>Recent test runs</h2>"
            "<table><thead><tr><th>run_id</th><th>day</th><th>total</th><th>pass</th><th>fail</th><th>skip</th></tr></thead>"
            f"<tbody>{hist}</tbody></table>"
        )

    def html_detailed() -> str:
        rows = []
        for c in merged:
            tone = "#006400" if c.get("result") == "PASS" else ("#8B0000" if c.get("result") == "FAIL" else "#000000")
            rows.append(
                "<tr>"
                f"<td>{_esc(c.get('case_id') or c.get('id'))}</td>"
                f"<td><code>{_esc(c.get('function_name'))}</code></td>"
                f"<td>{_esc(c.get('title') or c.get('name'))}</td>"
                f"<td>{_esc(c.get('description'))}</td>"
                f"<td>{_esc(c.get('category'))}</td>"
                f"<td style=\"color:{tone};font-weight:bold\">{_esc(c.get('result'))}</td>"
                "</tr>"
            )
        files = []
        for p in process:
            files.append(
                "<tr>"
                f"<td>{_esc(p.get('run_day'))}</td>"
                f"<td><code>{_esc(p.get('filename'))}</code></td>"
                f"<td>{_esc(p.get('pdf_page_count'))}</td>"
                f"<td>{_esc(p.get('markdown_page_count'))}</td>"
                f"<td>{_esc(p.get('api_key_type'))}</td>"
                f"<td>{_esc(p.get('status'))}</td>"
                f"<td>{'yes' if p.get('approved') else 'no'}</td>"
                f"<td><code>{_esc((p.get('sha256') or '')[:12])}</code></td>"
                "</tr>"
            )
        if not files:
            files.append("<tr><td colspan=\"8\">(none this day)</td></tr>")
        return (
            "<h1>Test Suite Detailed</h1>"
            "<p>Every test case in TEST_CASES, this run's result, and files processed this day.</p>"
            "<h2>Test cases</h2>"
            "<table><thead><tr><th>Test Case Number</th><th>Function</th><th>Name</th>"
            "<th>Description</th><th>Category</th><th>Result</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            "<h2>Files processed (this day)</h2>"
            "<table><thead><tr><th>Day</th><th>File</th><th>PDF pages</th><th>Markdown pages</th>"
            "<th>API key type</th><th>Status</th><th>Approved</th><th>SHA-256</th></tr></thead>"
            f"<tbody>{''.join(files)}</tbody></table>"
        )

    summary_html.write_text(html_wrap("Test Suite Summary", html_summary()), encoding="utf-8")
    detailed_html.write_text(html_wrap("Test Suite Detailed", html_detailed()), encoding="utf-8")
    if run:
        conn.execute(
            "UPDATE TEST_RUNS SET report_summary_path = ?, report_detailed_path = ? WHERE run_id = ?",
            (str(summary_md), str(detailed_md), run["run_id"]),
        )
        conn.commit()
    return {
        "summary_md": summary_md,
        "summary_html": summary_html,
        "detailed_md": detailed_md,
        "detailed_html": detailed_html,
    }



def write_tool_practice(dest_dir: Path) -> Path:
    """Living best-practice note for every future Satyagraha tool."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = resolve_generated_path(dest_dir, "Tool", "Build", "Practice", "md")
    body = "\n".join(
        [
            header_markdown(),
            "# Tool Build Practice",
            "",
            "Best practices learned while building the SLIP PDF to Markdown Ingestion Tool. Apply these to every new Satyagraha Law Group tool.",
            "",
            "1. **One sqlite book.** Identity, GUBERNATIO, TEST_CASES, TEST_RUNS, PROCESS_RUNS, and ERROR_CODES live together and share the sibling `.bak`.",
            "2. **Tests upsert the catalog first.** A new test case is a row in TEST_CASES (`TC-XXX-NNN` stays stable). Reports are generated from the tables, not from a disposable pytest dump.",
            "3. **Two reports every run.** Test-Suite-Summary (totals, recent runs) and Test-Suite-Detailed (every case plus files processed that day).",
            "4. **Process metrics on every convert.** Day, filename, PDF pages, markdown pages, API key type (`local_tesseract` or provider), status, approved yes/no.",
            "5. **Error codes before features ship.** `SLIP-E-NNN`, type, HIGH/MEDIUM/LOW, message, suggested resolution. Publish Error-Code-Catalog markdown and HTML.",
            "6. **Satyagraha header and footer** on every doc and report (Rig Veda, Aristotle, research disclaimer, site index / Calendly / channels).",
            "7. **Wiki graph.** Related files use Obsidian `[[Name]]` plus relative hrefs so HTML readers can click through.",
            "8. **Three-word names.** `Word1-Word2-Word3-vN-DD-MM-YYYY-HH-MI-SS`. Living files keep the first-created stamp.",
            "9. **Never store raw API keys.** Fingerprint plus provider only. Sentinel lease for remote APIs.",
            "10. **Memory.** Update Tool-Creation-Memory (global) and Session-Learning-Notes (session) in place after each slice. Git only after Anil approves.",
            "11. **Engine choice.** Before convert (including `--force`), ask 1 Local Tesseract or 2 Mistral AI. Do not pick `--engine` yourself.",
            "",
            footer_markdown(),
        ]
    )
    path.write_text(with_single_footer(body), encoding="utf-8")
    html_path = path.with_suffix(".html")
    html_path.write_text(
        html_wrap(
            "Tool Build Practice",
            "<h1>Tool Build Practice</h1>"
            "<p>Best practices learned while building the SLIP PDF to Markdown Ingestion Tool. Apply these to every new Satyagraha Law Group tool.</p>"
            "<ol>"
            "<li>One sqlite book for identity, GUBERNATIO, tests, process runs, and error codes.</li>"
            "<li>Tests upsert TEST_CASES first. Reports come from the tables.</li>"
            "<li>Summary and detailed test reports on every run.</li>"
            "<li>Convert records day, file, PDF pages, markdown pages, API key type, approval.</li>"
            "<li>New features register ERROR_CODES and republish the catalog.</li>"
            "<li>Satyagraha header and footer on every document.</li>"
            "<li>Obsidian wiki links plus HTML hrefs.</li>"
            "<li>Three-word filenames. Living stamps stay first-created.</li>"
            "<li>Never store raw API keys.</li>"
            "<li>Update Tool-Creation-Memory and Session-Learning-Notes after each slice.</li>"
            "<li>Always ask Local Tesseract vs Mistral AI before convert.</li>"
            "</ol>",
        ),
        encoding="utf-8",
    )
    return path
