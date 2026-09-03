
import pytest

from slip_pdf_md.engines import get_engine
from slip_pdf_md.engines.mistral_engine import (
    MistralConfigError,
    MistralOcrEngine,
    parse_ocr_pages,
    resolve_api_key,
)


def test_engine_aliases():
    assert get_engine("mistral").name == "mistral"
    assert get_engine("mistralai").name == "mistral"
    assert get_engine("mistral-ocr").name == "mistral"


def test_parse_ocr_pages_keeps_order():
    payload = {
        "model": "mistral-ocr-latest",
        "pages": [
            {"index": 0, "markdown": "Page one heading\n\nBody."},
            {"index": 1, "markdown": "| A | B |\n| --- | --- |\n| 1 | 2 |"},
        ],
        "usage_info": {"pages_processed": 2, "doc_size_bytes": 99},
    }
    pages, meta = parse_ocr_pages(payload)
    assert len(pages) == 2
    assert pages[0].startswith("Page one")
    assert "---" in pages[1]
    assert meta["pages_processed"] == 2


def test_missing_api_key(monkeypatch, tmp_path):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.delenv("MISTRALAI_API_KEY", raising=False)
    monkeypatch.setattr("slip_pdf_md.engines.mistral_engine.load_secrets", lambda *a, **k: {})
    engine = MistralOcrEngine()
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    with pytest.raises(MistralConfigError):
        engine.convert(pdf)


def test_convert_with_fake_transport(tmp_path):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 content")
    calls = []

    def transport(op, method, url, api_key, **kwargs):
        calls.append(op)
        if op == "upload":
            assert kwargs["filename"] == "scan.pdf"
            assert kwargs["content"].startswith(b"%PDF")
            return {"id": "file-abc"}
        if op == "signed_url":
            return {"url": "https://example.invalid/signed"}
        if op == "ocr":
            body = kwargs["json_body"]
            assert body["model"] == "mistral-ocr-latest"
            assert body["document"]["document_url"] == "https://example.invalid/signed"
            assert body["include_image_base64"] is False
            return {
                "model": "mistral-ocr-latest",
                "pages": [
                    {"index": 0, "markdown": "Section 21 commences on notice."},
                    {"index": 1, "markdown": "Section 22 equal treatment."},
                ],
                "usage_info": {"pages_processed": 2, "doc_size_bytes": 16},
            }
        if op == "delete":
            return {"id": "file-abc", "deleted": True}
        raise AssertionError(op)

    engine = MistralOcrEngine(api_key="test-key", transport=transport, delete_upload=True)
    result = engine.convert(pdf)
    assert result.engine == "mistral"
    assert result.page_count == 2
    assert result.needs_review is False
    assert "equal treatment" in result.pages[1]
    assert result.usage["mistral_pages_processed"] == 2
    assert calls == ["upload", "signed_url", "ocr", "delete"]


def test_resolve_api_key_from_env(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "  abc  ")
    assert resolve_api_key() == "abc"
