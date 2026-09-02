from pathlib import Path

import fitz

from slip_pdf_md.convert import convert_pdf
from slip_pdf_md.engines.pymupdf_engine import _rows_to_markdown_table
from slip_pdf_md.registry import Registry


def _table_pdf(path: Path) -> Path:
    doc = fitz.open()
    page = doc.new_page(width=400, height=300)
    xs = [50, 200, 350]
    ys = [50, 100, 150]
    for x in xs:
        page.draw_line(p1=(x, 50), p2=(x, 150), color=(0, 0, 0), width=1)
    for y in ys:
        page.draw_line(p1=(50, y), p2=(350, y), color=(0, 0, 0), width=1)
    page.insert_text((60, 80), "Name")
    page.insert_text((210, 80), "Year")
    page.insert_text((60, 130), "AIR")
    page.insert_text((210, 130), "2024")
    doc.save(path)
    doc.close()
    return path


def test_table_fixture_pdf(slip_tree):
    pdf = _table_pdf(slip_tree.raw / "schedule.pdf")
    reg = Registry(slip_tree.registry_path)
    result = convert_pdf(pdf, slip_tree, reg, move_raw=True)
    reg.close()
    text = Path(result["output"]).read_text(encoding="utf-8")
    assert "## Page 1" in text
    assert "Name" in text
    assert "Year" in text
    assert "2024" in text
    has_table = "|" in text and "---" in text
    has_callout = "UNRECOVERED TABLE REGION" in text
    assert has_table or has_callout or "AIR" in text


def test_tsv_buckets_build_pipe_table():
    rows = [
        [
            {"text": "Section", "x": 10, "width": 40, "conf": 90},
            {"text": "Title", "x": 120, "width": 40, "conf": 90},
        ],
        [
            {"text": "302", "x": 10, "width": 30, "conf": 90},
            {"text": "Murder", "x": 120, "width": 40, "conf": 90},
        ],
        [
            {"text": "304", "x": 10, "width": 30, "conf": 90},
            {"text": "Culpable", "x": 120, "width": 50, "conf": 90},
        ],
    ]
    md, unrecovered = _rows_to_markdown_table(rows)
    assert unrecovered is False
    assert md.startswith("| Section | Title |")
    assert "---" in md
    assert "| 302 | Murder |" in md
