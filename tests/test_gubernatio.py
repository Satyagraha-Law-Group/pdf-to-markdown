from pathlib import Path

from slip_pdf_md.convert import convert_pdf
from slip_pdf_md.registry import STATUS_DONE, Registry


def test_gubernatio_table_exists_and_records_filename(tmp_path):
    db = tmp_path / "registry.sqlite"
    pdf = tmp_path / "opinion.pdf"
    pdf.write_bytes(b"%PDF gubernatio-bytes\n")
    reg = Registry(db)
    names = {row[0] for row in reg.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "GUBERNATIO" in names
    row = reg.see(pdf, routed_to="10_02_READY_FOR_DOCLING")
    sha = row["sha256"]
    reg.set_status(sha, STATUS_DONE, engine="pymupdf", page_count=2, output_path=str(tmp_path / "opinion.md"))
    rows = reg.gubernatio_rows(sha)
    assert len(rows) >= 2
    assert any(r["filename"] == "opinion.pdf" for r in rows)
    assert any(r["step"] == "status_DONE" for r in rows)
    assert any(r["status"] == STATUS_DONE for r in rows)
    assert all(r.get("agent") for r in rows)
    assert all(r.get("host") for r in rows)
    assert reg.count_documents() == 1
    assert reg.count_gubernatio(sha) >= 2
    health = reg.health()
    assert health["gubernatio"] >= 2
    reg.close()


def test_gubernatio_keeps_documents_lean_on_duplicate_filename(tmp_path):
    db = tmp_path / "registry.sqlite"
    a = tmp_path / "first.pdf"
    b = tmp_path / "renamed-later.pdf"
    a.write_bytes(b"%PDF same-gubernatio\n")
    b.write_bytes(a.read_bytes())
    reg = Registry(db)
    one = reg.see(a, routed_to="10_02_READY_FOR_DOCLING")
    sha = one["sha256"]
    reg.set_status(sha, STATUS_DONE, engine="mistral", page_count=56)
    two = reg.see(b, routed_to="50_90_DUPLICATES")
    assert two["sha256"] == sha
    assert reg.count_documents() == 1
    files = {r["filename"] for r in reg.gubernatio_rows(sha)}
    assert "first.pdf" in files
    assert "renamed-later.pdf" in files
    assert reg.count_gubernatio(sha) >= 3
    reg.close()


def test_convert_writes_gubernatio_on_done_and_duplicate(slip_tree):
    import fitz

    def text_pdf(path: Path, text: str) -> Path:
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), text)
        doc.save(path)
        doc.close()
        return path

    pdf = text_pdf(slip_tree.raw / "notice.pdf", "Satyagraha Law Group hears the petition.")
    reg = Registry(slip_tree.registry_path)
    one = convert_pdf(pdf, slip_tree, reg, move_raw=True)
    assert one["status"] == "AWAITING_APPROVAL"
    sha = one["sha256"]
    assert reg.count_gubernatio(sha) >= 2
    processed = next(slip_tree.processed.rglob("notice.pdf"))
    twin = slip_tree.raw / "notice-copy.pdf"
    twin.write_bytes(processed.read_bytes())
    two = convert_pdf(twin, slip_tree, reg, move_raw=True)
    assert two["duplicate"] is True
    files = {r["filename"] for r in reg.gubernatio_rows(sha)}
    assert "notice.pdf" in files
    assert "notice-copy.pdf" in files
    assert reg.count_documents() == 1
    reg.close()


def test_backfill_gubernatio_from_legacy_sightings(tmp_path):
    import sqlite3

    from slip_pdf_md.registry import SCHEMA

    db = tmp_path / "legacy.sqlite"
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA)
    conn.execute(
        "INSERT INTO documents (sha256, original_filename, source_path, status, first_seen_at) "
        "VALUES (?, ?, ?, ?, ?)",
        ("ab" * 32, "old.pdf", "old.pdf", "DONE", "2026-09-03T05:00:00+05:30"),
    )
    conn.execute(
        "INSERT INTO sightings (sha256, filename, seen_at, routed_to) VALUES (?, ?, ?, ?)",
        ("ab" * 32, "old.pdf", "2026-09-03T05:00:00+05:30", "60_90_PROCESSED"),
    )
    conn.commit()
    conn.close()
    reg = Registry(db)
    assert reg.count_gubernatio() >= 1
    rows = reg.gubernatio_rows("ab" * 32)
    assert any(r["filename"] == "old.pdf" for r in rows)
    assert any(r["step"] == "backfill_sighting" for r in rows)
    reg.close()
