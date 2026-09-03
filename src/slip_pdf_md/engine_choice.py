"""Prompt a lawyer to pick Local Tesseract or Mistral AI.

Always asks in a real terminal, including --force reconverts.
`--engine` is only for scripts and non-interactive runs.
"""

from __future__ import annotations

import sys

from slip_pdf_md.branding import header_text

CHOICE_HELP = """
Choose the conversion engine:

  1) Local Tesseract
     Stays on this computer. Nothing is uploaded.
     Use for privileged or sealed papers.

  2) Mistral AI
     Uploads the PDF to Mistral. Stronger on tables and formulas.
     Needs a key in SECRETS.txt.
""".strip()

FORCE_BANNER = "This is a force reconvert. Pick an engine anyway."


def format_choice_help(*, force: bool = False) -> str:
    if force:
        return FORCE_BANNER + "\n\n" + CHOICE_HELP
    return CHOICE_HELP


def prompt_engine(
    explicit: str | None,
    *,
    interactive: bool | None = None,
    force: bool = False,
) -> str:
    """Ask 1 = Local Tesseract, 2 = Mistral AI.

    A terminal session always prompts (first convert or --force).
    Non-interactive runs use `--engine` if given, otherwise Local Tesseract.
    """
    use_tty = sys.stdin.isatty() if interactive is None else interactive
    if use_tty:
        print(header_text())
        print()
        print(format_choice_help(force=force))
        print()
        try:
            raw = input("Enter 1 (Local Tesseract) or 2 (Mistral AI) [default 1]: ").strip()
        except EOFError:
            raw = ""
        return _parse_choice(raw, default_local=True)

    if explicit:
        return _parse_choice(explicit, default_local=False)
    print("No interactive terminal — using Local Tesseract (nothing uploaded).")
    print("Pass --engine mistral to use Mistral AI from a script.")
    return "pymupdf"


def _parse_choice(raw: str, *, default_local: bool) -> str:
    key = (raw or "").strip().lower()
    if key in {"", "1"} and default_local:
        print("Using Local Tesseract.")
        return "pymupdf"
    if key in {"1", "local", "pymupdf", "tesseract", "pymupdf+tesseract", "local tesseract"}:
        print("Using Local Tesseract.")
        return "pymupdf"
    if key in {"2", "mistral", "mistralai", "mistral-ocr", "mistral ai"}:
        print("Using Mistral AI. The PDF will be uploaded.")
        return "mistral"
    if default_local:
        print(f"Unrecognized {raw!r} — using Local Tesseract.")
        return "pymupdf"
    return key
