from pathlib import Path

from slip_pdf_md.naming import REPORT_NAME_RE
from slip_pdf_md.paths import SlipPaths
from slip_pdf_md.registry import (
    STATUS_DONE,
    Registry,
    backup_path,
    format_duplicate_notice,
)
from slip_pdf_md.registry_rebuild import rebuild_from_vault


def _slip(tmp_path: Path) -> SlipPaths:
    root = tmp_path / "SLIP_DOCUMENT_PROCESSING"
    paths = SlipPaths(root)
    for folder in paths.all_dirs():
        folder.mkdir(parents=True, exist_ok=True)
    return paths


def test_backup_created_and_restores_after_delete(tmp_path: Path):
    db = tmp_path / "registry.sqlite"
    pdf = tmp_path / "opinion.pdf"
    pdf.write_bytes(b"%PDF same-bytes\n")
    reg = Registry(db)
    row = reg.see(pdf, routed_to="10_02_READY_FOR_DOCLING")
    sha = row["sha256"]
    reg.set_status(sha, STATUS_DONE, output_path=str(tmp_path / "opinion.md"), engine="mistral", page_count=56)
    bak = backup_path(db)
    assert bak.exists()
    notices = list(db.parent.glob("Registry-Safety-Notice-v*.txt"))
    assert notices
    assert REPORT_NAME_RE.match(notices[0].name)
    reg.close()
    db.unlink()
    assert not db.exists()
    restored = Registry(db)
    assert restored.restored_from_backup is True
    hit = restored.get(sha)
    assert hit is not None
    assert hit["original_filename"] == "opinion.pdf"
    assert hit["status"] == STATUS_DONE
    restored.close()


def test_duplicate_notice_names_first_file():
    text = format_duplicate_notice(
        {
            "sha256": "abc123",
            "original_filename": "Scan-March.pdf",
            "first_seen_at": "2026-03-01T09:00:00+05:30",
            "converted_at": "2026-03-01T09:02:00+05:30",
            "engine": "mistral",
            "page_count": 56,
            "output_path": "clean.md",
        },
        inbound_name="Scan-September.pdf",
        sidecar="dup.sidecar.md",
        sightings=4,
    )
    assert "Scan-March.pdf" in text
    assert "Scan-September.pdf" in text
    assert "[DUP]" in text
    assert "filename is not identity" in text
    assert "sightings_including_this: 4" in text


def test_rebuild_from_markdown_front_matter(tmp_path: Path):
    paths = _slip(tmp_path)
    md = paths.clean / "Scan.md"
    md.write_text(
        "---\ndocument_type: legal_pdf\nsource_file: Scan.pdf\n"
        "source_sha256: deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef\n"
        "processing_status: DONE\nengine: mistral\npage_count: 3\nconverted_at: 2026-09-03\n---\n\n## Page 1\n\nhello\n",
        encoding="utf-8",
    )
    result = rebuild_from_vault(paths)
    assert result["documents"] >= 1
    reg = Registry(paths.registry_path)
    row = reg.get("deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef")
    assert row is not None
    assert row["status"] == "DONE"
    assert row["original_filename"] == "Scan.pdf"
    reg.close()
