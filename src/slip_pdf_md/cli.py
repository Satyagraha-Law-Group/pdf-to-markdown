"""CLI: init, convert, audit, doctor."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from slip_pdf_md import FAMILY, ORG, PRODUCT_NAME, __version__
from slip_pdf_md.audit import run_audit
from slip_pdf_md.convert import convert_pdf, convert_vault
from slip_pdf_md.runlog import write_batch_summary
from slip_pdf_md.doctor import format_doctor, run_doctor
from slip_pdf_md.paths import SlipPaths, discover_slip_root
from slip_pdf_md.registry import Registry
from slip_pdf_md.scaffold import create_slip_tree


def _paths(vault: str | None) -> SlipPaths:
    return SlipPaths(discover_slip_root(vault))


def _registry(paths: SlipPaths) -> Registry:
    return Registry(paths.registry_path)


def cmd_init(args: argparse.Namespace) -> int:
    paths = create_slip_tree(discover_slip_root(args.vault))
    print(f"{ORG}")
    print(f"{PRODUCT_NAME} — scaffold ready at {paths.root}")
    for folder in paths.all_dirs():
        print(f"  {folder}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    vault = args.vault
    paths = None
    if vault or True:
        try:
            paths = _paths(vault)
        except Exception:
            paths = None
    report = run_doctor(paths)
    print(format_doctor(report))
    return 0 if report["ok"] else 1


def cmd_convert(args: argparse.Namespace) -> int:
    paths = _paths(args.vault)
    paths.root.mkdir(parents=True, exist_ok=True)
    for folder in paths.all_dirs():
        folder.mkdir(parents=True, exist_ok=True)
    registry = _registry(paths)
    try:
        if args.input:
            target = Path(args.input)
            if target.is_file():
                results = [
                    convert_pdf(
                        target,
                        paths,
                        registry,
                        engine_name=args.engine,
                        repair_citations_flag=args.repair_citations,
                        move_raw=False,
                    )
                ]
            else:
                # treat as a drop folder without requiring it to be 0_01_RAW_PDF
                pdfs = sorted(target.rglob("*.pdf"))
                results = [
                    convert_pdf(
                        pdf,
                        paths,
                        registry,
                        engine_name=args.engine,
                        repair_citations_flag=args.repair_citations,
                        move_raw=False,
                    )
                    for pdf in pdfs
                ]
        else:
            results = convert_vault(
                paths,
                registry,
                engine_name=args.engine,
                repair_citations_flag=args.repair_citations,
            )
    finally:
        registry.close()

    if not results:
        print("No PDF files found to convert.")
        return 0
    summary = write_batch_summary(paths, [r for r in results if r.get("started_at")])
    done = sum(1 for r in results if r["status"] == "DONE" and not r.get("duplicate"))
    dups = sum(1 for r in results if r.get("duplicate"))
    review = sum(1 for r in results if r["status"] == "NEEDS_REVIEW")
    llm = sum((r.get("token_usage") or {}).get("llm_total_tokens") or 0 for r in results)
    md_tok = sum((r.get("token_usage") or {}).get("markdown_tokens_estimate") or 0 for r in results)
    equiv = sum((r.get("token_usage") or {}).get("equivalent_internal_total_tokens") or 0 for r in results)
    print(f"{ORG} — {PRODUCT_NAME}")
    print(f"converted={done} duplicates={dups} needs_review={review}")
    print(
        f"tokens llm_total={llm} markdown_est={md_tok} equivalent_internal_total={equiv}"
    )
    if summary:
        print(f"batch_summary={summary}")
    print(f"run_log={paths.registry_dir / 'logs' / 'Conversion-Run-Log.md'}")
    for row in results:
        mark = "DUP" if row.get("duplicate") else row["status"]
        print(f"  [{mark}] {row.get('output') or row.get('sidecar')}")
        if row.get("started_at"):
            print(
                f"       started={row['started_at']} completed={row['completed_at']} "
                f"duration_ms={row.get('duration_ms')}"
            )
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    paths = _paths(args.vault)
    registry = _registry(paths)
    try:
        result = run_audit(paths, registry)
    finally:
        registry.close()
    print(f"audit report: {result['report']}")
    print(f"flagged: {result['flagged']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="slip-pdf-md",
        description=f"{ORG} — {PRODUCT_NAME} ({FAMILY})",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create the ten SLIP folders")
    p_init.add_argument("--vault", help="SLIP root or parent vault path")
    p_init.set_defaults(func=cmd_init)

    p_doc = sub.add_parser("doctor", help="Check Python, PyMuPDF, Tesseract, folders")
    p_doc.add_argument("--vault", help="SLIP root")
    p_doc.set_defaults(func=cmd_doctor)

    p_cv = sub.add_parser("convert", help="Hash, route, convert PDFs to Markdown")
    p_cv.add_argument("--vault", help="SLIP root containing 0_01_RAW_PDF")
    p_cv.add_argument("--input", help="Optional file or folder instead of 0_01_RAW_PDF")
    p_cv.add_argument("--engine", default="pymupdf", help="Engine adapter name")
    p_cv.add_argument(
        "--repair-citations",
        action="store_true",
        help="Apply conservative OCR citation repairs (ATR->AIR, not ATTRIBUTE)",
    )
    p_cv.set_defaults(func=cmd_convert)

    p_au = sub.add_parser("audit", help="Flag Markdown issues; write a 3-word report")
    p_au.add_argument("--vault", help="SLIP root")
    p_au.set_defaults(func=cmd_audit)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
