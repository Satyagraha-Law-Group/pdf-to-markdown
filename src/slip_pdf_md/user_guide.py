"""Compile the Lawyer User Guide (markdown + HTML) with wiki links."""

from __future__ import annotations

import html as html_lib
from pathlib import Path

from slip_pdf_md.branding import (
    footer_markdown,
    header_markdown,
    html_wrap,
    related_markdown,
    resolve_wiki_file,
    tool_root,
    with_single_footer,
)
from slip_pdf_md.naming import three_word_filename


def _md_to_html(text: str, root: Path | None = None) -> str:
    """Small markdown-to-HTML for the user guide. Wiki links become file links."""
    import re

    from slip_pdf_md.branding import WIKI_CATALOG, href_from

    root = Path(root or tool_root())
    catalog = {name: hint for name, hint, _ in WIKI_CATALOG}

    def wiki_sub(match: re.Match) -> str:
        name = match.group(1).strip()
        hint = catalog.get(name, name)
        target = resolve_wiki_file(root, hint)
        if target is None:
            return f"<code>[[{html_lib.escape(name)}]]</code>"
        href = href_from(root, target, from_docs=True, from_playbooks=False, html=True)
        return f'<a href="{html_lib.escape(href)}">{html_lib.escape(name)}</a>'

    body = text
    # drop header/footer duplication for HTML wrap
    if body.startswith("# Satyagraha Law Group"):
        _hdr, _sep, rest = body.partition("---")
        if _sep:
            body = rest.lstrip("\n")
    if "\n---\n" in body:
        body = body.rsplit("\n---\n", 1)[0]
    body = re.sub(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]", wiki_sub, body)
    out = []
    for line in body.splitlines():
        if line.startswith("# "):
            out.append(f"<h1>{html_lib.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            out.append(f"<h2>{html_lib.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            out.append(f"<h3>{html_lib.escape(line[4:])}</h3>")
        elif line.startswith("- "):
            inner = line[2:]
            inner = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', inner)
            out.append(f"<li>{inner}</li>")
        elif line.startswith("```"):
            out.append("<pre>" if "```" == line.strip() or line.startswith("```") else "")
        elif line.strip() == "":
            out.append("")
        else:
            inner = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', line)
            inner = re.sub(r"`([^`]+)`", r"<code>\1</code>", inner)
            inner = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", inner)
            out.append(f"<p>{inner}</p>")
    html = "\n".join(out)
    html = re.sub(r"(?:<li>.*</li>\n?)+", lambda m: "<ul>\n" + m.group(0) + "</ul>\n", html)
    return html


def guide_markdown(root: Path | None = None) -> str:
    return "\n".join(
        [
            header_markdown(),
            "# Lawyer User Guide",
            "",
            "This is the hub for converting a PDF to Markdown in the Satyagraha Law Group SLIP vault.",
            "Open this file in Obsidian to see the graph: every wiki link (the bracket-name form) is a real related file.",
            "On the web, use the HTML twin of this guide — each wiki name is a clickable file.",
            "",
            related_markdown(from_docs=True, root=root),
            "## What this product does",
            "",
            "[[README]] is the product overview. You drop a PDF in RAW. The tool hashes the bytes,",
            "asks GUBERNATIO whether this file is new, converts it to Markdown, and stages the",
            "result for a lawyer to approve. Filename is not identity. SHA-256 of the PDF bytes is.",
            "",
            "Terms live in [[Slip-Markdown-Glossary]]. The pipeline picture is [[Convert-Pipeline-Flowchart]].",
            "Requirements are [[Product-Requirements-Spec]]. Design is [[System-Design-Document]].",
            "Architecture is [[System-Architecture-Diagram]]. The implementation sequence is [[Implementation-Plan-Guide]].",
            "",
            "## Convert a PDF",
            "",
            "Day-to-day steps are in [[02-Convert-Documents]]. First-time folders are [[01-Deploy-Scaffold]].",
            "Quality after convert is [[03-Audit-Quality]]. A second copy of the same bytes is [[04-Handle-Duplicates]].",
            "Repair of already-written Markdown is [[05-Repair-Markdown]]. The narrative flow is [[Process-Workflow-Guide]].",
            "",
            "Before every convert the tool asks which engine:",
            "",
            "- `1` Local Tesseract — nothing is uploaded",
            "- `2` Mistral AI — the PDF is uploaded. Details in [[Mistral-Engine-Guide]] and [[Marker-Mistral-Engine]].",
            "",
            "```text",
            'slip-pdf-md convert --vault "D:\\satyagraha\\VAULT\\Satyagraha Law Group\\SLIP_DOCUMENT_PROCESSING"',
            "```",
            "",
            "## Token usage for each convert",
            "",
            "Each PDF-to-Markdown run stores **token usage for that file** in four places:",
            "",
            "- the identity table `documents.token_usage` (latest convert of this SHA-256)",
            "- **GUBERNATIO** `token_usage` on the convert row (this run)",
            "- Conversion-Run-Log and Conversion-Runs-Journal next to the registry",
            "- YAML front matter `token_usage` on the Markdown itself, plus the session convert summary",
            "",
            "Local Tesseract uses zero LLM tokens. The column still records `markdown_tokens_estimate`",
            "(output size, chars/4) and `equivalent_internal_total_tokens` (1,105 vision tokens per page",
            "plus that markdown estimate). Mistral OCR is billed per page: `mistral_pages_processed`.",
            "",
            "Inspect:",
            "",
            "```text",
            "slip-pdf-md registry gubernatio --vault PATH",
            "```",
            "",
            "## GUBERNATIO",
            "",
            "GUBERNATIO is the Latin noun for the system of governance, steering, direction, and administration.",
            "It is the entry gate after SHA-256. One row per file-event (this filename, this host, this agent,",
            "this step). `documents` stays one row per hash.",
            "",
            "A successful convert stages Markdown as `AWAITING_APPROVAL`. The loop is not closed until a",
            "Satyagraha lawyer runs `slip-pdf-md approve`. Then status is `APPROVED`.",
            "Lawyer-facing command notes are in [[Lawyer-Instruction-Guide]].",
            "",
            "## Test runs and error codes",
            "",
            "TEST_CASES is the source of truth for every test scenario. New tests upsert that table first.",
            "Each pytest run appends TEST_RUNS / TEST_RESULTS and republishes [[Test-Suite-Summary]] and [[Test-Suite-Detailed]].",
            "Each convert appends PROCESS_RUNS: the day, the filename, PDF pages, markdown pages, API key type, and whether a lawyer has approved.",
            "Classified product errors live in [[Error-Code-Catalog]] (HIGH / MEDIUM / LOW). New features register a code there.",
            "How we build tools this way is [[Tool-Build-Practice]].",
            "",
            "## Tests, FAQs, memory",
            "",
            "Numbered test cases: [[Test-Suite-Summary]]. Plain-English questions: [[Slip-Product-Faqs]].",
            "How the tool was built: [[Tool-Creation-Memory]]. This session: [[Session-Learning-Notes]].",
            "",
            footer_markdown(),
        ]
    ).replace("[[GUBERNATIO]]", "GUBERNATIO")


def write_lawyer_user_guide(root: Path | None = None) -> tuple[Path, Path]:
    """Write Lawyer-User-Guide markdown and HTML under docs/."""
    root = Path(root or tool_root())
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    existing = sorted(docs.glob("Lawyer-User-Guide-*.md"))
    md_path = existing[0] if existing else docs / three_word_filename("Lawyer", "User", "Guide", ext="md")
    md_path.write_text("# Lawyer User Guide\n", encoding="utf-8")
    body = with_single_footer(guide_markdown(root=root))
    md_path.write_text(body, encoding="utf-8")
    html_path = md_path.with_suffix(".html")
    html_path.write_text(
        html_wrap("Lawyer User Guide", _md_to_html(body, root=root), from_docs=True, root=root),
        encoding="utf-8",
    )
    return md_path, html_path
