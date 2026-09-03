from pathlib import Path

import fitz

from slip_pdf_md.convert import convert_pdf
from slip_pdf_md.registry import Registry
from slip_pdf_md.runlog import parse_token_usage


def _text_pdf(path: Path, text: str) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


def test_convert_writes_token_usage_column(slip_tree):
    pdf = _text_pdf(slip_tree.raw / "usage.pdf", "Token usage belongs on this convert.")
    reg = Registry(slip_tree.registry_path)
    result = convert_pdf(pdf, slip_tree, reg, move_raw=True)
    sha = result["sha256"]
    identity = reg.get(sha)
    gub = [row for row in reg.gubernatio_rows(sha) if row.get("step") == "status_AWAITING_APPROVAL"]
    reg.close()
    assert result["status"] == "AWAITING_APPROVAL"
    usage = parse_token_usage(result.get("token_usage") or identity.get("token_usage"))
    assert usage.get("markdown_tokens_estimate", 0) >= 1
    assert usage.get("llm_total_tokens") == 0
    assert usage.get("equivalent_internal_total_tokens", 0) >= 1105
    assert identity["token_usage"]
    ident_usage = parse_token_usage(identity["token_usage"])
    assert ident_usage.get("markdown_tokens_estimate") == usage.get("markdown_tokens_estimate")
    assert gub, "GUBERNATIO missing convert row"
    assert parse_token_usage(gub[0]["token_usage"]).get("markdown_tokens_estimate") >= 1
    md = Path(result["output"]).read_text(encoding="utf-8")
    assert "token_usage:" in md
    assert "markdown_tokens_estimate" in md


def test_registry_alters_token_usage_on_existing_db(tmp_path):
    import sqlite3
    db = tmp_path / "old.sqlite"
    conn = sqlite3.connect(str(db))
    conn.executescript(
        """
        CREATE TABLE documents (sha256 TEXT PRIMARY KEY, original_filename TEXT, source_path TEXT,
            status TEXT, engine TEXT, page_count INTEGER, output_path TEXT,
            first_seen_at TEXT, converted_at TEXT, last_error TEXT);
        CREATE TABLE sightings (id INTEGER PRIMARY KEY, sha256 TEXT, filename TEXT, seen_at TEXT, routed_to TEXT);
        CREATE TABLE "GUBERNATIO" (id INTEGER PRIMARY KEY, sha256 TEXT, filename TEXT, source_path TEXT,
            status TEXT, engine TEXT, page_count INTEGER, output_path TEXT, routed_to TEXT,
            first_seen_at TEXT, converted_at TEXT, last_error TEXT, seen_at TEXT,
            host TEXT, agent TEXT, step TEXT);
        """
    )
    conn.commit()
    conn.close()
    from slip_pdf_md.registry import Registry
    reg = Registry(db, restore_if_missing=False)
    docs_cols = {row[1] for row in reg.conn.execute("PRAGMA table_info(documents)")}
    gub_cols = {row[1] for row in reg.conn.execute('PRAGMA table_info("GUBERNATIO")')}
    reg.close()
    assert "token_usage" in docs_cols
    assert "token_usage" in gub_cols
