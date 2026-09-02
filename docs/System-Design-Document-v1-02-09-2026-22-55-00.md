# System Design Document

**Satyagraha Law Group**  
**Product:** PDF to Markdown  
**Family:** SLIP — Satyagraha Law Group Legal Intelligence Platform  
**Document:** System-Design-Document-v1-02-09-2026-22-55-00  
**Companion:** Product-Requirements-Spec, System-Architecture-Diagram, Process-Workflow-Guide

---

## 1. Two-level architecture

```
Level A — Platform (SLIP folders + SHA-256 registry + playbooks)
    Lawyer drop zone, routing, status, audit, confidentiality boundary.

Level B — Engine (adapter)
    Bytes in, Markdown pages out. PyMuPDF+Tesseract today.
    IBM Docling / Mistral / Reducto / Document AI tomorrow.
```

Level A must not know table-finding internals. Level B must not decide whether a file is a duplicate. Duplicates are a registry concern. Extraction quality is an engine concern. `NEEDS_REVIEW` is the handshake when the engine will not stand behind the page.

This split is what makes the bake-off possible without teaching lawyers a new product.

## 2. Process topology

Three invocation modes share one engine and one registry:

| Mode | Entry | When |
| --- | --- | --- |
| Phase 1 CLI | `slip-pdf-md convert` | Primary; vault already on disk |
| Phase 1 LLM | playbooks 01–05 | Agent-driven install and batch |
| Phase 2 web | `POST /jobs` | Lawyer without a terminal |
| Phase 2b | Drive watcher (design only) | Managed inbound folder |

All modes call `slip_pdf_md.convert.convert_pdf` after `registry.see(path)`.

## 3. Folder contracts

Paths are relative to the SLIP root (the directory that contains `0_01_RAW_PDF`). The tool often lives in `Convert-PDF-TO-MARKDOWN-01` as a child of that root. `paths.discover_slip_root()` walks parents until it finds `0_01_RAW_PDF`, or accepts `--vault`.

| Name | Mutability | Invariants |
| --- | --- | --- |
| `0_01_RAW_PDF` | Human write | Tool may read and, after success, move files to `60_90_PROCESSED`. It does not delete. |
| `10_02_READY_FOR_DOCLING` | Tool write | Only **new** hashes. Copy, do not consume the only bytes until processed. |
| `20_03_CLEAN_MARKDOWN` | Tool write | One Markdown per `DONE` hash. Filename stem from the **first** seen name. |
| `30_04_CASE_BRIEFS` | Reserved | Layer 2. This tool creates the folder and never writes into it. |
| `40_05_PROJECT_BRIEFS` | Reserved | Layer 2. Same. |
| `50_90_DUPLICATES` | Tool write | Copy of the newly seen file plus a `.sidecar.md` (or `.json`) explaining the original hash and the canonical Markdown path. |
| `60_90_PROCESSED` | Tool write | Originals after `DONE` or after duplicate routing. |
| `70_99_NEEDS_REVIEW` | Tool write | Failure notes and/or partial Markdown. |
| `90_00_PROJECT_TOOLING` | Tool write | `registry.sqlite`, optional clone of this product, lawyer guides. |
| `Convert-PDF-TO-MARKDOWN-01` | Git working copy | Public product + local legacy scripts that stay uncommitted. |

Folder names are a public contract. Do not rename them in code or in docs.

## 4. Engine adapter interface

```python
class ConversionResult:
    pages: list[str]          # Markdown bodies without the page heading
    page_count: int
    engine: str               # e.g. "pymupdf+tesseract"
    warnings: list[str]
    unrecovered_tables: int
    needs_review: bool

class EngineAdapter(Protocol):
    name: str
    def convert(self, pdf_path: Path) -> ConversionResult: ...
```

The CLI selects an engine by name (`--engine pymupdf`, default). Unknown names fail `doctor` / `convert` loudly. A future `DoclingAdapter` implements the same protocol and is registered in `engines.REGISTRY`. No adapter may write the registry or move SLIP folders; `convert.py` owns side effects.

### 4.1 PyMuPDF + Tesseract (Phase 1)

Per page:

1. Attempt `page.find_tables()`. If a table converts to Markdown with at least one header and one body row containing real cell text, emit it.
2. Else extract `page.get_text("text")`. If non-empty after normalisation, emit as paragraphs.
3. Else rasterise at 2.5×, threshold, Tesseract `--psm 6`.
4. Else Tesseract TSV (or `image_to_data`) word boxes → bucket by Y (row) then X-gap (columns). If ≥2 columns and ≥3 rows of real text, emit a pipe table.
5. If buckets look tabular (aligned X columns) but cells are empty / below confidence, emit:

```markdown
> **UNRECOVERED TABLE REGION**
> A table-like region was detected on this page but cell text could not be recovered faithfully.
> Surrounding extractable text is preserved. Do not invent missing cells.
```

Windows Tesseract path: `C:\Program Files\Tesseract-OCR\tesseract.exe` if the file exists; also prepend that directory to `PATH`.

### 4.2 Future adapters (not implemented)

Docling would replace steps 1–4 with its document export, then **re-shape** into `## Page N` + the same front matter. Cloud engines require an explicit confidentiality flag; default remains local.

## 5. Registry schema

SQLite file: `{slip_root}/90_00_PROJECT_TOOLING/pdf-to-markdown/registry.sqlite` (gitignored). Created on first `convert` / `init`.

```sql
CREATE TABLE documents (
    sha256            TEXT PRIMARY KEY,
    original_filename TEXT NOT NULL,
    source_path       TEXT,
    status            TEXT NOT NULL CHECK (status IN
                        ('NEW','PROCESSING','DONE','NEEDS_REVIEW')),
    engine            TEXT,
    page_count        INTEGER,
    output_path       TEXT,
    first_seen_at     TEXT NOT NULL,
    converted_at      TEXT,
    last_error        TEXT
);

CREATE TABLE sightings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    sha256     TEXT NOT NULL,
    filename   TEXT NOT NULL,
    seen_at    TEXT NOT NULL,
    routed_to  TEXT NOT NULL,
    FOREIGN KEY (sha256) REFERENCES documents(sha256)
);

CREATE INDEX idx_documents_status ON documents(status);
```

**Uniqueness:** `sha256` is the primary key. `INSERT OR IGNORE` plus a sighting row is the only legal way to record a repeat. Application code also guards: if `status == 'DONE'`, skip convert.

Timestamps are ISO-8601 with Asia/Calcutta offset (`+05:30`).

## 6. Data model (Markdown on disk)

```yaml
---
document_type: legal_pdf
source_file: Indian-Penal-Code-vol-1.pdf
source_sha256: <64 hex>
processing_status: DONE
engine: pymupdf+tesseract
page_count: 412
converted_at: 2026-09-02T22:55:00+05:30
---

## Page 1

...faithful text...

## Page 2

<!-- running header: LEXISNEXIS / 2024 EDITION -->

...
```

`document_type` is `legal_pdf` for this product. Other types are reserved.

Cleaning applied before write:

- Leader collapse: runs of 3+ `.` or `…` or spaced dots used as TOC leaders become a single two-space gap.
- Running header detector: a normalised line that appears at the top or bottom of ≥3 pages becomes an HTML comment on those pages and is removed from the visible body.
- Citation repairs only when `--repair-citations` is set.

## 7. Status machine

```
see(file)
  no row     -> insert NEW, sighting routed 10_02, then PROCESSING, then DONE or NEEDS_REVIEW
  DONE       -> sighting routed 50_90, no convert
  PROCESSING -> resume convert for that hash if output missing; do not insert a second document
  NEEDS_REVIEW -> allowed to retry convert; on success status DONE and Markdown promoted to 20_03
```

Crash safety: `PROCESSING` without an output file is recoverable. `DONE` with a missing output file is treated as `NEEDS_REVIEW` by `audit`, not silently reconverted until a human or `audit --repair-status` says so. Default `convert` still will not double-write a `DONE` hash.

## 8. LLM playbook invocation

Playbooks in `playbooks/` are SKILL-style:

- Goal, required parameters (`{{VAULT}}`, `{{REPO_URL}}`, `{{PYTHON}}`), steps, verification, stop conditions.
- They tell the agent to clone or pull https://github.com/Satyagraha-Law-Group/pdf-to-markdown, run `scripts/deploy.py`, then `slip-pdf-md convert`.
- They never instruct the agent to commit client PDFs, to force-push, or to delete duplicates.
- Any LLM may execute them; they do not depend on a vendor tool-calling schema.

The architecture diagram shows playbook invocation as an arrow from "Agent" to "Level A CLI", not into the engine.

## 9. Web design (Phase 2)

- Process: `uvicorn web.app:app`.
- Upload directory: local `web_jobs/` (gitignored).
- Each job: `{id, sha256, status, md_path, error}`.
- Background task calls the same `convert_pdf`. If a vault is configured via `SLIP_VAULT`, routing uses the full SLIP tree; otherwise the job workspace is a mini-vault created per process.
- `GET /health` → `{ "status": "ok", "product": "PDF to Markdown", "family": "SLIP" }`.
- No authentication in Phase 2 because the bind address is localhost. Binding `0.0.0.0` is a documented risk, not the default.

## 10. Phase 2b (design only)

A Drive watcher would:

1. Poll a designated inbound folder.
2. Download to `0_01_RAW_PDF`.
3. Invoke `slip-pdf-md convert`.
4. Optionally upload `20_03_CLEAN_MARKDOWN` to an outbound folder.

Make.com would HTTP-post the file to Phase 2 `POST /jobs` if a managed host exists. IBM Docling would be `--engine docling`. **None of this is implemented in this sprint.** Documents must not claim it is.

## 11. Security

| Threat | Control |
| --- | --- |
| Client PDF in public git | `.gitignore *.pdf`; docs warn; deploy does not copy PDFs |
| Registry leak | gitignore sqlite; hashes are not the document but still metadata — vault stays private |
| Path traversal in web upload | job ids are UUIDs; saved name is sanitised; convert opens only the saved path |
| SSRF / engine exec | no URL fetch in Phase 1 engine; Tesseract is local binary |
| Cloud OCR surprise | not on the default path |
| Duplicate "cleanup" scripts | product forbids deletion of duplicates in code comments and playbooks |

## 12. Testing design

Fixtures are **generated at test time** with PyMuPDF (tiny one-page text PDF, tiny grid-line table PDF). No book binaries in git.

| Test | Asserts |
| --- | --- |
| `test_registry.py` | second insert of same SHA does not create a second document; sighting recorded |
| `test_convert_text.py` | front matter, `## Page 1`, payload text |
| `test_convert_table.py` | pipe table or UNRECOVERED callout; never empty silence |
| `test_citations.py` | ATR→AIR, ATTRIBUTE untouched, remaining patterns |
| `test_deploy_folders.py` | all ten SLIP directories exist after `create_slip_tree` |
| `test_audit_report.py` | report name matches three-word convention |
| `test_web_health.py` | `/health` is 200 and JSON `status=ok` |

## 13. Packaging

- `src/slip_pdf_md` via setuptools.
- Console scripts `slip-pdf-md` and `pdf-to-markdown`.
- `scripts/deploy.py` is a thin vault bootstrapper that imports `slip_pdf_md.scaffold` when installed, or sys.path-injects `src/` when run from a clone.
- CI: GitHub Actions pytest on Python 3.11 and 3.12.

## 14. Local legacy

`legacy/convert_pdfs.py` is the reference implementation (PyMuPDF + pytesseract + find_tables + TSV buckets) that this package improves. It remains in tree for diffability. It is not the public CLI.
