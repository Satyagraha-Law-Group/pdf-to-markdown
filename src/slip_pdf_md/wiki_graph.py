"""Obsidian wiki-link graph and HTML href integrity for SLIP docs."""

from __future__ import annotations

import re
from pathlib import Path

from slip_pdf_md.branding import WIKI_CATALOG, resolve_wiki_file, tool_root

WIKI_RE = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
MD_HREF_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
HTML_HREF_RE = re.compile(r'href="([^"]+)"')


def extract_wiki_names(text: str) -> list[str]:
    names = []
    for match in WIKI_RE.finditer(text):
        name = match.group(1).strip()
        if name and name not in names:
            names.append(name)
    return names


def catalog_names() -> set[str]:
    return {name for name, _, _ in WIKI_CATALOG}


def find_user_guide(root: Path | None = None) -> Path | None:
    root = Path(root or tool_root())
    docs = root / "docs"
    if not docs.is_dir():
        return None
    matches = sorted(docs.glob("Lawyer-User-Guide-*.md"))
    return matches[-1] if matches else None


def check_wiki_graph(root: Path | None = None) -> dict:
    """One integrity check: every wiki link in the user guide resolves to a file."""
    root = Path(root or tool_root())
    guide = find_user_guide(root)
    missing_catalog = []
    missing_files = []
    broken_hrefs = []
    wiki_names: list[str] = []
    if guide is None:
        return {
            "ok": False,
            "root": str(root),
            "guide": None,
            "wiki_names": [],
            "missing_catalog": ["Lawyer-User-Guide"],
            "missing_files": [],
            "broken_hrefs": ["user guide markdown is missing"],
        }
    text = guide.read_text(encoding="utf-8")
    wiki_names = extract_wiki_names(text)
    known = catalog_names()
    for name in wiki_names:
        if name not in known:
            missing_catalog.append(name)
        hint = next((h for n, h, _ in WIKI_CATALOG if n == name), name)
        target = resolve_wiki_file(root, hint)
        if target is None or not target.is_file():
            missing_files.append(name)

    html = guide.with_suffix(".html")
    if html.is_file():
        html_text = html.read_text(encoding="utf-8")
        base = html.parent
        for href in HTML_HREF_RE.findall(html_text):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            if href.startswith("#"):
                continue
            candidate = (base / href).resolve()
            if not candidate.exists():
                broken_hrefs.append(href)
    else:
        broken_hrefs.append("user guide HTML is missing")

    ok = not missing_catalog and not missing_files and not broken_hrefs
    return {
        "ok": ok,
        "root": str(root),
        "guide": str(guide),
        "wiki_names": wiki_names,
        "missing_catalog": missing_catalog,
        "missing_files": missing_files,
        "broken_hrefs": broken_hrefs,
    }
