from pathlib import Path

import fitz

from slip_pdf_md.convert import convert_pdf
from slip_pdf_md.registry import Registry


def _text_pdf(path: Path, text: str) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


def test_text_layer_fixture_pdf(slip_tree):
    pdf = _text_pdf(slip_tree.raw / "notice.pdf", "Satyagraha Law Group hears the petition.")
    reg = Registry(slip_tree.registry_path)
    result = convert_pdf(pdf, slip_tree, reg, move_raw=True)
    reg.close()
    assert result["status"] == "AWAITING_APPROVAL"
    assert result["duplicate"] is False
    out = Path(result["output"])
    text = out.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "document_type: legal_pdf" in text
    assert "source_file: notice.pdf" in text
    assert "source_sha256:" in text
    assert "processing_status: AWAITING_APPROVAL" in text
    assert "engine:" in text
    assert "page_count: 1" in text
    assert "converted_at:" in text
    assert "token_usage:" in text
    assert "## Page 1" in text
    assert "Satyagraha Law Group hears the petition." in text


def test_retries_do_not_double_convert_done_hash(slip_tree):
    first = _text_pdf(slip_tree.raw / "brief.pdf", "Unique body text 7711.")
    reg = Registry(slip_tree.registry_path)
    one = convert_pdf(first, slip_tree, reg, move_raw=True)
    assert one["status"] == "AWAITING_APPROVAL"
    twin = slip_tree.raw / "brief-copy.pdf"
    # original was moved to processed; copy bytes under a new name into RAW
    processed = next(slip_tree.processed.rglob("brief.pdf"))
    twin.write_bytes(processed.read_bytes())
    two = convert_pdf(twin, slip_tree, reg, move_raw=True)
    reg.close()
    assert two["duplicate"] is True
    assert two["status"] == "AWAITING_APPROVAL"
    mds = list(slip_tree.clean.glob("*.md"))
    assert len(mds) == 1
    sidecars = list(slip_tree.duplicates.rglob("*.sidecar.md"))
    assert len(sidecars) == 1
