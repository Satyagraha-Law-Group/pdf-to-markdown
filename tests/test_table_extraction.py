from pathlib import Path

from convert_pdfs import extract_markdown_from_pdf

BASE_PATH = Path(
    r"C:\Users\SATYAGRAHA\Downloads\SHAM-01-960-SARKAR PC MAJOR ACTS 27-08-2026 17-07-50 A-4-split (1)"
)
PAGE_108 = BASE_PATH / "SHAM-01-960-SARKAR PC MAJOR ACTS 27-08-2026 17-07-50 A-4-00108.pdf"
PAGE_085 = BASE_PATH / "SHAM-01-960-SARKAR PC MAJOR ACTS 27-08-2026 17-07-50 A-4-00085.pdf"


def test_table_sections_are_rendered_as_markdown_tables():
    content = extract_markdown_from_pdf(PAGE_108)
    assert "|" in content, "expected Markdown table separators in extracted output"
    assert "Section" in content or "376" in content
    assert "Public servant" in content


def test_scanned_table_pages_are_reconstructed_as_markdown_tables():
    content = extract_markdown_from_pdf(PAGE_085)
    assert "|" in content, "expected the scanned legal table to be reconstructed as Markdown"
    assert "CLASSIFICATION" in content or "Section" in content or "Offence" in content

    table_lines = [line for line in content.splitlines() if "|" in line]
    assert len(table_lines) >= 2, "expected multiple table rows for the legal table page"
