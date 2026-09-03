from pathlib import Path

from slip_pdf_md.secrets import (
    DUMMY_KEY,
    parse_secrets_text,
    write_secret_templates,
)


def test_parse_setx_line():
    parsed = parse_secrets_text('setx MISTRAL_API_KEY "abcDEF123"')
    assert parsed["MISTRAL_API_KEY"] == "abcDEF123"


def test_parse_key_equals_value():
    parsed = parse_secrets_text("MISTRAL_API_KEY=sk-live-example\n# comment\n")
    assert parsed["MISTRAL_API_KEY"] == "sk-live-example"


def test_parse_export_and_set():
    text = "export MISTRAL_API_KEY=one\nset MISTRALAI_API_KEY=two\n"
    parsed = parse_secrets_text(text)
    assert parsed["MISTRAL_API_KEY"] == "one"
    assert parsed["MISTRALAI_API_KEY"] == "two"


def test_write_templates_do_not_overwrite_real(tmp_path: Path):
    existing = tmp_path / "SECRETS.txt"
    existing.write_text("MISTRAL_API_KEY=real-not-dummy\n", encoding="utf-8")
    written = write_secret_templates(tmp_path)
    assert written["example"].name == "SECRETS.example"
    assert "replace-with-your-mistral-api-key" in written["example"].read_text(encoding="utf-8")
    assert existing.read_text(encoding="utf-8").startswith("MISTRAL_API_KEY=real-not-dummy")
    assert DUMMY_KEY not in existing.read_text(encoding="utf-8")
