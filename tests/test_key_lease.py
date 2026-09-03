from pathlib import Path

import fitz

from slip_pdf_md.convert import convert_pdf
from slip_pdf_md.key_lease import (
    SENTINEL_NAME,
    api_key_fingerprint,
    sentinel_path,
    uses_mistral,
    uses_remote_api,
)
from slip_pdf_md.registry import Registry, sha256_file


def _text_pdf(path: Path, text: str) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


def test_sentinel_name_is_anils_exact_string():
    assert SENTINEL_NAME == "SLG-pdf_to_md_file_naming_convention.text"
    assert sentinel_path(Path("/tmp/gub")).name == SENTINEL_NAME


def test_uses_mistral_only_for_mistral_engines():
    assert uses_mistral("mistral") is True
    assert uses_mistral("mistralai") is True
    assert uses_mistral("pymupdf") is False
    assert uses_remote_api("mistral") is True
    assert uses_remote_api("pymupdf") is False


def test_second_agent_is_halted_until_release(tmp_path, monkeypatch):
    db = tmp_path / "registry.sqlite"
    sent = tmp_path / SENTINEL_NAME
    fp = api_key_fingerprint("secret-key-xyz")
    monkeypatch.setenv("SLIP_AGENT", "Spock")
    monkeypatch.setenv("COMPUTERNAME", "DESKTOP-IG57K1N")
    reg = Registry(db)
    first = reg.acquire_key_lease(
        fingerprint=fp, sentinel=sent, sha256="ab" * 32, filename="one.pdf"
    )
    assert first["ok"] is True
    assert sent.is_file()
    assert sent.stat().st_size == 0
    assert first["fingerprint"] == fp
    assert first["fingerprint"] != "secret-key-xyz"
    monkeypatch.setenv("SLIP_AGENT", "Claude")
    second = reg.acquire_key_lease(
        fingerprint=fp, sentinel=sent, sha256="cd" * 32, filename="two.pdf"
    )
    assert second["ok"] is False
    assert second["reason"] == "held"
    rows = reg.gubernatio_rows()
    assert all(r.get("api_key_fingerprint") != "secret-key-xyz" for r in rows)
    monkeypatch.setenv("SLIP_AGENT", "Spock")
    reg.release_key_lease(
        fingerprint=fp, sentinel=sent, sha256="ab" * 32, filename="one.pdf"
    )
    assert not sent.exists()
    monkeypatch.setenv("SLIP_AGENT", "Claude")
    third = reg.acquire_key_lease(
        fingerprint=fp, sentinel=sent, sha256="cd" * 32, filename="two.pdf"
    )
    assert third["ok"] is True
    reg.release_key_lease(
        fingerprint=fp, sentinel=sent, sha256="cd" * 32, filename="two.pdf"
    )
    reg.close()


def test_expired_lease_is_not_stuck_forever(tmp_path, monkeypatch):
    db = tmp_path / "registry.sqlite"
    sent = tmp_path / SENTINEL_NAME
    fp = api_key_fingerprint("secret-key-xyz")
    monkeypatch.setenv("SLIP_AGENT", "VPS")
    monkeypatch.setenv("SLIP_KEY_LEASE_SECONDS", "1")
    reg = Registry(db)
    first = reg.acquire_key_lease(
        fingerprint=fp, sentinel=sent, sha256="ab" * 32, filename="one.pdf", ttl_seconds=0
    )
    assert first["ok"] is True
    monkeypatch.setenv("SLIP_AGENT", "Spock")
    second = reg.acquire_key_lease(
        fingerprint=fp, sentinel=sent, sha256="cd" * 32, filename="two.pdf", ttl_seconds=60
    )
    assert second["ok"] is True
    reg.release_key_lease(
        fingerprint=fp, sentinel=sent, sha256="cd" * 32, filename="two.pdf"
    )
    reg.close()


def test_gubernatio_done_gates_before_registry(slip_tree):
    pdf = _text_pdf(slip_tree.raw / "prior.pdf", "Already governed as done.")
    sha = sha256_file(pdf)
    reg = Registry(slip_tree.registry_path)
    reg.gubernatio_record(sha256=sha, filename=pdf.name, step="prior_done", status="DONE")
    assert reg.get(sha) is None
    result = convert_pdf(pdf, slip_tree, reg, move_raw=True)
    assert result["duplicate"] is True
    assert result["status"] == "DONE"
    row = reg.get(sha)
    assert row is not None
    assert row["status"] == "DONE"
    reg.close()


def test_convert_halts_when_mistral_lease_held(slip_tree, monkeypatch):
    pdf = _text_pdf(slip_tree.raw / "busy.pdf", "Should not convert while lease held.")
    key = "secret-key-xyz"
    monkeypatch.setenv("MISTRAL_API_KEY", key)
    monkeypatch.setenv("SLIP_AGENT", "Claude")
    reg = Registry(slip_tree.registry_path)
    fp = api_key_fingerprint(key)
    sent = sentinel_path(slip_tree.registry_dir)
    held = reg.acquire_key_lease(
        fingerprint=fp, sentinel=sent, sha256="ee" * 32, filename="other.pdf"
    )
    assert held["ok"] is True
    monkeypatch.setenv("SLIP_AGENT", "Spock")
    result = convert_pdf(pdf, slip_tree, reg, engine_name="mistral", move_raw=True)
    assert result["status"] == "HALTED"
    assert pdf.exists()
    assert list(slip_tree.ready.rglob("*.pdf")) == []
    assert list(slip_tree.clean.glob("*.md")) == []
    monkeypatch.setenv("SLIP_AGENT", "Claude")
    reg.release_key_lease(
        fingerprint=fp, sentinel=sent, sha256="ee" * 32, filename="other.pdf"
    )
    reg.close()


def test_local_engine_does_not_create_sentinel(slip_tree):
    pdf = _text_pdf(slip_tree.raw / "local.pdf", "Local tesseract needs no key lease.")
    reg = Registry(slip_tree.registry_path)
    result = convert_pdf(pdf, slip_tree, reg, engine_name="pymupdf", move_raw=True)
    assert result["status"] == "AWAITING_APPROVAL"
    assert not sentinel_path(slip_tree.registry_dir).exists()
    reg.close()
