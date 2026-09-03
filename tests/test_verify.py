from pathlib import Path

from slip_pdf_md.verify import verify_markdown


def test_verify_synthetic_markdown(tmp_path: Path):
    md = tmp_path / "Sample.md"
    md.write_text(
        "---\ndocument_type: legal_pdf\nsource_sha256: abc\nprocessing_status: DONE\n---\n\n"
        "## Page 1\n\nThe arbitrator shall give notice to the parties of the hearing.\n",
        encoding="utf-8",
    )
    result = verify_markdown(md)
    names = {c["name"]: c["ok"] for c in result["checks"]}
    assert names["markdown_exists"] is True
    assert names["has_front_matter"] is True
    assert names["has_page_headings"] is True
    assert names["has_words"] is True
