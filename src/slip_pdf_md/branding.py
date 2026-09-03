"""Satyagraha Law Group header, footer, and research disclaimer.

Cues from https://www.satyagraha.com and the public site index:
https://github.com/anilsatyagraha/satyagraha-website/blob/main/index.md

  आ नो भद्राः क्रतवो यन्तु विश्वतः
  Let noble thoughts come to us from every side. — Rig Veda
  The law is reason, free from passion.

HTML guides use a white background, black text, and black borders.
"""

from __future__ import annotations

from pathlib import Path as FsPath

ORG = "Satyagraha Law Group"
PRODUCT = "SLIP PDF to Markdown Ingestion Tool"
FAMILY = "SLIP"
SITE = "https://www.satyagraha.com"
SITE_INDEX = "https://github.com/anilsatyagraha/satyagraha-website/blob/main/index.md"
CALENDLY = "https://calendly.com/anil-satyagraha/15min"
SANSKRIT = "आ नो भद्राः क्रतवो यन्तु विश्वतः"
RIG_VEDA = "Let noble thoughts come to us from every side. — Rig Veda"
ARISTOTLE = "The law is reason, free from passion."
TAGLINE = "Legal Research  ·  Practitioner-Scholar"
PUBLISH_LINE = (
    "Satyagraha Law Group publishes a SLIP PDF to Markdown Ingestion Tool. "
    "It does not publish a library."
)
FOUNDER_LINE = (
    "Founded by Anil B. (Lawyer), Satyagraha Law Group provides legal services "
    "for seekers looking for help by searching for Corporate Law, Civil Law, "
    "Criminal Law, Writs, High Court Lawyer, NRI Lawyer, Lawyer In Hyderabad, India."
)
NEED_HELP = "Need Legal Help."
DISCLAIMER = (
    "This is a research project at Satyagraha Law Group as part of its pursuit "
    "of excellence in legal research. It is not legal advice, not a solicitation, "
    "and not an offer to represent anyone."
)

# wiki name, path hint (prefix or exact file from tool root), label
WIKI_CATALOG = [
    ("README", "README.md", "Product overview"),
    ("Lawyer-User-Guide", "docs/Lawyer-User-Guide", "User guide hub"),
    ("Lawyer-Instruction-Guide", "Lawyer-Instruction-Guide.md", "Lawyer instruction"),
    ("Mistral-Engine-Guide", "docs/Mistral-Engine-Guide", "Mistral engine guide"),
    ("Marker-Mistral-Engine", "docs/Marker-Mistral-Engine", "Mistral engine mapping"),
    ("Product-Requirements-Spec", "docs/Product-Requirements-Spec", "Requirements"),
    ("System-Design-Document", "docs/System-Design-Document", "Design"),
    ("Implementation-Plan-Guide", "docs/Implementation-Plan-Guide", "Plan"),
    ("System-Architecture-Diagram", "docs/System-Architecture-Diagram", "Architecture"),
    ("Process-Workflow-Guide", "docs/Process-Workflow-Guide", "Workflow"),
    ("Slip-Markdown-Glossary", "docs/Slip-Markdown-Glossary", "Glossary"),
    ("Convert-Pipeline-Flowchart", "docs/Convert-Pipeline-Flowchart", "Pipeline flowchart"),
    ("Slip-Product-Faqs", "docs/Slip-Product-Faqs", "FAQs"),
    ("Test-Suite-Summary", "docs/Test-Suite-Summary", "Test suite summary"),
    ("Test-Suite-Detailed", "docs/Test-Suite-Detailed", "Detailed test report"),
    ("Error-Code-Catalog", "docs/Error-Code-Catalog", "Error code table"),
    ("Tool-Build-Practice", "docs/Tool-Build-Practice", "Tool-building best practices"),
    ("02-Convert-Documents", "playbooks/02-Convert-Documents.md", "Convert playbook"),
    ("01-Deploy-Scaffold", "playbooks/01-Deploy-Scaffold.md", "Deploy playbook"),
    ("03-Audit-Quality", "playbooks/03-Audit-Quality.md", "Audit playbook"),
    ("04-Handle-Duplicates", "playbooks/04-Handle-Duplicates.md", "Duplicates playbook"),
    ("05-Repair-Markdown", "playbooks/05-Repair-Markdown.md", "Repair playbook"),
    ("Tool-Creation-Memory", "Tool-Creation-Memory-v1-03-09-2026-05-05-24.md", "Tool memory"),
    ("Session-Learning-Notes", "Session-Learning-Notes-v1-03-09-2026-05-05-24.md", "Session notes"),
]

SITE_LINKS = [
    ("Website", SITE),
    ("YouTube", "https://www.youtube.com/@satyagrahalawgroup2002"),
    ("Udemy Courses", "https://www.udemy.com/user/anil-b-23/"),
    ("LinkedIn", "https://www.linkedin.com/in/anilsatyagraha/"),
    ("Facebook", "https://www.facebook.com/satyagrahalawgroup"),
    ("Twitter / X", "https://twitter.com/_satyagraha"),
    ("WordPress", "https://satyagrahalawgroup.wordpress.com/"),
    ("Instagram", "https://www.instagram.com/satyagrahalawgroup/"),
    ("Pinterest", "https://in.pinterest.com/satyagrahalawgroup/"),
    ("Tumblr", "https://www.tumblr.com/blog/satyagrahalawgroup"),
    ("SoundCloud", "https://soundcloud.com/satyagrahalawgroup"),
    ("Podomatic", "http://anil-satyagraha.podomatic.com/"),
    ("Newsletter", "https://satyagraha.substack.com/"),
    ("WhatsApp", "https://api.whatsapp.com/send?phone=917095776633"),
]


def tool_root() -> FsPath:
    return FsPath(__file__).resolve().parents[2]


def resolve_wiki_file(root: FsPath | None, hint: str) -> FsPath | None:
    """Resolve a catalog hint to an existing markdown, html, or png file."""
    root = FsPath(root or tool_root())
    hint = hint.replace("\\", "/")
    exact = root / hint
    if exact.is_file():
        return exact
    parent = exact.parent if exact.suffix else (root / hint).parent
    stem = exact.name if not exact.suffix else exact.stem
    if not parent.is_dir():
        parent = root / FsPath(hint).parent
    if parent.is_dir():
        matches = sorted(
            p
            for p in parent.iterdir()
            if p.is_file() and p.name.startswith(stem) and p.suffix.lower() in {".md", ".html", ".png"}
        )
        md = [p for p in matches if p.suffix.lower() == ".md"]
        if md:
            return md[-1]
        html = [p for p in matches if p.suffix.lower() == ".html"]
        if html:
            return html[-1]
        if matches:
            return matches[-1]
    return exact if exact.exists() else None


def href_from(root: FsPath, target: FsPath, *, from_docs: bool, from_playbooks: bool, html: bool = False) -> str:
    try:
        rel = target.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        rel = target.name
    if html:
        html_sib = target.with_suffix(".html")
        if html_sib.is_file():
            rel = html_sib.resolve().relative_to(root.resolve()).as_posix()
    if from_docs:
        if rel == "README.md":
            return "../README.md"
        if rel.startswith("docs/"):
            return rel.split("/", 1)[1]
        return f"../{rel}"
    if from_playbooks:
        if rel == "README.md":
            return "../README.md"
        return f"../{rel}"
    return rel


def related_markdown(*, from_docs: bool = False, from_playbooks: bool = False, root: FsPath | None = None) -> str:
    """Obsidian wiki links plus clickable relative links (GitHub / HTML)."""
    root = FsPath(root or tool_root())
    lines = [
        "<!-- Related documents: Obsidian wiki links AND relative file links -->",
        "<!-- " + " ".join(f"[[{name}]]" for name, _, _ in WIKI_CATALOG) + " -->",
        "",
        "## Related documents",
        "",
    ]
    for name, hint, label in WIKI_CATALOG:
        target = resolve_wiki_file(root, hint)
        href = href_from(root, target, from_docs=from_docs, from_playbooks=from_playbooks) if target else hint
        lines.append(f"- [[{name}]] — [{label}]({href})")
    lines.append("")
    return "\n".join(lines)


def related_html(*, from_docs: bool = True, root: FsPath | None = None) -> str:
    root = FsPath(root or tool_root())
    items = []
    for name, hint, label in WIKI_CATALOG:
        target = resolve_wiki_file(root, hint)
        href = href_from(root, target, from_docs=from_docs, from_playbooks=False, html=True) if target else hint
        items.append(f'<li><a href="{href}">{label}</a> (wiki [[{name}]])</li>')
    return "".join(items)


def site_links_markdown() -> str:
    return " · ".join(f"[{label}]({url})" for label, url in SITE_LINKS)


def site_links_html() -> str:
    return " · ".join(f'<a href="{url}">{label}</a>' for label, url in SITE_LINKS)



_PROTECT_TOKENS = (
    "replace_photocopier",
    "test_lawyer_photocopier_story",
    "test_footer_is_not_duplicated_and_has_no_photocopier",
    "has_no_photocopier",
)


def replace_photocopier(text: str, *, leftover: bool = True) -> str:
    """Rename the old photocopier metaphor to the product name."""
    holders: dict[str, str] = {}
    for i, tok in enumerate(_PROTECT_TOKENS):
        key = f"\x00SLIPPROTECT{i}\x00"
        holders[key] = tok
        text = text.replace(tok, key)
    text = text.replace('"photocopier"', '"\x00SLIPWORD\x00"')
    text = text.replace("'photocopier'", "'\x00SLIPWORD\x00'")
    pairs = (
        ("the photocopier's internals", "the tool's internals"),
        ("The photocopier copies", "The SLIP PDF to Markdown Ingestion Tool copies"),
        ("the photocopier should not", "the SLIP PDF to Markdown Ingestion Tool should not"),
        ("the photocopier contract", "the ingestion contract"),
        ("the photocopier drop zone", "the RAW drop zone"),
        ("including the photocopier drop zone", "including the RAW drop zone"),
        ("Photocopier drop zone", "RAW drop zone"),
        ("Photocopier UX", "SLIP PDF to Markdown Ingestion Tool"),
        ("photocopier UX", "SLIP PDF to Markdown Ingestion Tool"),
        ("a photocopier with a hash register", "a SLIP PDF to Markdown Ingestion Tool with a hash register"),
        ("a photocopier for legal PDFs", "the SLIP PDF to Markdown Ingestion Tool for legal PDFs"),
        ("the photocopier for legal PDFs", "the SLIP PDF to Markdown Ingestion Tool for legal PDFs"),
        ("It is a photocopier", "It is the SLIP PDF to Markdown Ingestion Tool"),
        ("it is a photocopier", "it is the SLIP PDF to Markdown Ingestion Tool"),
        ("publishes a photocopier", "publishes a SLIP PDF to Markdown Ingestion Tool"),
        ("Happy path (photocopier)", "Happy path (ingestion)"),
        ("Photocopier story", "Ingestion story"),
        ("Photocopier copy on the page", "Ingestion copy on the page"),
        ("Photocopier produced a blank", "Ingestion produced a blank"),
        ("for the photocopier:", "for the SLIP PDF to Markdown Ingestion Tool:"),
        ("Photocopier: Drop PDF", "SLIP PDF to Markdown Ingestion Tool: Drop PDF"),
        ("matches the photocopier contract", "matches the ingestion contract"),
        ("Flag extracts the photocopier should not silently bless", "Flag extracts the SLIP PDF to Markdown Ingestion Tool should not silently bless"),
    )
    for old, new in pairs:
        text = text.replace(old, new)
        text = text.replace(old.capitalize(), new) if old[:1].islower() else text
    if leftover:
        text = text.replace("Photocopier", "SLIP PDF to Markdown Ingestion Tool")
        text = text.replace("photocopier", "SLIP PDF to Markdown Ingestion Tool")
    for key, tok in holders.items():
        text = text.replace(key, tok)
    text = text.replace("\x00SLIPWORD\x00", "photocopier")
    return text


def strip_trailing_footers(text: str) -> str:
    """Drop stacked Satyagraha footers (old short footer plus site footer)."""
    markers = (
        "This is a research project at Satyagraha Law Group",
        "Need Legal Help",
        "Founded by Anil B. (Lawyer)",
        "Satyagraha Law Group publishes a photocopier",
        "Satyagraha Law Group publishes a SLIP PDF to Markdown Ingestion Tool",
        "Explore further:",
    )
    text = text.replace("\r\n", "\n")
    while True:
        idx = text.rfind("\n---\n")
        if idx < 0:
            break
        tail = text[idx:]
        if len(tail) > 4000:
            break
        if any(m in tail for m in markers) or "**Satyagraha Law Group**" in tail:
            text = text[:idx].rstrip()
            continue
        break
    for prefix in (
        "Satyagraha Law Group publishes a photocopier",
        "Satyagraha Law Group publishes a SLIP PDF to Markdown Ingestion Tool",
    ):
        i = text.rfind(prefix)
        if i >= 0 and i >= len(text) - 500:
            text = text[:i].rstrip()
    return text.rstrip() + "\n"


def with_single_footer(text: str) -> str:
    """Body plus exactly one canonical footer."""
    return strip_trailing_footers(replace_photocopier(text)) + footer_markdown()

def header_markdown() -> str:
    return "\n".join(
        [
            f"# {ORG}",
            "",
            f"**{PRODUCT}**  ·  {FAMILY}  ·  {TAGLINE}",
            "",
            f"{SANSKRIT}",
            "",
            f"*{RIG_VEDA}*",
            "",
            f"*{ARISTOTLE}*",
            "",
            f"[{SITE}]({SITE})",
            "",
            f"> {DISCLAIMER}",
            "",
            "---",
            "",
        ]
    )


def footer_markdown() -> str:
    """Site index footer used on every documentation and report."""
    return "\n".join(
        [
            "",
            "---",
            "",
            PUBLISH_LINE,
            "",
            f"**{ORG}**  ·  {PRODUCT}  ·  {FAMILY}",
            "",
            FOUNDER_LINE,
            "",
            f"{NEED_HELP} [Click here]({CALENDLY}).",
            "",
            f"{SANSKRIT}",
            "",
            f"*{RIG_VEDA}*",
            "",
            f"*{ARISTOTLE}*",
            "",
            f"> {DISCLAIMER}",
            "",
            f"[{SITE}]({SITE})",
            "",
            "This site is built from **real-world experience helping clients seeking Justice**, "
            "case by case — based on our work involving Legal Research, Drafting, Pleadings, "
            "Representation and beyond.",
            "",
            "Explore further: " + site_links_markdown(),
            "",
            f"Need Legal Help? [Click Here For Next Steps]({CALENDLY})",
            "",
        ]
    )


def header_text() -> str:
    bar = "=" * 68
    return "\n".join(
        [
            bar,
            f"  {ORG}",
            f"  {PRODUCT}  ·  {FAMILY}  ·  {TAGLINE}",
            f"  {SANSKRIT}",
            f"  {RIG_VEDA}",
            f"  {ARISTOTLE}",
            f"  {SITE}",
            bar,
            f"  {DISCLAIMER}",
            bar,
        ]
    )


def footer_text() -> str:
    bar = "=" * 68
    return "\n".join(
        [
            bar,
            f"  {PUBLISH_LINE}",
            f"  {ORG}  ·  {PRODUCT}  ·  {SITE}",
            f"  {FOUNDER_LINE}",
            f"  {NEED_HELP} {CALENDLY}",
            f"  {DISCLAIMER}",
            bar,
        ]
    )


def html_wrap(title: str, body_html: str, *, from_docs: bool = True, root: FsPath | None = None) -> str:
    """White background, black text, Satyagraha header and site footer."""
    related = related_html(from_docs=from_docs, root=root)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — {ORG}</title>
  <style>
    html, body {{ background:#ffffff !important; color:#000000 !important; }}
    body {{ margin:0; font: 17px/1.55 "Palatino Linotype", Palatino, "Times New Roman", serif; }}
    a {{ color:#000000; text-decoration: underline; }}
    header, footer {{ background:#ffffff; color:#000000; border-color:#000000; }}
    header {{ border-bottom: 2px solid #000000; padding: 28px 24px 18px; text-align:center; }}
    footer {{ border-top: 2px solid #000000; padding: 18px 24px 28px; text-align:center; margin-top: 48px; }}
    main {{ max-width: 820px; margin: 0 auto; padding: 28px 24px; background:#ffffff; color:#000000; }}
    h1, h2, h3, p, li, td, th {{ color:#000000; }}
    table {{ width:100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #000000; padding: 8px 10px; text-align:left; }}
    pre, code {{ font-family: Consolas, "Courier New", monospace; color:#000000; background:#ffffff; }}
    pre {{ border: 1px solid #000000; padding: 12px; overflow:auto; }}
    .sanskrit {{ font-size: 1.05rem; }}
    .disclaimer {{ border: 1px solid #000000; padding: 10px 14px; margin: 16px 0; }}
    .founder {{ margin: 12px 0; }}
  </style>
</head>
<body>
<header>
  <div>{ORG}</div>
  <div>{PRODUCT} · {FAMILY} · {TAGLINE}</div>
  <div class="sanskrit">{SANSKRIT}</div>
  <div><em>{RIG_VEDA}</em></div>
  <div><em>{ARISTOTLE}</em></div>
  <div><a href="{SITE}">{SITE}</a></div>
  <div class="disclaimer">{DISCLAIMER}</div>
</header>
<main>
{body_html}
<h2>Related documents</h2>
<ul>{related}</ul>
</main>
<footer>
  <p>{PUBLISH_LINE}</p>
  <div>{ORG} · {PRODUCT} · {FAMILY}</div>
  <p class="founder">{FOUNDER_LINE}</p>
  <p>{NEED_HELP} <a href="{CALENDLY}">Click here</a>.</p>
  <div class="sanskrit">{SANSKRIT}</div>
  <div>{RIG_VEDA}</div>
  <div>{ARISTOTLE}</div>
  <div class="disclaimer">{DISCLAIMER}</div>
  <p>This site is built from real-world experience helping clients seeking Justice, case by case — Legal Research, Drafting, Pleadings, Representation and beyond.</p>
  <p>{site_links_html()}</p>
  <p>Need Legal Help? <a href="{CALENDLY}">Click Here For Next Steps</a></p>
  <div><a href="{SITE}">{SITE}</a></div>
</footer>
</body>
</html>
"""
