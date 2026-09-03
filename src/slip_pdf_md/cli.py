"""CLI: init, convert, audit, doctor."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from slip_pdf_md import FAMILY, ORG, PRODUCT_NAME, __version__
from slip_pdf_md.audit import run_audit
from slip_pdf_md.auditcontrol import SessionAudit, collect_sequential_pdfs
from slip_pdf_md.branding import footer_text, header_text
from slip_pdf_md.convert import convert_pdf
from slip_pdf_md.doctor import format_doctor, run_doctor
from slip_pdf_md.engine_choice import prompt_engine
from slip_pdf_md.naming import now_calcutta
from slip_pdf_md.paths import SlipPaths, discover_slip_root
from slip_pdf_md.progress import make_file_progress
from slip_pdf_md.registry import Registry, RegistryCorrupt, backup_path, sha256_file
from slip_pdf_md.runlog import markdown_log_path, write_batch_summary
from slip_pdf_md.scaffold import create_slip_tree
from slip_pdf_md.secrets import load_secrets, write_secret_templates
from slip_pdf_md.sessionlog import format_lawyer_recap, write_session_summary
from slip_pdf_md.verify import verify_markdown, write_report


def _paths(vault: str | None) -> SlipPaths:
    return SlipPaths(discover_slip_root(vault))


def _registry(paths: SlipPaths) -> Registry:
    return Registry(paths.registry_path)


def cmd_init(args: argparse.Namespace) -> int:
    print(header_text())
    paths = create_slip_tree(discover_slip_root(args.vault))
    repo_root = Path(__file__).resolve().parents[2]
    written = write_secret_templates(repo_root)
    write_secret_templates(paths.registry_dir)
    print(f"{ORG}")
    print(f"{PRODUCT_NAME} — scaffold ready at {paths.root}")
    for folder in paths.all_dirs():
        print(f"  {folder}")
    print(f"  secrets_example={written['example']}")
    print("  real keys go in gitignored SECRETS.txt (never commit SECRETS*)")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    vault = args.vault
    paths = None
    if vault or True:
        try:
            paths = _paths(vault)
        except Exception:
            paths = None
    print(header_text())
    report = run_doctor(paths)
    print(format_doctor(report))
    print(footer_text())
    return 0 if report["ok"] else 1


def _in_ready(pdf: Path, paths) -> bool:
    pdf = Path(pdf)
    try:
        pdf.resolve().relative_to(paths.ready.resolve())
        return True
    except ValueError:
        return paths.ready in pdf.parents or pdf.parent == paths.ready


def _in_raw(pdf: Path, paths) -> bool:
    pdf = Path(pdf)
    try:
        pdf.resolve().relative_to(paths.raw.resolve())
        return True
    except ValueError:
        return paths.raw in pdf.parents or pdf.parent == paths.raw


def cmd_convert(args: argparse.Namespace) -> int:
    print(header_text())
    engine_name = prompt_engine(args.engine, force=bool(getattr(args, "force", False)))
    paths = _paths(args.vault)
    load_secrets(tool_root=Path(__file__).resolve().parents[2], vault_root=paths.root)
    paths.root.mkdir(parents=True, exist_ok=True)
    for folder in paths.all_dirs():
        folder.mkdir(parents=True, exist_ok=True)
    registry = _registry(paths)
    if getattr(registry, "restored_from_backup", False):
        print("NOTICE: Document-Hash-Registry sqlite was missing. Restored from the matching .bak.")
    started = now_calcutta()
    try:
        if args.input:
            target = Path(args.input)
            if target.is_file():
                pdfs = [target]
            else:
                pdfs = sorted(target.rglob("*.pdf"))
        else:
            pdfs = collect_sequential_pdfs(paths)
        audit = SessionAudit(paths, engine=engine_name, force=bool(args.force))
        print(f"audit_control={audit.path}")
        results = []
        total = max(len(pdfs), 1)
        for index, pdf in enumerate(pdfs, 1):
            results.append(
                convert_pdf(
                    pdf,
                    paths,
                    registry,
                    engine_name=engine_name,
                    repair_citations_flag=args.repair_citations,
                    move_raw=_in_raw(pdf, paths) or _in_ready(pdf, paths),
                    force=args.force,
                    progress=make_file_progress(index, total),
                    audit=audit,
                )
            )
        audit.close()
    finally:
        registry.close()

    if not results:
        print("No PDF files found to convert.")
        print(footer_text())
        return 0
    summary = write_batch_summary(paths, [r for r in results if r.get("started_at")])
    session = write_session_summary(paths, results, engine=engine_name, started=started)
    done = sum(1 for r in results if r["status"] in {"DONE", "AWAITING_APPROVAL", "APPROVED"} and not r.get("duplicate"))
    dups = sum(1 for r in results if r.get("duplicate"))
    review = sum(1 for r in results if r["status"] == "NEEDS_REVIEW")
    halted = sum(1 for r in results if r.get("status") == "HALTED")
    awaiting = sum(1 for r in results if r.get("status") == "AWAITING_APPROVAL" and not r.get("duplicate"))
    llm = sum((r.get("token_usage") or {}).get("llm_total_tokens") or 0 for r in results)
    md_tok = sum((r.get("token_usage") or {}).get("markdown_tokens_estimate") or 0 for r in results)
    equiv = sum((r.get("token_usage") or {}).get("equivalent_internal_total_tokens") or 0 for r in results)
    print(format_lawyer_recap(results, session))
    print(f"converted={done} duplicates={dups} needs_review={review} halted={halted} awaiting_approval={awaiting}")
    print(f"tokens llm_total={llm} markdown_est={md_tok} equivalent_internal_total={equiv}")
    if summary:
        print(f"batch_summary={summary}")
    print(f"run_log={markdown_log_path(paths)}")
    print(f"session_summary={session}")
    print(f"audit_control={audit.path }")
    for row in results:
        if row.get("duplicate"):
            print(row.get("duplicate_notice") or f"  [DUP] {row.get('output') or row.get('sidecar')}")
            if row.get("routed_to"):
                print(f"       routed_to={row['routed_to']}")
        else:
            print(f"  [{row['status']}] {row.get('output') or row.get('sidecar')}")
            if row.get("moved_to"):
                print(f"       moved_raw={row['moved_to']}")
            if row.get("started_at"):
                print(
                    f"       started={row['started_at']} completed={row['completed_at']} "
                    f"duration_ms={row.get('duration_ms')}"
                )
    print(footer_text())
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    print(header_text())
    result = verify_markdown(
        Path(args.markdown),
        pdf_path=Path(args.pdf) if args.pdf else None,
        companion_path=Path(args.companion) if args.companion else None,
        recall_threshold=args.threshold,
    )
    for check in result["checks"]:
        print(f"[{'PASS' if check['ok'] else 'FAIL'}] {check['name']}: {check['detail']}")
    print("overall:", "PASS" if result["ok"] else "FAIL")
    if args.report:
        write_report(result, Path(args.report))
        print("report:", args.report)
    print(footer_text())
    return 0 if result["ok"] else 1


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



def cmd_registry(args: argparse.Namespace) -> int:
    print(header_text())
    paths = _paths(args.vault)
    action = args.registry_action
    db = paths.registry_path
    if action == "status":
        try:
            registry = Registry(db)
        except RegistryCorrupt as exc:
            print(f"CORRUPT: {exc}")
            print(footer_text())
            return 1
        try:
            h = registry.health()
        finally:
            registry.close()
        print(f"registry: {h['path']}")
        print(f"integrity: {'ok' if h['integrity_ok'] else 'FAIL'}")
        print(f"documents: {h['documents']}")
        print(f"sightings: {h['sightings']}")
        print(f"GUBERNATIO: {h.get('gubernatio', 0)}")
        print(f"backup: {h['backup_path']} exists={h['backup_exists']}")
        if h['restored_from_backup']:
            print("restored_from_backup: yes (live file was missing)")
        print("If this file is deleted, convert restores it from the matching three-word .bak automatically.")
        print("If both copies are gone or corrupt: slip-pdf-md registry rebuild --vault PATH")
        print(footer_text())
        return 0 if h["integrity_ok"] else 1
    if action == "backup":
        registry = Registry(db)
        try:
            dest = registry.backup()
        finally:
            registry.close()
        print(f"backup written: {dest}")
        print(footer_text())
        return 0
    if action == "restore":
        bak = backup_path(db)
        if not bak.exists():
            print(f"No backup at {bak}")
            print("Try: slip-pdf-md registry rebuild --vault PATH")
            print(footer_text())
            return 1
        registry = Registry(db, restore_if_missing=True)
        try:
            ok = registry.restore_from_backup()
            print("restore:", "ok" if ok else "failed")
        finally:
            registry.close()
        print(footer_text())
        return 0 if ok else 1
    if action == "rebuild":
        from slip_pdf_md.registry_rebuild import rebuild_from_vault
        result = rebuild_from_vault(paths)
        for k, v in result.items():
            print(f"{k}: {v}")
        print(footer_text())
        return 0
    if action == "gubernatio":
        registry = Registry(db)
        try:
            rows = registry.gubernatio_rows(limit=50)
            print("GUBERNATIO — Latin: the system of governance, steering, direction, and administration.")
            print("Per-file steering table. documents stays one row per SHA-256.")
            print(f"rows: {registry.count_gubernatio()}")
            from slip_pdf_md.runlog import token_usage_summary
            print("id | seen_at | filename | status | step | token_usage | host | agent | sha256")
            for row in rows:
                sha = (row.get("sha256") or "")[:12]
                tok = token_usage_summary(row.get("token_usage")) or "-"
                print(
                    f"{row.get('id')} | {row.get('seen_at')} | {row.get('filename')} | "
                    f"{row.get('status')} | {row.get('step')} | {tok} | {row.get('host')} | "
                    f"{row.get('agent')} | {sha}"
                )
        finally:
            registry.close()
        print(footer_text())
        return 0
    print("unknown registry action")
    return 2



def cmd_approve(args: argparse.Namespace) -> int:
    print(header_text())
    paths = _paths(args.vault)
    registry = _registry(paths)
    sha = (args.sha256 or "").strip().lower()
    if not sha and args.file:
        target = Path(args.file)
        if target.suffix.lower() == ".pdf" and target.is_file():
            sha = sha256_file(target)
        else:
            # markdown front matter
            text = target.read_text(encoding="utf-8") if target.is_file() else ""
            for line in text.splitlines():
                if line.startswith("source_sha256:"):
                    sha = line.split(":", 1)[1].strip().strip('"').lower()
                    break
    if not sha:
        print("Need --sha256 or --file")
        print(footer_text())
        registry.close()
        return 2
    try:
        row = registry.approve(sha, by=args.by)
    except ValueError as exc:
        print(f"approve failed: {exc}")
        registry.close()
        print(footer_text())
        return 1
    registry.close()
    print(f"APPROVED sha256={row.get('sha256')}")
    print(f"filename={row.get('original_filename')}")
    print(f"markdown={row.get('output_path')}")
    print("GUBERNATIO loop is closed. Downstream may use this file.")
    print(footer_text())
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    print(header_text())
    paths = _paths(args.vault)
    registry = _registry(paths)
    try:
        dest = registry.write_awaiting_approval_report(paths.registry_dir)
        rows = registry.list_by_status("AWAITING_APPROVAL")
    finally:
        registry.close()
    print(f"awaiting_approval={len(rows)}")
    print(f"report={dest}")
    for row in rows:
        print(f"  {row.get('original_filename')}  {row.get('sha256')}")
    print(footer_text())
    return 0


def cmd_test_report(args: argparse.Namespace) -> int:
    """Run the categorized suite and write Test-Suite-Summary plus FAQs."""
    print(header_text())
    from slip_pdf_md.test_report import run_suite_and_write

    paths = None
    dest = Path(args.dest) if args.dest else None
    tests_root = Path(__file__).resolve().parents[2]
    if args.vault:
        paths = _paths(args.vault)
        dest = dest or (paths.tool / "docs" if hasattr(paths, "tool") else paths.registry_dir)
        tests_root = paths.tool if hasattr(paths, "tool") else tests_root
    dest = dest or (tests_root / "docs")
    result = run_suite_and_write(dest, tests_root=tests_root)
    print(f"summary={result.get('summary_md')}")
    print(f"summary_html={result.get('summary_html')}")
    print(f"faqs={result.get('faq_md')}")
    print(f"faqs_html={result.get('faq_html')}")
    print(footer_text())
    return int(result.get("exit_code") or 0)




def cmd_catalog(args: argparse.Namespace) -> int:
    """Publish TEST_CASES / PROCESS_RUNS / ERROR_CODES from the live registry."""
    print(header_text())
    paths = _paths(args.vault)
    registry = _registry(paths)
    dest = Path(args.dest) if args.dest else (paths.tool / "docs")
    dest.mkdir(parents=True, exist_ok=True)
    from slip_pdf_md.catalog import (
        list_error_codes,
        list_process_runs,
        list_test_cases,
        write_error_catalog,
        write_test_reports,
    )
    action = args.catalog_action
    try:
        if action == "errors":
            md, html = write_error_catalog(registry.conn, dest)
            print(f"error_codes={len(list_error_codes(registry.conn))}")
            print(f"markdown={md}")
            print(f"html={html}")
        elif action == "tests":
            out = write_test_reports(registry.conn, dest)
            print(f"test_cases={len(list_test_cases(registry.conn))}")
            print(f"summary={out['summary_md']}")
            print(f"detailed={out['detailed_md']}")
        elif action == "process":
            rows = list_process_runs(registry.conn, limit=50)
            print("day | file | pdf_pages | md_pages | api_key_type | status | approved")
            for row in rows:
                print(
                    f"{row.get('run_day')} | {row.get('filename')} | {row.get('pdf_page_count')} | "
                    f"{row.get('markdown_page_count')} | {row.get('api_key_type')} | "
                    f"{row.get('status')} | {'yes' if row.get('approved') else 'no'}"
                )
            print(f"rows={len(rows)}")
        else:
            print("unknown catalog action")
            return 2
    finally:
        registry.close()
    print(footer_text())
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
    p_cv.add_argument("--engine", default=None, help="pymupdf or mistral. In a terminal the tool always asks 1 Local Tesseract / 2 Mistral AI (including --force). --engine is for scripts only.")
    p_cv.add_argument(
        "--repair-citations",
        action="store_true",
        help="Apply conservative OCR citation repairs (ATR->AIR, not ATTRIBUTE)",
    )
    p_cv.add_argument(
        "--force",
        action="store_true",
        help="Reconvert even if this SHA-256 is already DONE",
    )
    p_cv.set_defaults(func=cmd_convert)

    p_au = sub.add_parser("audit", help="Flag Markdown issues; write a 3-word report")
    p_au.add_argument("--vault", help="SLIP root")
    p_au.set_defaults(func=cmd_audit)

    p_vf = sub.add_parser("verify", help="Check authenticity and accuracy of a converted Markdown file")
    p_vf.add_argument("--markdown", required=True, help="Converted .md")
    p_vf.add_argument("--pdf", help="Source PDF")
    p_vf.add_argument("--companion", help="Optional companion markdown")
    p_vf.add_argument("--threshold", type=float, default=0.90)
    p_vf.add_argument("--report", help="Optional report path")
    p_vf.set_defaults(func=cmd_verify)

    p_reg = sub.add_parser("registry", help="Status, backup, restore, rebuild, or list GUBERNATIO")
    p_reg.add_argument("--vault", help="SLIP root")
    p_reg.add_argument("registry_action", choices=["status", "backup", "restore", "rebuild", "gubernatio"])
    p_reg.set_defaults(func=cmd_registry)

    p_ap = sub.add_parser("approve", help="Lawyer closes the GUBERNATIO loop for a processed file")
    p_ap.add_argument("--vault", help="SLIP root")
    p_ap.add_argument("--sha256", help="Document SHA-256")
    p_ap.add_argument("--file", help="PDF or markdown whose source_sha256 to approve")
    p_ap.add_argument("--by", help="Lawyer name")
    p_ap.set_defaults(func=cmd_approve)

    p_rp = sub.add_parser("report", help="Write the Awaiting Approval Report")
    p_rp.add_argument("--vault", help="SLIP root")
    p_rp.set_defaults(func=cmd_report)

    p_tr = sub.add_parser("test-report", help="Run the categorized suite and write Test-Suite-Summary plus FAQs")
    p_tr.add_argument("--vault", help="SLIP root")
    p_tr.add_argument("--dest", help="Folder for the three-word reports")
    p_tr.set_defaults(func=cmd_test_report)

    p_cat = sub.add_parser("catalog", help="Publish test-run, process-run, and error-code catalogs")
    p_cat.add_argument("--vault", help="SLIP root")
    p_cat.add_argument("--dest", help="Folder for markdown/HTML catalogs")
    p_cat.add_argument("catalog_action", choices=["errors", "tests", "process"])
    p_cat.set_defaults(func=cmd_catalog)

    return parser


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
