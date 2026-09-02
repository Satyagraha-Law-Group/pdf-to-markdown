from pathlib import Path

from slip_pdf_md.registry import STATUS_DONE, Registry, sha256_file


def test_registry_uniqueness_same_bytes_two_names(tmp_path: Path):
    db = tmp_path / "registry.sqlite"
    a = tmp_path / "opinion.pdf"
    b = tmp_path / "opinion (1).pdf"
    payload = b"%PDF-1.4 fake but hashed as bytes\n"
    a.write_bytes(payload)
    b.write_bytes(payload)
    assert sha256_file(a) == sha256_file(b)

    reg = Registry(db)
    row1 = reg.see(a, routed_to="10_02_READY_FOR_DOCLING")
    sha = row1["sha256"]
    reg.set_status(sha, STATUS_DONE, output_path=str(tmp_path / "opinion.md"))
    row2 = reg.see(b, routed_to="50_90_DUPLICATES", sha256=sha)

    assert reg.count_documents() == 1
    assert reg.count_sightings(sha) == 2
    assert row2["original_filename"] == "opinion.pdf"
    assert row2["status"] == STATUS_DONE
    assert reg.should_convert(sha) is False
    reg.close()


def test_needs_review_may_retry(tmp_path: Path):
    db = tmp_path / "registry.sqlite"
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"abc")
    reg = Registry(db)
    row = reg.see(pdf, routed_to="10_02_READY_FOR_DOCLING")
    reg.set_status(row["sha256"], "NEEDS_REVIEW")
    assert reg.should_convert(row["sha256"]) is True
    reg.close()
