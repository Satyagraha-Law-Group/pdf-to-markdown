# Satyagraha Law Group

**PDF to Markdown**  ·  SLIP  ·  Legal Research  ·  Practitioner-Scholar

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

[https://www.satyagraha.com](https://www.satyagraha.com)

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

---
<!-- Related documents: Obsidian wiki links AND GitHub relative links -->
<!-- [[README]] [[Slip-Markdown-Glossary]] [[Mistral-Engine-Guide]] [[Tool-Creation-Memory]] -->

## Related documents

- [[README]] — [Product overview](README.md)
- [[Slip-Markdown-Glossary]] — [Glossary](docs/Slip-Markdown-Glossary-v1-03-09-2026-08-35-00.md)
- [[Mistral-Engine-Guide]] — [Lawyer user guide](docs/Mistral-Engine-Guide-v1-03-09-2026-04-39-31.md)
- [[Tool-Creation-Memory]] — [Tool-folder memory](Tool-Creation-Memory-v1-03-09-2026-05-05-24.md)

# Session Learning Notes

Research project at Satyagraha Law Group. Not legal advice. Not a solicitation.

This is the **session-specific** memory file. Stamp is first-created time (`v1-03-09-2026-05-05-24`). Do not rename it on later writes. Prefer this file over stuffing the assistant's internal memory.

## User

- Name: Anil B
- Addresses the assistant as Spock
- Windows account: SATYAGRAHA
- Computer: DESKTOP-IG57K1N
- Organization: Satyagraha Law Group
- GitHub: anilsatyagraha / Satyagraha-Law-Group
- Vault: `D:\satyagraha\VAULT\Satyagraha Law Group\SLIP_DOCUMENT_PROCESSING`
- Filename rule: `Word1-Word2-Word3-vN-DD-MM-YYYY-HH-MI-SS.ext`
- No Git commit or push until local verification and explicit approval
- Finished products with tests, not partials ("boil the ocean")

## Tool creation session (02–03 Sep 2026)

- Built PDF to Markdown (SLIP) at Convert-PDF-TO-MARKDOWN-01, public repo Satyagraha-Law-Group/pdf-to-markdown
- Identity is SHA-256 of PDF bytes, not filename
- Local engine: PyMuPDF + Tesseract; optional MistralAI OCR
- Secrets live in gitignored SECRETS.txt; convert prompts 1 local / 2 Mistral
- Sequential convert: leftover READY first, then RAW; MOVE RAW → READY dated Stem folder before OCR
- Split at READY if over 100 pages or 100 MB; merge markdown; delete parts; original to `60_90_PROCESSED/YYYY-MM-DD/Stem/Stem.pdf`
- **GUBERNATIO** (03 Sep 2026): Latin, *the system of governance, steering, direction, and administration*. Per-file steering table in the registry sqlite. Written after hash (including DONE) and when convert finishes. `documents` stays one row per hash so multiple agents/devices do not clog identity.
- Happy-path flowchart: `docs/Convert-Pipeline-Flowchart-v1-03-09-2026-06-48-52.png` (white background, black type, black borders)
- Glossary: `docs/Slip-Markdown-Glossary-v1-03-09-2026-08-35-00.md`
- **GUBERNATIO-first + Mistral key lease (03 Sep 2026, layer one):** After SHA-256, GUBERNATIO is the DONE gate; registry is identity/secondary. Same Mistral key cannot dual-run. Sentinel filename Anil confirmed: `SLG-pdf_to_md_file_naming_convention.text` beside the sqlite. Fingerprint of the key only. TTL 15 minutes so a crashed job cannot stuck the next lawyer. Local Tesseract does not lease. Google Drive shared-folder sync is layer two / later. Git still untouched.
- **Human in the loop (03 Sep 2026):** convert status is AWAITING_APPROVAL. GUBERNATIO closes only on lawyer `approve`. Remote API fingerprint + provider placeholder. Git still untouched.
- **Test suite (03 Sep 2026):** categorized pytest with TC numbers, Test-Suite-Summary and Slip-Product-Faqs in md+html. Git still untouched.
- Git still untouched pending Anil's approval

## Files processed in this session

- Arbitration PDF SHA-256 `6c777a9c2976b8343c9b5d4a64b6426e5eab410755c4a22de2acf25538de31e7` (56 pages)
- Local Tesseract reconvert: companion recall 99.07%
- Mistral converts: companion recall 100%, 0 pipe tables, DONE in ~11–12 seconds

## Related

- [[README]]
- [[Slip-Markdown-Glossary]]
- [[Tool-Creation-Memory]]
- [[Mistral-Engine-Guide]]

---

**Satyagraha Law Group**  ·  PDF to Markdown  ·  SLIP

आ नो भद्राः क्रतवो यन्तु विश्वतः  ·  Let noble thoughts come to us from every side. — Rig Veda

The law is reason, free from passion.

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

[https://www.satyagraha.com](https://www.satyagraha.com)

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
