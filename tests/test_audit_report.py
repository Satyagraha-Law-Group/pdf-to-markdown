from slip_pdf_md.audit import run_audit
from slip_pdf_md.naming import REPORT_NAME_RE
from slip_pdf_md.registry import Registry


def test_audit_writes_three_word_named_report(slip_tree):
    sample = slip_tree.clean / "sample.md"
    sample.write_text(
        "---\ndocument_type: legal_pdf\nsource_file: sample.pdf\n"
        "source_sha256: " + ("ab" * 32) + "\n"
        "processing_status: DONE\nengine: pymupdf+tesseract\n"
        "page_count: 1\nconverted_at: 2026-09-02T22:55:00+05:30\n---\n\n"
        "## Page 1\n\nHello from Satyagraha Law Group.\n",
        encoding="utf-8",
    )
    reg = Registry(slip_tree.registry_path)
    result = run_audit(slip_tree, reg)
    reg.close()
    report = result["report"]
    assert report.exists()
    assert REPORT_NAME_RE.match(report.name), report.name
    assert report.name.startswith("Audit-Quality-Report-v1-")
    body = report.read_text(encoding="utf-8")
    assert "Satyagraha Law Group" in body
    assert "Audit Quality Report" in body
