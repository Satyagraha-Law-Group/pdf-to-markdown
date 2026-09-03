"""Generic authenticity and accuracy checks for a converted Markdown file."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from slip_pdf_md.branding import footer_markdown, header_markdown
from slip_pdf_md.fidelity import alnum_tokens, score_markdown_against_pdf, token_recall
from slip_pdf_md.registry import sha256_file

TOKEN_RE = re.compile(r"[A-Za-z0-9]{2,}")


def _front_matter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    meta = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta


def verify_markdown(
    markdown_path: Path,
    *,
    pdf_path: Path | None = None,
    companion_path: Path | None = None,
    recall_threshold: float = 0.90,
) -> dict:
    markdown_path = Path(markdown_path)
    text = markdown_path.read_text(encoding="utf-8", errors="replace")
    meta = _front_matter(text)
    checks = []
    words = re.findall(r"[A-Za-z0-9']+", text)
    pages_md = text.count("## Page ")
    pipe_rows = sum(1 for ln in text.splitlines() if ln.strip().startswith("| ") and "---" not in ln)

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    add("markdown_exists", markdown_path.is_file() and markdown_path.stat().st_size > 0, f"{markdown_path.stat().st_size} bytes")
    add("has_front_matter", bool(meta), ",".join(meta) or "missing")
    add("has_page_headings", pages_md > 0, f"## Page count={pages_md}")
    add("has_words", len(words) >= 20, f"words={len(words)}")
    add("not_all_tables", pipe_rows < max(50, len(words) // 3), f"pipe_rows={pipe_rows}")

    if pdf_path and Path(pdf_path).is_file():
        sha = sha256_file(pdf_path)
        declared = meta.get("source_sha256", "")
        add("sha256_matches_front_matter", not declared or declared == sha, "ok" if declared == sha else f"declared={declared[:12]} file={sha[:12]}")
        fidelity = score_markdown_against_pdf(pdf_path, text, threshold=recall_threshold)
        add(
            "sample_page_ocr_recall",
            fidelity["passed"],
            f"recall={fidelity['overall_recall']} threshold={recall_threshold}",
        )
        try:
            import fitz
            pdf_pages = fitz.open(pdf_path).page_count
        except Exception:
            pdf_pages = 0
        if pdf_pages:
            add("page_count_vs_pdf", pages_md == pdf_pages or abs(pages_md - pdf_pages) <= 1, f"md={pages_md} pdf={pdf_pages}")
    if companion_path and Path(companion_path).is_file():
        companion = Path(companion_path).read_text(encoding="utf-8", errors="replace")
        rec = token_recall(companion, text)
        add("companion_token_recall", rec >= recall_threshold, f"recall={rec:.4f}")

    ok = all(c["ok"] for c in checks)
    return {
        "ok": ok,
        "markdown": str(markdown_path),
        "pdf": str(pdf_path) if pdf_path else None,
        "checks": checks,
        "words": len(words),
        "pages": pages_md,
        "pipe_rows": pipe_rows,
        "unique_alnum": len(alnum_tokens(text)),
    }


def write_report(result: dict, dest: Path) -> Path:
    lines = [
        header_markdown(),
        "# Markdown Accuracy Check",
        "",
        f"- markdown: `{result['markdown']}`",
        f"- pdf: `{result.get('pdf')}`",
        f"- verdict: **{'PASS' if result['ok'] else 'FAIL'}**",
        f"- words: {result['words']}",
        f"- pages: {result['pages']}",
        "",
        "| check | result | detail |",
        "| --- | --- | --- |",
    ]
    for c in result["checks"]:
        lines.append(f"| {c['name']} | {'PASS' if c['ok'] else 'FAIL'} | {c['detail']} |")
    lines += ["", footer_markdown()]
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify authenticity and accuracy of SLIP Markdown")
    p.add_argument("--markdown", required=True, help="Converted .md path")
    p.add_argument("--pdf", help="Source PDF for SHA and sample OCR recall")
    p.add_argument("--companion", help="Optional high-quality companion .md")
    p.add_argument("--threshold", type=float, default=0.90)
    p.add_argument("--report", help="Optional report path")
    args = p.parse_args(argv)
    result = verify_markdown(
        Path(args.markdown),
        pdf_path=Path(args.pdf) if args.pdf else None,
        companion_path=Path(args.companion) if args.companion else None,
        recall_threshold=args.threshold,
    )
    for c in result["checks"]:
        print(f"[{'PASS' if c['ok'] else 'FAIL'}] {c['name']}: {c['detail']}")
    print("overall:", "PASS" if result["ok"] else "FAIL")
    if args.report:
        write_report(result, Path(args.report))
        print("report:", args.report)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
