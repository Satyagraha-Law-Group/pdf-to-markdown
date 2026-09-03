from pathlib import Path

import fitz

from slip_pdf_md.catalog import (
    list_error_codes,
    list_process_runs,
    list_test_cases,
    write_error_catalog,
    write_test_reports,
)
from slip_pdf_md.convert import convert_pdf
from slip_pdf_md.registry import Registry


def _text_pdf(path: Path, text: str) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


def test_error_codes_are_seeded_and_classified(tmp_path):
    reg = Registry(tmp_path / "reg.sqlite")
    rows = list_error_codes(reg.conn)
    reg.close()
    assert rows, "ERROR_CODES must be seeded"
    cats = {r["error_category"] for r in rows}
    assert {"HIGH", "MEDIUM", "LOW"} <= cats
    assert any(r["error_code"] == "SLIP-E-004" for r in rows)
    assert all(r.get("suggested_resolution") for r in rows)


def test_register_error_upserts_and_publishes(tmp_path):
    reg = Registry(tmp_path / "reg.sqlite")
    reg.register_error(
        error_code="SLIP-E-099",
        error_type="catalog",
        error_category="LOW",
        error_message="Example code for a new feature.",
        suggested_resolution="Keep registering codes when a feature ships.",
        source_module="test",
    )
    md, html = write_error_catalog(reg.conn, tmp_path / "docs")
    text = md.read_text(encoding="utf-8")
    html_text = html.read_text(encoding="utf-8")
    reg.close()
    assert "SLIP-E-099" in text
    assert "Founded by Anil B. (Lawyer)" in text
    assert "SLIP-E-099" in html_text
    assert "background:#ffffff" in html_text


def test_test_case_upsert_keeps_stable_id(tmp_path):
    reg = Registry(tmp_path / "reg.sqlite")
    a = reg.upsert_test_case(
        function_name="test_alpha",
        source_file="test_alpha.py",
        category="unit",
        title="Alpha",
        description="First.",
    )
    b = reg.upsert_test_case(
        function_name="test_alpha",
        source_file="test_alpha.py",
        category="unit",
        title="Alpha refreshed",
        description="Still first.",
    )
    c = reg.upsert_test_case(
        function_name="test_beta",
        source_file="test_beta.py",
        category="unit",
        title="Beta",
        description="Second.",
    )
    cases = list_test_cases(reg.conn)
    reg.close()
    assert a == b == "TC-UNT-001"
    assert c == "TC-UNT-002"
    assert cases[0]["title"] == "Alpha refreshed"


def test_convert_writes_process_run_metrics(slip_tree):
    pdf = _text_pdf(slip_tree.raw / "metrics.pdf", "Catalog metrics for this file.")
    reg = Registry(slip_tree.registry_path)
    result = convert_pdf(pdf, slip_tree, reg, move_raw=True)
    rows = list_process_runs(reg.conn)
    reg.close()
    assert result["status"] == "AWAITING_APPROVAL"
    assert rows, "PROCESS_RUNS must record the convert"
    row = rows[0]
    assert row["filename"] == "metrics.pdf"
    assert int(row["pdf_page_count"] or 0) == 1
    assert int(row["markdown_page_count"] or 0) >= 1
    assert row["api_key_type"] == "local_tesseract"
    assert row["status"] == "AWAITING_APPROVAL"
    assert int(row["approved"] or 0) == 0
    assert row["run_day"]


def test_reports_generate_from_catalog_tables(tmp_path):
    from slip_pdf_md.catalog import finish_test_run, start_test_run

    reg = Registry(tmp_path / "reg.sqlite")
    case_id = reg.upsert_test_case(
        function_name="test_reports_generate_from_catalog_tables",
        source_file="test_catalog.py",
        category="integrity",
        title="Reports come from the catalog",
        description="Detailed and summary reports are generated from TEST_CASES.",
    )
    run_id = start_test_run(reg.conn)
    finish_test_run(
        reg.conn,
        run_id,
        results=[{"id": case_id, "function_name": "test_reports_generate_from_catalog_tables", "result": "PASS"}],
    )
    dest = tmp_path / "docs"
    out = write_test_reports(reg.conn, dest, run_id=run_id)
    summary = out["summary_md"].read_text(encoding="utf-8")
    detailed = out["detailed_md"].read_text(encoding="utf-8")
    reg.close()
    assert "Test Suite Summary" in summary
    assert "Founded by Anil B. (Lawyer)" in summary
    assert case_id in detailed
    assert "Files processed" in detailed
    assert out["summary_html"].is_file()
    assert out["detailed_html"].is_file()
