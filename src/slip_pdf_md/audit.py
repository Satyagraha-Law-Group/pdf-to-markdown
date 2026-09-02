"""Audit clean Markdown and NEEDS_REVIEW; write a three-word-named report."""

from __future__ import annotations

import re
from pathlib import Path

from slip_pdf_md.naming import REPORT_NAME_RE, three_word_filename
from slip_pdf_md.paths import SlipPaths
from slip_pdf_md.registry import STATUS_DONE, STATUS_PROCESSING, Registry

FRONT_RE = re.compile(r"^---\s*$", re.M)
PAGE_RE = re.compile(r"^## Page\s+\d+", re.M)
HASH_RE = re.compile(r"^source_sha256:\s*[\"']?([0-9a-fA-F]{64})", re.M)


def _flags_for_markdown(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    flags = []
    if not text.lstrip().startswith("---"):
        flags.append("MISSING_FRONT_MATTER")
    if not PAGE_RE.search(text):
        flags.append("NO_PAGE_HEADINGS")
    body = FRONT_RE.split(text, maxsplit=2)
    rest = body[-1] if body else text
    visible = re.sub(r"<!--.*?-->", "", rest, flags=re.S).strip()
    visible = re.sub(r"^## Page\s+\d+\s*", "", visible, flags=re.M).strip()
    if not visible or visible.startswith("_No extractable"):
        flags.append("EMPTY_BODY")
    if "UNRECOVERED TABLE REGION" in text:
        flags.append("UNRECOVERED_TABLE")
    return flags


def run_audit(paths: SlipPaths, registry: Registry | None = None) -> dict:
    findings: list[dict] = []
    for folder, label in ((paths.clean, "clean"), (paths.needs_review, "needs_review")):
        if not folder.is_dir():
            continue
        for md in sorted(folder.glob("*.md")):
            if md.name.endswith(".sidecar.md"):
                continue
            flags = _flags_for_markdown(md)
            findings.append({"path": str(md), "tray": label, "flags": flags})

    if registry is not None:
        for row in registry.all_documents():
            out = row.get("output_path") or ""
            if row["status"] == STATUS_DONE and (not out or not Path(out).exists()):
                findings.append(
                    {
                        "path": out or row["sha256"],
                        "tray": "registry",
                        "flags": ["ORPHAN_DONE"],
                    }
                )
            if row["status"] == STATUS_PROCESSING:
                findings.append(
                    {
                        "path": row["sha256"],
                        "tray": "registry",
                        "flags": ["STALE_PROCESSING"],
                    }
                )

    flagged = [f for f in findings if f["flags"]]
    report_name = three_word_filename("Audit", "Quality", "Report")
    dest_dir = paths.registry_dir if paths.registry_dir.exists() else paths.root
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / report_name
    lines = [
        "# Audit Quality Report",
        "",
        "**Satyagraha Law Group** — PDF to Markdown (SLIP).",
        "",
        f"- files_scanned: {len(findings)}",
        f"- files_flagged: {len(flagged)}",
        f"- clean_tray: `{paths.clean}`",
        f"- review_tray: `{paths.needs_review}`",
        "",
        "## Findings",
        "",
    ]
    if not flagged:
        lines.append("No flags. Clean Markdown tray matches the photocopier contract.")
    else:
        for item in flagged:
            flag_s = ", ".join(item["flags"])
            lines.append(f"- `{item['path']}` ({item['tray']}): {flag_s}")
    lines.append("")
    dest.write_text("\n".join(lines), encoding="utf-8")
    if not REPORT_NAME_RE.match(dest.name):
        raise RuntimeError(f"audit report name failed convention: {dest.name}")
    return {"report": dest, "findings": findings, "flagged": len(flagged)}
