# Product Requirements Specification

**Satyagraha Law Group**  
**Product:** PDF to Markdown  
**Family:** SLIP — Satyagraha Law Group Legal Intelligence Platform  
**Document:** Product-Requirements-Spec-v1-02-09-2026-22-55-00  
**Status:** Approved for Phase 1 (local) and Phase 2 (web) implementation  
**Classification:** Internal product specification — contains no client documents

---

## 1. Problem

Lawyers and clerks at Satyagraha Law Group receive evidence, statutes, reported judgments, and scanned books as PDF. Downstream work (search, quoting, LLM briefing, clause compare) needs **Markdown that a human can trust**.

Existing converters fail the practice in four ways:

1. **Scanned pages become empty files** when the PDF has no text layer.
2. **Legal tables flatten into prose**, destroying schedules, limitation tables, and section lists.
3. **The same book is converted twice** because someone renamed the file. Filename is treated as identity. Disk and attention are wasted; worse, two slightly different Markdown files appear and a lawyer cannot tell which is canonical.
4. **Tools invent cells** or silently drop rows when OCR is unsure. For legal work that is a fabrication.

The product Satyagraha Law Group needs is not "an AI that reads PDFs". It is a **photocopier with a hash register**: Drop PDF → Wait → Open Markdown. Layer 1 is faithful extract. Layer 2 (case briefs, project briefs) is a different product and is out of scope except for keeping the empty folders so the platform stays coherent.

## 2. Users

| Actor | Job to be done | Success looks like |
| --- | --- | --- |
| Lawyer | Drop a brief or a reported judgment and open Markdown without learning Python | Three-step README; no jargon in the happy path |
| Clerk / paralegal | Batch-drop a folder of scans; see duplicates routed, not deleted | `50_90_DUPLICATES` sidecar names the original |
| LLM agent | Follow a playbook against the public GitHub URL and produce the same tree on a new vault | Parameterized SKILL-style playbooks 01–05 |
| Engineer | Swap IBM Docling (or Mistral, Reducto, Document AI) behind the same CLI later | Engine adapter interface; bake-off is future work |

Confidentiality is a user requirement, not an afterthought. Client PDFs do not go to GitHub. The registry stores hashes and filenames, not document bodies, when it can avoid it. The web app binds to localhost by default.

## 3. Product principles

1. **Photocopier UX.** The lawyer does not configure engines. Drop, wait, open.
2. **Hash is identity.** SHA-256 of file bytes. Filename is a label only.
3. **Convert once.** Same PDF, different name = one Markdown. The second drop is a duplicate, not a second conversion.
4. **No AI deletion of duplicates.** Route, sidecar, leave the bytes. A human decides.
5. **Do not invent table cells.** Prefer `UNRECOVERED` callouts over guessed grid text.
6. **Page boundaries are sacred.** Every page is `## Page N`.
7. **Layer 1 vs Layer 2.** This tool writes `20_03_CLEAN_MARKDOWN`. It does not fill `30_04_CASE_BRIEFS` or `40_05_PROJECT_BRIEFS`.
8. **Retries are idempotent.** A `DONE` hash is never converted again by a retry.

## 4. Scope

### 4.1 Phase 1 — local engine and CLI (this sprint's primary code)

A Python package `slip_pdf_md` installed from this repository:

- Commands: `init`, `convert`, `audit`, `doctor`.
- SQLite registry with unique SHA-256.
- Pipeline: PyMuPDF text layer → if empty, Tesseract OCR → tables via `find_tables`, else Tesseract TSV column buckets.
- YAML front matter on every Markdown file.
- `## Page N` body.
- Optional `--repair-citations` (conservative OCR substitutions listed in §7).
- Leader-dot collapse; running headers demoted to HTML comments.
- Duplicate routing into `50_90_DUPLICATES`.
- Status machine: `NEW` / `PROCESSING` / `DONE` / `NEEDS_REVIEW`.
- LLM playbooks 01–05.
- Tests that actually pass (registry, text PDF, table PDF, citations, scaffold, audit filename).

### 4.2 Phase 2 — web app that works (this sprint)

A FastAPI app plus a static drop page:

- `POST /jobs` — upload a PDF.
- Background convert with the **same** engine as the CLI.
- `GET /jobs/{id}` — status + Markdown download URL.
- `GET /health` — liveness.
- README one-liner: `uvicorn web.app:app --reload --host 127.0.0.1 --port 8000`.
- Test for `/health`.

### 4.3 Phase 2b — managed Drive / Docling (design only, not this sprint's code)

Documented in the design and architecture papers, **not implemented**:

- Google Drive (or equivalent) inbound folder watcher.
- Make.com / n8n glue for non-engineer operators.
- IBM Docling, Mistral OCR, Reducto, Google Document AI as **engine adapters** behind the same CLI (`slip-pdf-md convert --engine docling`).
- No fake clients, no stub that pretends Docling ran.

## 5. Non-goals

- Generating case briefs, headnotes, or project briefs (Layer 2).
- Sending client PDFs to a third-party cloud OCR API as the default path.
- Deleting, shredding, or "smart-merging" duplicates.
- Treating filename, path, or "Page 1 title" as document identity.
- Inventing missing table cells, footnotes, or citations.
- Training or fine-tuning a model on client books.
- Renaming the SLIP pipeline folders (`0_01_RAW_PDF` and siblings stay exactly those names).
- Committing `.venv`, `MASTER_MACDONE.md`, client PDFs, or repair dumps to git.

## 6. Folder contract (acceptance)

The tool must honour this tree, created by `init` / `deploy` and already used in production vaults:

| Directory | Writer | Reader |
| --- | --- | --- |
| `0_01_RAW_PDF` | Human drop | `convert` |
| `10_02_READY_FOR_DOCLING` | `convert` on **new** hashes | engine |
| `20_03_CLEAN_MARKDOWN` | engine on success | lawyer, LLM, audit |
| `30_04_CASE_BRIEFS` | not this tool | Layer 2 later |
| `40_05_PROJECT_BRIEFS` | not this tool | Layer 2 later |
| `50_90_DUPLICATES` | `convert` on known hashes | human review |
| `60_90_PROCESSED` | `convert` after success | archive |
| `70_99_NEEDS_REVIEW` | `convert` / `audit` | human + repair playbook |
| `90_00_PROJECT_TOOLING` | deploy, registry | engineers |
| `Convert-PDF-TO-MARKDOWN-01` | this product | git working copy |

A duplicate sidecar must record: duplicate filename, SHA-256, timestamp, and the path of the first successful Markdown (or a clear `PENDING` if the original is still `PROCESSING`).

## 7. Functional requirements

### 7.1 Identity and registry

- Compute SHA-256 over the full file.
- Unique constraint on `sha256`. A second insert of the same hash is a sighting, not a new document.
- Sightings store filename, path, and route (`10_02` or `50_90_DUPLICATES`).
- `DONE` hashes: convert is a no-op except routing the new file into duplicates.
- `PROCESSING` hashes left behind by a crash: convert may resume the same hash, never spawn a second Markdown for it.
- `NEEDS_REVIEW` hashes may be retried explicitly; a successful retry flips status to `DONE` and writes/overwrites Markdown once.

### 7.2 Extraction

- Prefer the PDF text layer (PyMuPDF `get_text`).
- If a page's text layer is empty or whitespace, OCR that page with Tesseract. On Windows, use `C:\Program Files\Tesseract-OCR\tesseract.exe` when present.
- Tables: `page.find_tables()` first; if that yields no usable grid, bucket Tesseract TSV words by Y-row then X-gap into columns.
- If a region looks like a table but cells cannot be recovered, emit an `UNRECOVERED` callout and keep surrounding text. Never fabricate a cell.
- Every page emitted as `## Page N`.
- YAML front matter keys (required): `document_type`, `source_file`, `source_sha256`, `processing_status`, `engine`, `page_count`, `converted_at`.

### 7.3 Cleaning (Layer 1, mechanical)

- Collapse repeated leader dots/dashes used in contents pages.
- Detect running headers/footers (same line, same relative position, ≥3 pages) and wrap them in HTML comments so they do not pollute search.
- Optional `--repair-citations`:
  - `ATR` → `AIR` using a word boundary so **ATTRIBUTE is never changed**
  - `L]` → `LJ`
  - `AIL)` → `All.`
  - `Caleutta` → `Calcutta`
  - `Jnarkhand` → `Jharkhand`
  - `I71-B` → `171-B`
- Do not run a general LLM rewriter over the page. Repair is regex and layout, not "make it nicer".

### 7.4 Audit

- `slip-pdf-md audit` walks `20_03_CLEAN_MARKDOWN` and `70_99_NEEDS_REVIEW`.
- Flags: missing front matter, missing page headings, empty body, duplicate SHA in Markdown vs registry mismatch, UNRECOVERED count.
- Writes a report whose filename follows **Word1-Word2-Word3-vN-DD-MM-YYYY-HH-MI-SS.ext** with exactly three Title-Case words, hyphens only, 24-hour Asia/Calcutta time.

### 7.5 Doctor

- Reports Python version, PyMuPDF import, Tesseract binary, write access to the SLIP tree, and registry reachability.

## 8. Acceptance matrix (from product brainstorm)

| ID | Criterion | Pass |
| --- | --- | --- |
| A1 | Same PDF bytes, different filename, converted once | Registry unique SHA-256; second file in `50_90_DUPLICATES` with sidecar; one Markdown |
| A2 | Filename is not identity | Renaming a raw PDF does not create a new document row |
| A3 | No AI deletion of duplicates | Duplicate bytes remain on disk; tool never unlinks them as a "cleanup" |
| A4 | Empty text layer pages still produce Markdown via OCR when Tesseract is present | `## Page N` with recovered text or an explicit empty/UNRECOVERED note |
| A5 | Tables survive as pipe tables or UNRECOVERED, never silently as prose-only when a grid was detected | Unit test on a generated table PDF |
| A6 | Citation repairs do not touch ATTRIBUTE | Unit test |
| A7 | Drop PDF → Wait → Open Markdown is documented at the top of README | README lawyer section |
| A8 | Layer 2 folders exist and stay empty of tool output | `init` creates them; convert does not write briefs |
| A9 | Retries do not double-convert `DONE` | Registry guard |
| A10 | Web `/health` returns ok | Phase 2 test |
| A11 | Client PDFs and `.venv` are not in git | `.gitignore` + review of commits |
| A12 | Five specification documents exist with the required filenames and were committed before converter code | Git history |

## 9. Engine bake-off (future adapters, same CLI)

Phase 1 ships one engine: **PyMuPDF + Tesseract**. The design requires an adapter interface so later bake-off candidates plug in without changing lawyer UX:

| Candidate | Why it might win | Why it is not default |
| --- | --- | --- |
| IBM Docling | Strong layout / table story for scanned books | Extra runtime; not yet in this sprint |
| Mistral OCR | High-quality OCR API | Cloud, confidentiality review required |
| Reducto | Legal-document marketing, tables | Vendor lock, cloud |
| Google Document AI | Form/table parsers | Cloud, billing, data residency |

Bake-off rule: every adapter must write the **same** front matter shape, the same `## Page N` contract, and honour the registry. The lawyer still drops into `0_01_RAW_PDF`.

## 10. Quality bar for Markdown

A conversion is `DONE` only if:

- Front matter is valid and `source_sha256` matches the registry.
- At least one `## Page N` heading exists, or the file contains a single explicit empty-document notice.
- No fabricated table cells.
- Running headers, if detected, are comments not body copy.

Otherwise status is `NEEDS_REVIEW` and the Markdown (or a failure note) lands in `70_99_NEEDS_REVIEW`.

## 11. Security and confidentiality

- Default web bind: `127.0.0.1`.
- No secrets in the repo. No client extracts in docs.
- Hash registry is a local SQLite file under tooling, gitignored.
- Uploads in Phase 2 stay on local disk.

## 12. Out-of-repo local working copy

The production vault already contains a working converter, a `.venv`, `markdown/` outputs, and `MASTER_MACDONE.md`. Those remain on disk as `legacy/` plus ignored outputs. They are **not** the public product. The public product is this package, these docs, and the playbooks.

## 13. Success

Satyagraha Law Group can clone https://github.com/Satyagraha-Law-Group/pdf-to-markdown, run deploy, drop a PDF, and open Markdown — locally or via the web drop zone — with duplicates routed, hashes unique, and Layer 2 folders waiting for a later tool.
