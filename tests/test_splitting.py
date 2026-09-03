from pathlib import Path

import fitz

from slip_pdf_md.auditcontrol import SessionAudit
from slip_pdf_md.convert import convert_pdf
from slip_pdf_md.registry import Registry
from slip_pdf_md.splitting import (
    merge_markdown_parts,
    needs_split,
    pdf_page_count,
    reindex_pages,
    split_pdf,
    stem_folder_name,
)


def _n_page_pdf(path: Path, n: int, prefix: str = "PAGE") -> Path:
    doc = fitz.open()
    for i in range(1, n + 1):
        page = doc.new_page()
        page.insert_text((72, 72), f"{prefix} {i}")
    doc.save(path)
    doc.close()
    return path


def test_stem_folder_name_strips_extension():
    assert stem_folder_name("Arbitration Act.pdf") == "Arbitration Act"


def test_five_page_file_splits_into_three_parts(tmp_path):
    src = _n_page_pdf(tmp_path / "Long-Brief.pdf", 5)
    parts = split_pdf(src, tmp_path / "parts", max_pages=2, max_bytes=10**12)
    assert src.exists()
    assert [p.name for p in parts] == [
        "Long-Brief-part-01-of-03.pdf",
        "Long-Brief-part-02-of-03.pdf",
        "Long-Brief-part-03-of-03.pdf",
    ]
    assert [pdf_page_count(p) for p in parts] == [2, 2, 1]
    assert all(p.stat().st_size > 0 for p in parts)


def test_needs_split_page_and_size_caps(tmp_path):
    src = _n_page_pdf(tmp_path / "small.pdf", 3)
    assert needs_split(src, max_pages=2, max_bytes=10**12) is True
    assert needs_split(src, max_pages=10, max_bytes=10**12) is False
    tiny = src.stat().st_size - 1
    assert needs_split(src, max_pages=10, max_bytes=tiny) is True


def test_reindex_and_merge_markdown_parts():
    one = "---\npage_count: 2\n---\n\n## Page 1\n\nA\n\n## Page 2\n\nB\n"
    two = "---\npage_count: 1\n---\n\n## Page 1\n\nC\n"
    assert reindex_pages("## Page 1\n\nC\n", 2) == "## Page 3\n\nC\n"
    template = "---\nsource_file: x.pdf\npage_count: 0\n---\n\n"
    merged = merge_markdown_parts([one, two], total_pages=3, template=template)
    assert "page_count: 3" in merged
    assert "## Page 1" in merged
    assert "## Page 2" in merged
    assert "## Page 3" in merged
    assert merged.count("## Page 1") == 1


def test_happy_path_split_convert_merges_and_deletes_parts(slip_tree, monkeypatch):
    import slip_pdf_md.convert as convert_mod

    monkeypatch.setattr(convert_mod, "MAX_PAGES_PER_PART", 2)
    monkeypatch.setattr(convert_mod, "MAX_BYTES_PER_PART", 10**12)
    pdf = _n_page_pdf(slip_tree.raw / "Long-Opinion.pdf", 5, prefix="TOKEN")
    audit = SessionAudit(slip_tree, engine="pymupdf")
    reg = Registry(slip_tree.registry_path)
    result = convert_pdf(pdf, slip_tree, reg, move_raw=True, audit=audit)
    audit.close()
    reg.close()
    assert result["status"] == "AWAITING_APPROVAL"
    assert result["page_count"] == 5
    assert not pdf.exists()
    md = Path(result["output"]).read_text(encoding="utf-8")
    assert "page_count: 5" in md
    for i in range(1, 6):
        assert f"## Page {i}" in md
        assert f"TOKEN {i}" in md
    processed = list(slip_tree.processed.rglob("Long-Opinion.pdf"))
    assert len(processed) == 1
    assert processed[0].parent.name == "Long-Opinion"
    assert list(slip_tree.ready.rglob("*.pdf")) == []
    assert list(slip_tree.raw.rglob("*.pdf")) == []
    parts = list(slip_tree.ready.rglob("parts")) + list(slip_tree.processed.rglob("parts"))
    assert parts == []
    text = audit.path.read_text(encoding="utf-8")
    assert "split" in text
    assert "deleted_parts" in text
    assert "moved_to_processed" in text
