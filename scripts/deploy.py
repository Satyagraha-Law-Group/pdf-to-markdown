#!/usr/bin/env python3
"""Satyagraha Law Group — SLIP PDF to Markdown Ingestion Tool deploy.

Bootstrap a Satyagraha Law Group SLIP vault.
Research project. Not legal advice. Not a solicitation.
https://www.satyagraha.com
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from slip_pdf_md import FAMILY, ORG, PRODUCT_NAME
from slip_pdf_md.naming import three_word_filename
from slip_pdf_md.scaffold import create_slip_tree

SKIP_COPY_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "markdown",
    "delete me",
    "md_repair_work",
    "MASTER_MACDONE.md",
    ".pytest_cache",
    "web_jobs",
}


def _copy_tree(src: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in SKIP_COPY_NAMES or item.name.endswith(".pdf"):
            continue
        if item.name == ".venv":
            continue
        target = dest / item.name
        if item.is_dir():
            if item.name == "legacy" and target.exists():
                continue
            shutil.copytree(item, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*SKIP_COPY_NAMES, "*.pdf"))
        else:
            if item.suffix.lower() == ".pdf":
                continue
            shutil.copy2(item, target)


def _write_pointer(dest: Path, tool_dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    readme = dest / "README.md"
    readme.write_text(
        "\n".join(
            [
                f"# {ORG}",
                "",
                f"**{PRODUCT_NAME}** — tooling pointer.",
                f"**Family:** {FAMILY}",
                "",
                "The working copy of this product (with git history) lives at:",
                "",
                f"`{tool_dest}`",
                "",
                "This folder on purpose does **not** duplicate `.venv`.",
                "Install once in Convert-PDF-TO-MARKDOWN-01:",
                "",
                "```text",
                "pip install -e .",
                "```",
                "",
                "Public repo: https://github.com/Satyagraha-Law-Group/pdf-to-markdown",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_lawyer_guide(paths, tool_dest: Path) -> Path:
    name = three_word_filename("Lawyer", "Instruction", "Guide")
    dest = tool_dest / name
    dest.write_text(
        "\n".join(
            [
                f"# {ORG}",
                "",
                f"# {PRODUCT_NAME} — Lawyer Instruction Guide",
                "",
                f"**Family:** {FAMILY}",
                "",
                "SLIP PDF to Markdown Ingestion Tool. No Python required after someone has run deploy.",
                "",
                "1. Put PDFs in `0_01_RAW_PDF`.",
                "2. Ask whoever keeps the machine to run convert, or open the web page if it is running.",
                "3. Open `20_03_CLEAN_MARKDOWN`.",
                "",
                "Same PDF under a new name is converted **once**. Duplicates go to `50_90_DUPLICATES` and are never deleted by the tool.",
                "",
                f"- Tool folder: `{tool_dest}`",
                f"- SLIP root: `{paths.root}`",
                "- Public repo: https://github.com/Satyagraha-Law-Group/pdf-to-markdown",
                "",
                "For an LLM: open `playbooks/01-Deploy-Scaffold.md` and point it at that GitHub URL.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return dest


def deploy(vault: Path, skip_install: bool = False) -> dict:
    paths = create_slip_tree(vault)
    tool_dest = paths.tool
    tool_dest.mkdir(parents=True, exist_ok=True)
    if tool_dest.resolve() != ROOT.resolve():
        _copy_tree(ROOT, tool_dest)
    pointer = paths.tooling / "pdf-to-markdown"
    if pointer.resolve() != tool_dest.resolve():
        _write_pointer(pointer, tool_dest)
    guide = _write_lawyer_guide(paths, tool_dest)
    if not skip_install:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-e", str(tool_dest)],
        )
    return {"slip_root": paths.root, "tool": tool_dest, "guide": guide}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=f"{ORG} — deploy {PRODUCT_NAME} into a SLIP vault"
    )
    parser.add_argument("--vault", required=True, help="Vault parent or SLIP root")
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args(argv)
    info = deploy(Path(args.vault), skip_install=args.skip_install)
    print(f"{ORG} — {PRODUCT_NAME} deployed")
    print(f"slip_root={info['slip_root']}")
    print(f"tool={info['tool']}")
    print(f"guide={info['guide']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
