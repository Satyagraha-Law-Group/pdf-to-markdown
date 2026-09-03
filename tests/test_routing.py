from pathlib import Path

import fitz

from slip_pdf_md.auditcontrol import SessionAudit, collect_sequential_pdfs
from slip_pdf_md.convert import convert_pdf
from slip_pdf_md.naming import REPORT_NAME_RE
from slip_pdf_md.registry import Registry


def _text_pdf(path: Path, text: str) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


def test_new_file_moves_raw_to_ready_then_processed(slip_tree):
    pdf = _text_pdf(slip_tree.raw / "notice.pdf", "Satyagraha Law Group hears the petition.")
    audit = SessionAudit(slip_tree, engine="pymupdf")
    reg = Registry(slip_tree.registry_path)
    result = convert_pdf(pdf, slip_tree, reg, move_raw=True, audit=audit)
    audit.close()
    reg.close()
    assert result["status"] == "AWAITING_APPROVAL"
    assert not pdf.exists()
    assert list(slip_tree.raw.rglob("*.pdf")) == []
    processed = list(slip_tree.processed.rglob("notice.pdf"))
    assert len(processed) == 1
    assert processed[0].parent.name == "notice"
    assert processed[0].parent.parent.name.count("-") == 2  # YYYY-MM-DD
    assert list(slip_tree.ready.rglob("*.pdf")) == []
    text = audit.path.read_text(encoding="utf-8")
    assert REPORT_NAME_RE.match(audit.path.name)
    assert "moved_to_ready" in text
    assert "moved_to_processed" in text
    assert "hashed" in text


def test_duplicate_goes_to_dated_duplicates_not_processed(slip_tree):
    first = _text_pdf(slip_tree.raw / "brief.pdf", "Unique body text 7711.")
    reg = Registry(slip_tree.registry_path)
    one = convert_pdf(first, slip_tree, reg, move_raw=True)
    assert one["status"] == "AWAITING_APPROVAL"
    processed = next(slip_tree.processed.rglob("brief.pdf"))
    twin = slip_tree.raw / "brief-copy.pdf"
    twin.write_bytes(processed.read_bytes())
    two = convert_pdf(twin, slip_tree, reg, move_raw=True)
    reg.close()
    assert two["duplicate"] is True
    assert not twin.exists()
    dups = list(slip_tree.duplicates.rglob("brief-copy.pdf"))
    assert len(dups) == 1
    assert dups[0].parent.name.count("-") == 2
    assert list(slip_tree.processed.rglob("brief-copy.pdf")) == []
    sidecars = list(slip_tree.duplicates.rglob("*.sidecar.md"))
    assert len(sidecars) == 1


def test_collect_ready_leftovers_before_raw(slip_tree):
    day = slip_tree.bucket(slip_tree.ready)
    _text_pdf(day / "leftover.pdf", "Leftover ready queue.")
    _text_pdf(slip_tree.raw / "newer.pdf", "Newer raw drop.")
    ordered = collect_sequential_pdfs(slip_tree)
    names = [p.name for p in ordered]
    assert names[0] == "leftover.pdf"
    assert "newer.pdf" in names


def test_collect_skips_split_parts(slip_tree):
    day = slip_tree.bucket(slip_tree.ready)
    home = day / "Big-Scan"
    parts = home / "parts"
    parts.mkdir(parents=True)
    _text_pdf(home / "Big-Scan.pdf", "Original whole file.")
    _text_pdf(parts / "Big-Scan-part-01-of-02.pdf", "Part one.")
    ordered = collect_sequential_pdfs(slip_tree)
    names = [p.name for p in ordered]
    assert "Big-Scan.pdf" in names
    assert "Big-Scan-part-01-of-02.pdf" not in names
