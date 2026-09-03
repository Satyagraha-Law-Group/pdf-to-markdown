# Satyagraha Law Group

**PDF to Markdown**  ·  SLIP  ·  Legal Research  ·  Practitioner-Scholar

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

[https://www.satyagraha.com](https://www.satyagraha.com)

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

---

<!-- Related documents: Obsidian wiki links AND GitHub relative links -->

<!-- [[README]] [[Slip-Markdown-Glossary]] [[Mistral-Engine-Guide]] [[Process-Workflow-Guide]] -->

## Related documents

- [[README]] — [Product overview](README.md)
- [[Slip-Markdown-Glossary]] — [Glossary](docs/Slip-Markdown-Glossary-v1-03-09-2026-08-35-00.md)
- [[Mistral-Engine-Guide]] — [Lawyer user guide](docs/Mistral-Engine-Guide-v1-03-09-2026-04-39-31.md)
- [[Process-Workflow-Guide]] — [Workflow](docs/Process-Workflow-Guide-v1-02-09-2026-22-55-00.md)

# Tool Creation Memory

Satyagraha Law Group research project. Not legal advice. Not a solicitation.

This is the **tool-folder / global** memory file. Stamp is first-created time (`v1-03-09-2026-05-05-24`). Do not rename it on later writes. Prefer this file over stuffing the assistant's internal memory.

## Standing rules

- Commit only after local tests and Anil’s explicit approval
- Do not rename pipeline folders (`0_01_RAW_PDF`, `10_02_READY_FOR_DOCLING`, `20_03_CLEAN_MARKDOWN`, `50_90_DUPLICATES`, `60_90_PROCESSED`, …)
- Generated artifacts use Title-Case three-word hyphenated names: `Word1-Word2-Word3-vN-DD-MM-YYYY-HH-MI-SS.ext`
- GitHub `README.md`, Python source, `SECRETS*`, and `*.pdf.sidecar.md` stay as-is
- Never invent statutory table cells
- Privileged papers stay on the local engine
- Never commit `SECRETS`, `SECRETS.txt`, or `SECRETS-*`
- Before convert (including `--force`), ask Anil: 1 Local Tesseract or 2 Mistral AI
- CopyToBox/CopyFromBox cannot reach `D:\satyagraha\VAULT`; use a Downloads staging folder then Python copy
- PowerShell strips `$` in inline python; write `.py` files instead

## Architecture

- CLI: `slip-pdf-md init | doctor | convert | verify | audit | registry`
- Engines: `pymupdf` (default, local), `mistral` (uploads)
- Registry sqlite: `90_00_PROJECT_TOOLING/pdf-to-markdown/Document-Hash-Registry-vN-….sqlite` plus sibling `.bak`
- `documents`: one row per SHA-256 (identity). Do not clog it.
- **GUBERNATIO**: proper Latin noun meaning *the system of governance, steering, direction, and administration*. Per-file steering table (filename, host, agent, step, registry-like fields). **Entry gate after SHA-256.** If GUBERNATIO says DONE, park duplicate; update `documents` second. `slip-pdf-md registry gubernatio`
- **Human in the loop:** convert writes `AWAITING_APPROVAL` (processed, markdown staged). Only `slip-pdf-md approve` writes `APPROVED` and closes GUBERNATIO. Legacy `DONE` counts as closed. `slip-pdf-md report` lists waiting files.
- **Remote API keys:** never store a raw key. Fingerprint + `api_provider` (mistral, docling, google, claude, hermes, reducto). Same fingerprint exclusive; different keys parallel.
- **Mistral key lease**: same API key cannot convert in two places at once. Store SHA-256 fingerprint only. Sentinel next to sqlite: exact name `SLG-pdf_to_md_file_naming_convention.text` (zero-byte exclusive create). TTL 15 minutes (`SLIP_KEY_LEASE_SECONDS` in tests). Expired RUNNING is free. Local Tesseract takes no lease. HALT does not move RAW. Release on success and NEEDS_REVIEW (release must not mark the file DONE).
- Split at READY: 100 pages or 100 MB. Convert parts, merge markdown, delete parts, original to `60_90_PROCESSED/YYYY-MM-DD/Stem/Stem.pdf`
- Logs: Conversion-Run-Log, Conversion-Runs-Journal, Session-Convert-Summary, Audit-Control-Session
- Fidelity gate: sample-page OCR recall vs markdown, ~90%
- Branding: Rig Veda line and Aristotle tag from satyagraha.com, plus research disclaimer
- HTML guides: white background, black text, black borders
- **Test suite:** pytest markers smoke/unit/functionality/integration/system/uat/security/integrity/regression/performance. `slip-pdf-md test-report` writes Test-Suite-Summary and Slip-Product-Faqs (md+html, three-word names).

## Memory split

- This file: tool-global standing rules
- `Session-Learning-Notes-v1-03-09-2026-05-05-24.md`: session-specific
- Assistant internal memory: short pointers only. If it is clogged, read these two files.

## Related

- [[README]]
- [[Slip-Markdown-Glossary]]
- [[System-Design-Document]]
- [[Process-Workflow-Guide]]


## 03 Sep 2026 12:13 IST — token_usage column, Satyagraha site footer, wiki user guide

- `documents.token_usage` and `"GUBERNATIO".token_usage` store JSON for each PDF-to-markdown convert (llm_*, markdown_tokens_estimate, equivalent_internal_*, mistral_pages_processed). Live DBs ALTER on open. Also YAML front matter, Conversion-Run-Log, session summary, `slip-pdf-md registry gubernatio`, and the awaiting-approval report.
- Documentation/report footer now includes the public site index (https://github.com/anilsatyagraha/satyagraha-website/blob/main/index.md): founder line, Calendly, channels, plus Rig Veda / Aristotle / research disclaimer.
- Lawyer user guide hub (living stamp): `docs/Lawyer-User-Guide-v1-03-09-2026-12-13-51.md` and `.html`. All related files use Obsidian wiki links `[[Name]]` plus relative hrefs. Integrity check `check_wiki_graph` PASS.
- Pytest: 75 passed (table extraction still ignored). Git still untouched.

## 03 Sep 2026 12:30 IST — test-run catalog, process metrics, error codes

- Document-Hash-Registry sqlite now holds TEST_CASES, TEST_RUNS, TEST_RESULTS, PROCESS_RUNS, and ERROR_CODES next to GUBERNATIO. Future tests upsert TEST_CASES first (stable TC-XXX-NNN). Pytest sessionfinish writes TEST_RUNS/TEST_RESULTS and generates Test-Suite-Summary plus Test-Suite-Detailed from the tables.
- PROCESS_RUNS is the file-level source of truth: run_day, filename, pdf_page_count, markdown_page_count, api_key_type (local_tesseract or mistral), status, approved. Written on convert and on lawyer approve.
- ERROR_CODES seeded SLIP-E-001..022 classified HIGH/MEDIUM/LOW with message and suggested resolution. Living publish: docs/Error-Code-Catalog-v1-03-09-2026-12-25-29.md/.html. CLI: slip-pdf-md catalog errors|tests|process.
- Tool-Build-Practice-v1-03-09-2026-12-25-29.md is the reusable best-practice note for future Satyagraha tools. Lawyer user guide wiki-links the new catalogs. Pytest 80 passed. Git untouched.

## 03-09-2026 — product name and single footer

- 2026-09-03T13:39:22+05:30. Human-facing name is **SLIP PDF to Markdown Ingestion Tool** (never photocopier). `test_lawyer_photocopier_story` keeps that pytest id.
- Canonical footer is once: publish line, then site footer (founder, Calendly, Rig Veda, Aristotle, disclaimer, satyagraha.com, channels). Stacked old+new footers stripped.
- Legal extracts under `markdown/` do not carry the product footer.
- Git still untouched.


---

**Satyagraha Law Group**  ·  PDF to Markdown  ·  SLIP

आ नो भद्राः क्रतवो यन्तु विश्वतः  ·  Let noble thoughts come to us from every side. — Rig Veda

The law is reason, free from passion. ~Aristotle

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

[https://www.satyagraha.com](https://www.satyagraha.com)
