from pathlib import Path

from slip_pdf_md.naming import (
    REPORT_NAME_RE,
    resolve_generated_path,
    three_word_filename,
)


def test_three_word_filename_matches_convention():
    name = three_word_filename("Document", "Hash", "Registry", ext="sqlite")
    assert REPORT_NAME_RE.match(name)
    assert name.startswith("Document-Hash-Registry-v1-")
    assert name.endswith(".sqlite")


def test_resolve_migrates_legacy_registry(tmp_path: Path):
    folder = tmp_path / "pdf-to-markdown"
    folder.mkdir()
    legacy = folder / "registry.sqlite"
    legacy.write_bytes(b"sqlite-bytes")
    live = resolve_generated_path(
        folder, "Document", "Hash", "Registry", "sqlite", legacy_names=("registry.sqlite",)
    )
    assert not legacy.exists()
    assert live.exists()
    assert REPORT_NAME_RE.match(live.name)
    assert live.read_bytes() == b"sqlite-bytes"
    again = resolve_generated_path(
        folder, "Document", "Hash", "Registry", "sqlite", legacy_names=("registry.sqlite",)
    )
    assert again == live
