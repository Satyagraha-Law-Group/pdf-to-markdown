from pathlib import Path

import fitz
import pytest

from slip_pdf_md.convert import convert_pdf
from slip_pdf_md.key_lease import (
    SENTINEL_NAME,
    api_key_fingerprint,
    require_fingerprint,
    uses_remote_api,
)
from slip_pdf_md.registry import (
    STATUS_APPROVED,
    STATUS_AWAITING_APPROVAL,
    Registry,
)


def _text_pdf(path: Path, text: str) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


def test_require_fingerprint_refuses_raw_key():
    with pytest.raises(ValueError, match="refuses to store a secret"):
        require_fingerprint("sk-mistral-this-is-not-a-hash")
    fp = api_key_fingerprint("sk-mistral-this-is-not-a-hash")
    assert require_fingerprint(fp) == fp
    assert fp != "sk-mistral-this-is-not-a-hash"


def test_gubernatio_record_refuses_raw_api_key(tmp_path):
    reg = Registry(tmp_path / "registry.sqlite")
    with pytest.raises(ValueError, match="refuses to store a secret"):
        reg.gubernatio_record(
            sha256="ab" * 32,
            filename="x.pdf",
            step="bad",
            status="PROCESSING",
            api_key_fingerprint="sk-mistral-raw-secret-value",
        )
    fp = api_key_fingerprint("sk-mistral-raw-secret-value")
    reg.gubernatio_record(
        sha256="ab" * 32,
        filename="x.pdf",
        step="lease",
        status="PROCESSING",
        api_key_fingerprint=fp,
        api_provider="mistral",
    )
    rows = reg.gubernatio_rows()
    assert all(r.get("api_key_fingerprint") != "sk-mistral-raw-secret-value" for r in rows)
    assert any(r.get("api_key_fingerprint") == fp for r in rows)
    assert any(r.get("api_provider") == "mistral" for r in rows)
    reg.close()


def test_uses_remote_api_placeholder_engines():
    assert uses_remote_api("mistral") is True
    assert uses_remote_api("docling") is True
    assert uses_remote_api("google") is True
    assert uses_remote_api("claude") is True
    assert uses_remote_api("hermes") is True
    assert uses_remote_api("reducto") is True
    assert uses_remote_api("pymupdf") is False


def test_different_fingerprints_may_run_in_parallel(tmp_path, monkeypatch):
    monkeypatch.setenv("SLIP_AGENT", "Spock")
    db = tmp_path / "registry.sqlite"
    sent = tmp_path / SENTINEL_NAME
    reg = Registry(db)
    a = reg.acquire_key_lease(
        fingerprint=api_key_fingerprint("mistral-key-one"),
        sentinel=sent,
        sha256="aa" * 32,
        filename="one.pdf",
        api_provider="mistral",
    )
    b = reg.acquire_key_lease(
        fingerprint=api_key_fingerprint("docling-key-two"),
        sentinel=sent,
        sha256="bb" * 32,
        filename="two.pdf",
        api_provider="docling",
    )
    assert a["ok"] is True
    assert b["ok"] is True
    assert a["fingerprint"] != b["fingerprint"]
    reg.release_key_lease(
        fingerprint=a["fingerprint"], sentinel=sent, sha256="aa" * 32, filename="one.pdf"
    )
    assert sent.exists()
    reg.release_key_lease(
        fingerprint=b["fingerprint"], sentinel=sent, sha256="bb" * 32, filename="two.pdf"
    )
    assert not sent.exists()
    reg.close()


def test_convert_awaits_lawyer_before_gubernatio_closes(slip_tree):
    pdf = _text_pdf(slip_tree.raw / "opinion.pdf", "Satyagraha Law Group hears the petition.")
    reg = Registry(slip_tree.registry_path)
    result = convert_pdf(pdf, slip_tree, reg, move_raw=True)
    sha = result["sha256"]
    assert result["status"] == STATUS_AWAITING_APPROVAL
    assert result["duplicate"] is False
    text = Path(result["output"]).read_text(encoding="utf-8")
    assert "processing_status: AWAITING_APPROVAL" in text
    assert reg.get(sha)["status"] == STATUS_AWAITING_APPROVAL
    assert reg.gubernatio_is_extracted(sha) is True
    assert reg.gubernatio_loop_closed(sha) is False
    twin = slip_tree.raw / "opinion-copy.pdf"
    processed = next(slip_tree.processed.rglob("opinion.pdf"))
    twin.write_bytes(processed.read_bytes())
    two = convert_pdf(twin, slip_tree, reg, move_raw=True)
    assert two["duplicate"] is True
    assert two["status"] == STATUS_AWAITING_APPROVAL
    approved = reg.approve(sha, by="Anil B")
    assert approved["status"] == STATUS_APPROVED
    assert reg.gubernatio_loop_closed(sha) is True
    rows = reg.gubernatio_rows(sha)
    assert any(r.get("step") == "lawyer_approved" and r.get("approved_by") == "Anil B" for r in rows)
    report = reg.write_awaiting_approval_report(slip_tree.registry_dir)
    assert report.name.startswith("Awaiting-Approval-Report-v1-")
    body = report.read_text(encoding="utf-8")
    assert "awaiting_count: 0" in body
    reg.close()
