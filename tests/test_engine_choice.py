from slip_pdf_md.engine_choice import format_choice_help, prompt_engine


def test_explicit_aliases():
    assert prompt_engine("1") == "pymupdf"
    assert prompt_engine("pymupdf") == "pymupdf"
    assert prompt_engine("2") == "mistral"
    assert prompt_engine("mistralai") == "mistral"
    assert prompt_engine("mistral ai") == "mistral"


def test_noninteractive_defaults_local():
    assert prompt_engine(None, interactive=False) == "pymupdf"


def test_choice_help_names_both_engines():
    text = format_choice_help()
    assert "1) Local Tesseract" in text
    assert "2) Mistral AI" in text
    assert "force reconvert" not in text.lower()


def test_force_banner_still_asks():
    text = format_choice_help(force=True)
    assert "force reconvert" in text.lower()
    assert "1) Local Tesseract" in text
    assert "2) Mistral AI" in text


def test_interactive_always_prompts_even_if_engine_passed(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "1")
    assert prompt_engine("mistral", interactive=True, force=True) == "pymupdf"
    out = capsys.readouterr().out
    assert "Local Tesseract" in out
    assert "Mistral AI" in out
    assert "force reconvert" in out.lower()


def test_interactive_choice_two_is_mistral(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "2")
    assert prompt_engine(None, interactive=True) == "mistral"
