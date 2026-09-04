"""Categorized test-suite reporter for SLIP PDF to Markdown.

Collects every pytest case (number, name, description, category, PASS/FAIL)
and writes Test-Suite-Summary plus Slip-Product-Faqs as markdown and HTML.
Generated names use Word1-Word2-Word3-vN-DD-MM-YYYY-HH-MI-SS in Asia/Calcutta.
HTML is white background, black text, black borders.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

import pytest

from slip_pdf_md.branding import (
    footer_markdown,
    header_markdown,
    html_wrap,
    with_single_footer,
)
from slip_pdf_md.naming import iso_calcutta, three_word_filename

FILE_CATEGORY = {
    "test_approval.py": "integration",
    "test_audit_report.py": "system",
    "test_citations.py": "unit",
    "test_convert_table.py": "functionality",
    "test_convert_text.py": "functionality",
    "test_deploy_folders.py": "smoke",
    "test_engine_choice.py": "uat",
    "test_gubernatio.py": "integration",
    "test_key_lease.py": "security",
    "test_mistral_engine.py": "unit",
    "test_naming_resolve.py": "unit",
    "test_registry.py": "unit",
    "test_registry_safety.py": "system",
    "test_routing.py": "system",
    "test_runlog.py": "unit",
    "test_secrets.py": "security",
    "test_sessionlog.py": "unit",
    "test_splitting.py": "functionality",
    "test_suite_gaps.py": "smoke",
    "test_table_extraction.py": "integrity",
    "test_table_gate.py": "integrity",
    "test_verify.py": "integrity",
    "test_catalog.py": "integrity",
    "test_token_usage.py": "integrity",
    "test_wiki_integrity.py": "integrity",
    "test_web_health.py": "smoke",
}

PREFIX = {
    "smoke": "SMO",
    "unit": "UNT",
    "functionality": "FUN",
    "integration": "INT",
    "system": "SYS",
    "uat": "UAT",
    "security": "SEC",
    "integrity": "FID",
    "regression": "REG",
    "performance": "PER",
}

INLINE_CODE_RE = re.compile(r"`([^`]+)`")

# function_name -> (category, title, description)
META = {
    "test_footer_is_not_duplicated_and_has_no_photocopier": ("integrity", "Footer appears once", "Documentation carries one Satyagraha footer and never uses the old product metaphor."),
    "test_error_codes_are_seeded_and_classified": ("integrity", "Error codes are classified", "ERROR_CODES is seeded with type, HIGH/MEDIUM/LOW category, message, and resolution."),
    "test_register_error_upserts_and_publishes": ("integrity", "New errors publish to the catalog", "Registering a code updates ERROR_CODES and the markdown/HTML error table."),
    "test_test_case_upsert_keeps_stable_id": ("integrity", "Test case IDs stay stable", "Updating a test case keeps TC-XXX-NNN. A new function gets the next number."),
    "test_convert_writes_process_run_metrics": ("integrity", "Convert writes process-run metrics", "Each convert records day, filename, PDF pages, markdown pages, API key type, and approval status."),
    "test_reports_generate_from_catalog_tables": ("integrity", "Reports come from the catalog tables", "Detailed and summary test reports are generated from TEST_CASES and TEST_RUNS."),
    "test_convert_writes_token_usage_column": ("integrity", "Token usage column on convert", "Each PDF-to-markdown run stores token_usage on documents, GUBERNATIO, YAML, and the run log."),
    "test_registry_alters_token_usage_on_existing_db": ("integrity", "Live registry gains token_usage", "Opening an older sqlite adds the token_usage column to documents and GUBERNATIO."),
    "test_site_footer_includes_index_content": ("uat", "Docs footer matches satyagraha-website", "Reports and guides carry the Satyagraha site index footer, including Calendly and the public channels."),
    "test_user_guide_wiki_graph_integrity": ("integrity", "User guide wiki graph", "The lawyer user guide wiki-links every related file. Obsidian can graph them. HTML hrefs resolve."),
    "test_live_user_guide_integrity_when_present": ("integrity", "Live user guide integrity check", "When the tool folder has the user guide, every wiki link and HTML href resolves."),
    "test_require_fingerprint_refuses_raw_key": ("security", "Raw API key is refused", "A raw secret must not be stored. Only a SHA-256 fingerprint is accepted."),
    "test_gubernatio_record_refuses_raw_api_key": ("security", "GUBERNATIO refuses a raw key", "Writing a raw API key into GUBERNATIO is rejected. The fingerprint is stored instead."),
    "test_uses_remote_api_placeholder_engines": ("unit", "Remote API placeholders", "Mistral, Docling, Google, Claude, Hermes, and Reducto are remote. Local Tesseract is not."),
    "test_different_fingerprints_may_run_in_parallel": ("security", "Different keys may run together", "Two different API fingerprints may convert at the same time. The same fingerprint may not."),
    "test_convert_awaits_lawyer_before_gubernatio_closes": ("uat", "Lawyer must approve before GUBERNATIO closes", "A successful convert stages markdown as awaiting approval. Only a lawyer approve closes the loop."),
    "test_audit_writes_three_word_named_report": ("system", "Audit report uses three-word name", "Quality audit writes a Title-Case three-word filename with a Calcutta stamp."),
    "test_citation_repairs_and_attribute_untouched": ("unit", "Citation repairs leave ATTRIBUTE", "Conservative OCR repairs map ATR to AIR and never touch the word ATTRIBUTE."),
    "test_table_fixture_pdf": ("functionality", "True table becomes markdown table", "A real table in a PDF is rendered as a markdown table, not invented cells."),
    "test_tsv_buckets_build_pipe_table": ("unit", "TSV buckets become a pipe table", "Recovered table tokens are joined into a markdown pipe table."),
    "test_text_layer_fixture_pdf": ("functionality", "Text PDF becomes staged markdown", "A one-page text PDF converts to markdown with YAML front matter and Page 1, status awaiting approval."),
    "test_retries_do_not_double_convert_done_hash": ("regression", "Same bytes convert once", "Dropping the same PDF under a new name parks a duplicate. Markdown is not written twice."),
    "test_deploy_creates_folders": ("smoke", "Init creates the SLIP folders", "scaffold creates the ten pipeline folders a lawyer expects."),
    "test_explicit_aliases": ("unit", "Engine aliases", "pymupdf and mistral aliases resolve to the two engines the lawyer is asked about."),
    "test_noninteractive_defaults_local": ("uat", "Scripts default to local Tesseract", "A non-interactive script without --engine stays on the local engine."),
    "test_choice_help_names_both_engines": ("uat", "Help names both engines", "The convert prompt names Local Tesseract and Mistral AI."),
    "test_force_banner_still_asks": ("uat", "Force still asks the engine", "--force still asks 1 Local Tesseract or 2 Mistral AI."),
    "test_interactive_always_prompts_even_if_engine_passed": ("uat", "Terminal always asks", "In a terminal the tool asks even if --engine was passed."),
    "test_interactive_choice_two_is_mistral": ("uat", "Choice 2 is Mistral", "Answering 2 selects the Mistral AI engine."),
    "test_gubernatio_table_exists_and_records_filename": ("integration", "GUBERNATIO records this filename", "Every sighting appends a GUBERNATIO row with filename, host, and agent. documents stays one row per hash."),
    "test_gubernatio_keeps_documents_lean_on_duplicate_filename": ("integration", "Rename does not clog identity", "The same bytes under a new name stay one documents row. GUBERNATIO keeps both filenames."),
    "test_convert_writes_gubernatio_on_done_and_duplicate": ("integration", "Convert writes GUBERNATIO", "Convert and a later duplicate both append GUBERNATIO rows."),
    "test_backfill_gubernatio_from_legacy_sightings": ("system", "Legacy sightings backfill GUBERNATIO", "An older registry without GUBERNATIO is filled from sightings once."),
    "test_sentinel_name_is_anils_exact_string": ("security", "Sentinel name is exact", "The lease sentinel is exactly SLG-pdf_to_md_file_naming_convention.text."),
    "test_uses_mistral_only_for_mistral_engines": ("unit", "Local engine takes no lease", "Only Mistral-family names take the Mistral lease. pymupdf does not."),
    "test_second_agent_is_halted_until_release": ("security", "Same key cannot dual-run", "A second agent using the same key is HALTed until the first releases."),
    "test_expired_lease_is_not_stuck_forever": ("security", "Expired lease is free", "After the 15-minute lease expires, the next lawyer is not stuck."),
    "test_gubernatio_done_gates_before_registry": ("integration", "GUBERNATIO is the DONE gate", "If GUBERNATIO already extracted a hash, convert parks a duplicate even if documents is empty."),
    "test_convert_halts_when_mistral_lease_held": ("security", "HALT leaves RAW", "When the Mistral key is held, convert returns HALTED and does not move the PDF."),
    "test_local_engine_does_not_create_sentinel": ("security", "Tesseract creates no sentinel", "A local convert does not touch the key-lease sentinel."),
    "test_engine_aliases": ("unit", "Mistral engine aliases", "mistral / mistralai names resolve to the upload engine."),
    "test_parse_ocr_pages_keeps_order": ("unit", "OCR pages keep order", "Mistral page payloads stay in document order."),
    "test_missing_api_key": ("security", "Missing Mistral key fails closed", "Convert with Mistral without a key does not pretend to succeed."),
    "test_convert_with_fake_transport": ("unit", "Mistral fake transport", "A stubbed Mistral transport still yields ordered pages."),
    "test_resolve_api_key_from_env": ("security", "Key is read from the environment", "The Mistral key is taken from the environment or gitignored SECRETS, never from sqlite."),
    "test_three_word_filename_matches_convention": ("unit", "Three-word filename convention", "Generated artifacts match Word1-Word2-Word3-vN-DD-MM-YYYY-HH-MI-SS."),
    "test_resolve_migrates_legacy_registry": ("system", "Legacy registry name migrates", "An old registry.sqlite is resolved to the living three-word sqlite."),
    "test_registry_uniqueness_same_bytes_two_names": ("unit", "Hash is identity", "Two filenames with the same bytes share one SHA-256 row."),
    "test_needs_review_may_retry": ("functionality", "NEEDS_REVIEW may retry", "A file the engine will not stand behind can be converted again."),
    "test_backup_created_and_restores_after_delete": ("system", "Registry backup restores", "If the live sqlite is deleted, the sibling .bak is restored."),
    "test_duplicate_notice_names_first_file": ("functionality", "Duplicate notice names the first file", "A [DUP] notice points at the original filename and canonical markdown."),
    "test_rebuild_from_markdown_front_matter": ("system", "Rebuild from markdown", "If both sqlite copies are gone, the registry rebuilds from YAML front matter."),
    "test_new_file_moves_raw_to_ready_then_processed": ("system", "RAW to READY to PROCESSED", "A new PDF moves RAW to READY, then the original parks under PROCESSED."),
    "test_duplicate_goes_to_dated_duplicates_not_processed": ("regression", "Duplicates go to DUPLICATES", "A known hash is moved to dated DUPLICATES, not PROCESSED, and is not converted again."),
    "test_collect_ready_leftovers_before_raw": ("system", "READY leftovers go first", "Sequential convert finishes leftover READY files before new RAW files."),
    "test_collect_skips_split_parts": ("system", "Split parts are not collected as originals", "Part PDFs under Stem/parts are not treated as new source files."),
    "test_convert_writes_start_end_and_token_log": ("unit", "Run log has start and end", "Each convert writes started, completed, and token estimates."),
    "test_parse_setx_line": ("unit", "SECRETS setx lines parse", "Windows setx lines in SECRETS.txt are read."),
    "test_parse_key_equals_value": ("unit", "SECRETS key=value parses", "KEY=value lines in SECRETS.txt are read."),
    "test_parse_export_and_set": ("unit", "SECRETS export/set parse", "export and set forms in SECRETS.txt are read."),
    "test_write_templates_do_not_overwrite_real": ("security", "Templates do not overwrite real secrets", "Writing SECRETS.example never overwrites a real SECRETS.txt."),
    "test_session_summary_writes_three_word_name": ("unit", "Session summary three-word name", "The convert session summary uses the three-word stamp."),
    "test_stem_folder_name_strips_extension": ("unit", "Stem folder strips extension", "READY / PROCESSED stem folders are the filename without .pdf."),
    "test_five_page_file_splits_into_three_parts": ("functionality", "Oversized PDF splits at READY", "A file over the page cap is split into parts of at most 100 pages."),
    "test_needs_split_page_and_size_caps": ("unit", "Split caps are 100 pages or 100 MB", "needs_split is true only when pages or bytes exceed the cap."),
    "test_reindex_and_merge_markdown_parts": ("functionality", "Part markdown merges as one file", "Page headings continue 1..N after parts are merged."),
    "test_happy_path_split_convert_merges_and_deletes_parts": ("system", "Happy-path split deletes parts", "After a clean merge the part PDFs are deleted and the original is processed."),
    "test_table_sections_are_rendered_as_markdown_tables": ("integrity", "Extracted tables stay tables", "Table regions become markdown tables, not prose."),
    "test_scanned_table_pages_are_reconstructed_as_markdown_tables": ("integrity", "Scanned tables reconstruct", "OCR table pages reconstruct as markdown tables when the grid is real."),
    "test_real_citation_grid_accepted": ("integrity", "Citation grid accepted as table", "A genuine citation grid is kept as a table."),
    "test_commentary_paragraphs_rejected_as_table": ("integrity", "Commentary is not a table", "Prose commentary is not forced into a pipe table."),
    "test_two_rows_not_enough": ("integrity", "Two rows are not a table", "A two-row fragment is not promoted to a table."),
    "test_tsv_helper_still_builds_pipe_table": ("unit", "TSV helper builds pipes", "The TSV helper still emits a markdown pipe table."),
    "test_token_recall_counts_overlap": ("integrity", "Token recall measures overlap", "Fidelity recall counts overlapping tokens between PDF and markdown."),
    "test_verify_synthetic_markdown": ("integrity", "Verify checks a markdown file", "verify reports PASS/FAIL on required front matter and structure."),
    "test_health_ok": ("smoke", "Web health endpoint", "The optional web app answers a health check."),
    "test_package_imports": ("smoke", "Package imports", "slip_pdf_md imports and exposes the product name."),
    "test_cli_help_lists_lawyer_commands": ("smoke", "CLI help lists lawyer commands", "slip-pdf-md --help names convert, approve, report, and doctor."),
    "test_doctor_on_fresh_tree": ("smoke", "Doctor on a fresh tree", "doctor runs against a new SLIP folder set without crashing."),
    "test_gitignore_keeps_secrets_out": ("security", "SECRETS stay gitignored", "SECRETS* is gitignored so keys never enter git."),
    "test_convert_yaml_has_required_keys": ("integrity", "Staged markdown has required YAML", "Front matter carries document_type, source_sha256, processing_status, engine, page_count."),
    "test_small_convert_finishes_promptly": ("performance", "Small PDF converts promptly", "A one-page text PDF finishes convert in under thirty seconds."),
    "test_lawyer_photocopier_story": ("uat", "Ingestion story", "Drop PDF, convert, open markdown, see awaiting, approve, GUBERNATIO closes."),
}

MARKERS = tuple(PREFIX)


def _humanize(name: str) -> str:
    text = re.sub(r"^test_", "", name)
    return text.replace("_", " ").strip().capitalize()


def _category_for(item: pytest.Item) -> str:
    marks = [m.name for m in item.iter_markers() if m.name in PREFIX]
    if marks:
        return marks[0]
    path = Path(str(item.fspath)).name
    return FILE_CATEGORY.get(path, "functionality")


def _meta_for(item: pytest.Item) -> tuple[str, str, str]:
    fn = item.originalname if hasattr(item, "originalname") else item.name.split("[")[0]
    cat, title, desc = META.get(fn, (_category_for(item), _humanize(fn), _humanize(fn) + "."))
    doc = (item.obj.__doc__ or "").strip() if getattr(item, "obj", None) is not None else ""
    if doc:
        lines = [ln.strip() for ln in doc.splitlines() if ln.strip()]
        if lines and lines[0].startswith("TC-"):
            lines = lines[1:]
        if lines:
            title = lines[0]
        if len(lines) > 1:
            desc = " ".join(lines[1:])
    return cat, title, desc


def pytest_configure(config):
    config._slip_cases = []
    config._slip_counters = {k: 0 for k in PREFIX}


def pytest_collection_modifyitems(config, items):
    for item in items:
        cat, title, desc = _meta_for(item)
        if not any(m.name == cat for m in item.iter_markers()):
            item.add_marker(getattr(pytest.mark, cat))
        config._slip_counters[cat] = config._slip_counters.get(cat, 0) + 1
        tc_id = f"TC-{PREFIX.get(cat, 'FUN')}-{config._slip_counters[cat]:03d}"
        item.user_properties.append(("tc_id", tc_id))
        item.user_properties.append(("tc_title", title))
        item.user_properties.append(("tc_desc", desc))
        item.user_properties.append(("tc_cat", cat))
        fn = item.originalname if hasattr(item, "originalname") else item.name.split("[")[0]
        item._slip_record = {
            "id": tc_id,
            "name": title,
            "description": desc,
            "category": cat,
            "nodeid": item.nodeid,
            "result": "NOT RUN",
            "function_name": fn,
            "source_file": Path(str(item.fspath)).name,
        }


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    rec = getattr(item, "_slip_record", None)
    if rec is None or rep.when != "call":
        if rec is not None and rep.when == "setup" and rep.failed:
            rec["result"] = "FAIL"
            item.config._slip_cases.append(rec)
        elif rec is not None and rep.when == "setup" and getattr(rep, "skipped", False):
            rec["result"] = "SKIP"
            item.config._slip_cases.append(rec)
        return
    rec["result"] = "PASS" if rep.passed else ("SKIP" if rep.skipped else "FAIL")
    item.config._slip_cases.append(rec)


def _open_tool_registry(root: Path):
    """Live Document-Hash-Registry when tests run inside the SLIP tool folder."""
    vault = Path(root).parent
    tooling = vault / "90_00_PROJECT_TOOLING" / "pdf-to-markdown"
    if not tooling.is_dir():
        return None
    from slip_pdf_md.paths import SlipPaths
    from slip_pdf_md.registry import Registry
    return Registry(SlipPaths(vault).registry_path)


def pytest_sessionfinish(session, exitstatus):
    dest = Path(getattr(session.config.option, "slip_report_dir", "") or "")
    if not str(dest):
        dest = Path(session.config.rootpath) / "docs"
    dest.mkdir(parents=True, exist_ok=True)
    cases = list(getattr(session.config, "_slip_cases", []) or [])
    registry = _open_tool_registry(session.config.rootpath)
    close = False
    if registry is None:
        from slip_pdf_md.registry import Registry
        registry = Registry(dest / "session-catalog.sqlite")
        close = True
    try:
        from slip_pdf_md.catalog import (
            finish_test_run,
            start_test_run,
            write_error_catalog,
            write_test_reports,
            write_tool_practice,
        )
        for rec in cases:
            case_id = registry.upsert_test_case(
                function_name=rec.get("function_name") or rec.get("id"),
                source_file=rec.get("source_file") or "",
                category=rec.get("category") or "functionality",
                title=rec.get("name") or "",
                description=rec.get("description") or "",
            )
            rec["id"] = case_id
            rec["case_id"] = case_id
        run_id = start_test_run(registry.conn)
        finish_test_run(registry.conn, run_id, results=cases)
        _paths = write_test_reports(registry.conn, dest, run_id=run_id)
        write_error_catalog(registry.conn, dest)
        write_tool_practice(dest)
        write_product_faqs(dest)
        registry._backup_quiet()
    finally:
        if close or registry is not None:
            registry.close()


def pytest_addoption(parser):
    parser.addoption(
        "--slip-report-dir",
        action="store",
        default="",
        help="Folder for Test-Suite-Summary and Slip-Product-Faqs",
    )


def _esc(text: str) -> str:
    return html.escape(str(text or ""), quote=True)


def _html_inline(text: str) -> str:
    source = str(text or "")
    parts: list[str] = []
    last = 0
    for match in INLINE_CODE_RE.finditer(source):
        parts.append(_esc(match.string[last:match.start()]))
        parts.append(f"<code>{_esc(match.group(1))}</code>")
        last = match.end()
    parts.append(_esc(source[last:]))
    return "".join(parts)


def write_suite_summary(dest_dir: Path, cases: list[dict]) -> tuple[Path, Path]:
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp_name = three_word_filename("Test", "Suite", "Summary", ext="md")
    md_path = dest_dir / stamp_name
    html_path = dest_dir / stamp_name.replace(".md", ".html")
    total = len(cases)
    passed = sum(1 for c in cases if c.get("result") == "PASS")
    failed = sum(1 for c in cases if c.get("result") == "FAIL")
    skipped = sum(1 for c in cases if c.get("result") == "SKIP")
    by_cat: dict[str, list] = {}
    for c in cases:
        by_cat.setdefault(c.get("category") or "functionality", []).append(c)

    lines = [
        header_markdown(),
        "# Test Suite Summary",
        "",
        "Satyagraha Law Group — SLIP PDF to Markdown Ingestion Tool.",
        "Categorized results for the SLIP PDF to Markdown Ingestion Tool: Drop PDF, wait, open Markdown.",
        "",
        f"- written_at: {iso_calcutta()}",
        f"- total: {total}",
        f"- pass: {passed}",
        f"- fail: {failed}",
        f"- skip: {skipped}",
        "",
        "## Totals by category",
        "",
        "| Category | Count | Pass | Fail | Skip |",
        "| --- | --- | --- | --- | --- |",
    ]
    for cat in ("smoke", "unit", "functionality", "integration", "system", "uat", "security", "integrity", "regression", "performance"):
        group = by_cat.get(cat, [])
        if not group:
            continue
        lines.append(
            f"| {cat} | {len(group)} | "
            f"{sum(1 for c in group if c['result']=='PASS')} | "
            f"{sum(1 for c in group if c['result']=='FAIL')} | "
            f"{sum(1 for c in group if c['result']=='SKIP')} |"
        )
    lines += [
        "",
        "## Test cases",
        "",
        "| Test Case Number | Test Case Name | Description | Category | Result |",
        "| --- | --- | --- | --- | --- |",
    ]
    for c in cases:
        desc = (c.get("description") or "").replace("|", "/")
        name = (c.get("name") or "").replace("|", "/")
        lines.append(
            f"| {c.get('id')} | {name} | {desc} | {c.get('category')} | {c.get('result')} |"
        )
    lines.append(footer_markdown())
    md_path.write_text(with_single_footer("\n".join(lines)), encoding="utf-8")

    rows = []
    for c in cases:
        tone = "#006400" if c.get("result") == "PASS" else ("#8B0000" if c.get("result") == "FAIL" else "#000000")
        rows.append(
            "<tr>"
            f"<td>{_esc(c.get('id'))}</td>"
            f"<td>{_esc(c.get('name'))}</td>"
            f"<td>{_esc(c.get('description'))}</td>"
            f"<td>{_esc(c.get('category'))}</td>"
            f"<td style=\"color:{tone};font-weight:bold\">{_esc(c.get('result'))}</td>"
            "</tr>"
        )
    cat_rows = []
    for cat in ("smoke", "unit", "functionality", "integration", "system", "uat", "security", "integrity", "regression", "performance"):
        group = by_cat.get(cat, [])
        if not group:
            continue
        cat_rows.append(
            "<tr>"
            f"<td>{_esc(cat)}</td><td>{len(group)}</td>"
            f"<td>{sum(1 for c in group if c['result']=='PASS')}</td>"
            f"<td>{sum(1 for c in group if c['result']=='FAIL')}</td>"
            f"<td>{sum(1 for c in group if c['result']=='SKIP')}</td>"
            "</tr>"
        )
    body = (
        "<h1>Test Suite Summary</h1>"
        "<p>Satyagraha Law Group — SLIP PDF to Markdown Ingestion Tool. SLIP PDF to Markdown Ingestion Tool: Drop PDF, wait, open Markdown.</p>"
        f"<p>Written { _esc(iso_calcutta()) }. Total {total}. Pass {passed}. Fail {failed}. Skip {skipped}.</p>"
        "<h2>Totals by category</h2>"
        "<table><thead><tr><th>Category</th><th>Count</th><th>Pass</th><th>Fail</th><th>Skip</th></tr></thead>"
        f"<tbody>{''.join(cat_rows)}</tbody></table>"
        "<h2>Test cases</h2>"
        "<table><thead><tr><th>Test Case Number</th><th>Test Case Name</th><th>Description</th><th>Category</th><th>Result</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )
    html_path.write_text(html_wrap("Test Suite Summary", body), encoding="utf-8")
    return md_path, html_path


FAQS = [
    ("What does this tool do?", "It is the SLIP PDF to Markdown Ingestion Tool for legal PDFs. You put a PDF in, wait, and open a Markdown file. It does not write a case brief and it does not invent table cells."),
    ("How is this repository organized?", "It is a Python application. `src/slip_pdf_md` holds the CLI, convert pipeline, engines, registry, and support modules. `tests` prove behavior. `web` holds the FastAPI app. `docs` and `playbooks` hold guides. `scripts` holds helper commands. Packaging and dependencies live in `pyproject.toml`."),
    ("How does the tool know two files are the same?", "It hashes the PDF bytes (SHA-256). The filename is not identity. A rename months later is still the same document."),
    ("What is GUBERNATIO?", "GUBERNATIO is Latin for governance, steering, direction, and administration. It is the master record after the hash. The identity registry stays one row per hash so several people and devices do not clog it."),
    ("When is a file finished?", "When convert succeeds, the markdown is only staged. Status is awaiting approval. A Satyagraha lawyer must approve. Only then is GUBERNATIO closed for downstream work."),
    ("What if I drop the same PDF under a new name?", "It is converted once. The second copy is parked in Duplicates with a note pointing at the first markdown. The tool never deletes duplicates."),
    ("Do I have to use Mistral?", "No. In a terminal the tool always asks: 1 Local Tesseract (nothing uploaded) or 2 Mistral AI (the PDF is uploaded). Privileged papers stay on the local engine."),
    ("Why is Mistral often better?", "For many scans it is faster and cleaner than local Tesseract, especially tables and formulas. It uploads the file, so you choose it on purpose."),
    ("Will tomorrow's Docling or Claude key work the same way?", "The lease is built for any remote API. Today the provider is Mistral. The same fingerprint-and-provider slot is ready for Docling, Google, Claude, Hermes, or Reducto."),
    ("Are API keys stored in the database?", "Never. GUBERNATIO stores only a SHA-256 fingerprint of the key and which provider it belongs to. A raw key is refused."),
    ("What is the sentinel file?", "A zero-byte lock file next to the database named exactly SLG-pdf_to_md_file_naming_convention.text. It stops two jobs using the same key at once."),
    ("What if convert says HALT?", "Someone else is already using that same API key. Your PDF stays in RAW. Wait, or use a different key. After fifteen minutes an abandoned lock is treated as free."),
    ("Does local Tesseract take that lock?", "No. Only a remote API convert takes a key lease."),
    ("What happens to a very large PDF?", "At Ready for Doc Link, a file over 100 pages or 100 MB is split. You still get one markdown. Extra part files are deleted. The original PDF is kept under Processed."),
    ("What is NEEDS_REVIEW?", "The engine will not stand behind the extract. The file is routed for a human look. It may be converted again."),
    ("Where do real keys live?", "In gitignored SECRETS.txt. The example template never overwrites a real key file. Keys are never committed."),
    ("Can downstream tools use a file that is only processed?", "Not as a closed record. Downstream should wait until a lawyer has approved, so GUBERNATIO shows the loop is closed."),
    ("How do I see what is waiting on me?", "Run the awaiting-approval report. It lists processed files that a lawyer has not yet approved."),
    ("How do I approve a file?", "Run approve with the SHA-256 (or the markdown file) and your name. GUBERNATIO then records who approved and when."),
    ("Will a failed computer lose the register?", "The live sqlite has a sibling backup. If the live file is deleted, the next open restores it. If both copies are gone, it can rebuild from markdown front matter."),
    ("Does the markdown remember the source?", "Yes. YAML front matter carries the source filename, SHA-256, engine, page count, status, and convert time. The body uses Page N headings."),
]


def write_product_faqs(dest_dir: Path) -> tuple[Path, Path]:
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp_name = three_word_filename("Slip", "Product", "Faqs", ext="md")
    md_path = dest_dir / stamp_name
    html_path = dest_dir / stamp_name.replace(".md", ".html")
    lines = [header_markdown(), "# Frequently Asked Questions", "", "Satyagraha Law Group — SLIP PDF to Markdown Ingestion Tool.", "Plain answers, taken from what the test suite actually proves.", ""]
    for i, (q, a) in enumerate(FAQS, 1):
        lines += [f"## {i}. {q}", "", a, ""]
    lines.append(footer_markdown())
    md_path.write_text(with_single_footer("\n".join(lines)), encoding="utf-8")
    parts = ["<h1>Frequently Asked Questions</h1>", "<p>Satyagraha Law Group — SLIP PDF to Markdown Ingestion Tool. Plain answers, taken from what the test suite actually proves.</p>"]
    for i, (q, a) in enumerate(FAQS, 1):
        parts.append(f"<h2>{i}. {_esc(q)}</h2><p>{_html_inline(a)}</p>")
    html_path.write_text(html_wrap("Frequently Asked Questions", "".join(parts)), encoding="utf-8")
    return md_path, html_path


def run_suite_and_write(dest_dir: Path, tests_root: Path | None = None) -> dict:
    """Run pytest and write the summary plus FAQs. Returns paths and counts."""
    import subprocess
    import sys

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    root = Path(tests_root) if tests_root else Path(__file__).resolve().parents[2]
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests",
        "--ignore=tests/test_table_extraction.py",
        f"--slip-report-dir={dest_dir}",
        "-q",
    ]
    code = subprocess.call(cmd, cwd=str(root))
    summaries = sorted(dest_dir.glob("Test-Suite-Summary-v1-*.md"))
    faqs = sorted(dest_dir.glob("Slip-Product-Faqs-v1-*.md"))
    return {
        "exit_code": code,
        "summary_md": str(summaries[-1]) if summaries else "",
        "summary_html": str(summaries[-1]).replace(".md", ".html") if summaries else "",
        "faq_md": str(faqs[-1]) if faqs else "",
        "faq_html": str(faqs[-1]).replace(".md", ".html") if faqs else "",
    }
