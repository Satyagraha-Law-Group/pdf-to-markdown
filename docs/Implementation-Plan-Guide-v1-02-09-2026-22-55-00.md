# Implementation Plan Guide

**Satyagraha Law Group**  
**Product:** PDF to Markdown  
**Family:** SLIP — Satyagraha Law Group Legal Intelligence Platform  
**Document:** Implementation-Plan-Guide-v1-02-09-2026-22-55-00  
**Method:** sequenced work, each slice shippable, documents committed before converter code

---

## 0. Order of git history (non-negotiable)

The public repository https://github.com/Satyagraha-Law-Group/pdf-to-markdown is built in four commits. Documents land first because Satyagraha Law Group treats written contracts as prior to scripts.

1. **Docs + README + LICENSE + .gitignore + empty SLIP scaffold**
2. **Phase 1 local engine + tests + LLM playbooks**
3. **Bootstrap** (`scripts/deploy.py`, `deploy.ps1`, `deploy.sh`, GitHub Actions)
4. **Phase 2 web app that works** (FastAPI + static HTML + `/health` test)

Do not force-push `main`. Do not rewrite this order.

---

## 1. Phase 1 — local LLM + CLI (this sprint)

### 1.1 Preconditions

- Windows working copy at  
  `D:\satyagraha\VAULT\Satyagraha Law Group\SLIP_DOCUMENT_PROCESSING\Convert-PDF-TO-MARKDOWN-01`
- Existing `convert_pdfs.py` is a **reference**. Move it to `legacy/` if the name collides. Do not delete it.
- Do not commit `.venv`, `markdown/`, `MASTER_MACDONE.md`, client PDFs, `md_repair_work/`.
- Tesseract installed at `C:\Program Files\Tesseract-OCR\tesseract.exe` when OCR is required.
- GitHub repo already created (empty, public). User `anilsatyagraha` can push to the org.

### 1.2 Work sequence

| Step | Work | Done when |
| --- | --- | --- |
| P1.0 | `.gitignore`, MIT LICENSE, lawyer-first README, five docs, ten `.gitkeep` dirs | Commit 1 on `main` |
| P1.1 | Package layout `src/slip_pdf_md` with `paths`, `naming`, `registry`, `engines.base` | Imports succeed |
| P1.2 | Port `legacy/convert_pdfs.py` into `engines/pymupdf_engine.py` with UNRECOVERED callouts | Table + OCR paths unit-tested |
| P1.3 | Cleaning: leaders, running headers, `--repair-citations` | Citation tests pass, ATTRIBUTE untouched |
| P1.4 | `convert.py` orchestration: hash, route, status, front matter, `## Page N` | Duplicate PDF converted once |
| P1.5 | CLI: `init convert audit doctor` | `slip-pdf-md doctor` prints Tesseract and folders |
| P1.6 | Playbooks 01–05, SKILL-style, parameterized, any LLM | Agent can deploy from GitHub URL |
| P1.7 | pytest suite (fixtures generated in-test) | `pytest` green on 3.11+ |
| P1.8 | Commit 2, push `main` | SHA recorded |

### 1.3 Implementation notes for P1.2 (engine)

Reuse, do not regress:

- `find_tables()` then `to_markdown()`.
- Tesseract `image_to_data` / TSV buckets with X-gap ≈ 25 px at 2.5× raster.
- Noise filter from the reference script, but **do not** treat the substring `oil` as universal noise in a general-purpose product (too many false positives on real words). Keep publisher-header heuristics milder; running-header detection replaces blunt keyword drops where possible.
- Empty document notice rather than a silent zero-byte file.

### 1.4 Implementation notes for P1.4 (orchestration)

- Discover SLIP root from `--vault`, else `SLIP_VAULT` env, else walk parents for `0_01_RAW_PDF`.
- Copy new PDFs into `10_02_READY_FOR_DOCLING` using the original filename if free, else `{stem}-{sha12}{suffix}`.
- Write Markdown to `20_03_CLEAN_MARKDOWN/{stem}.md`. If that name exists for a **different** hash, suffix with `-{sha12}`.
- On duplicate hash: copy inbound file to `50_90_DUPLICATES/` and write `{filename}.sidecar.md`.
- After `DONE`, move (not delete) the RAW file into `60_90_PROCESSED/`.
- On `NEEDS_REVIEW`, write a note plus any partial Markdown into `70_99_NEEDS_REVIEW/`.

### 1.5 Tests that must pass before Commit 2 is pushed

1. Registry uniqueness (same SHA, two filenames).
2. Text-layer fixture PDF (PyMuPDF-generated).
3. Table fixture PDF (grid lines + cell text).
4. Citation regex including ATTRIBUTE negative case.
5. Deploy/init creates all ten folders.
6. Audit writes a three-word-named report matching  
   `^[A-Z][A-Za-z0-9]*-[A-Z][A-Za-z0-9]*-[A-Z][A-Za-z0-9]*-v\d+-\d{2}-\d{2}-\d{4}-\d{2}-\d{2}-\d{2}\.[A-Za-z0-9]+$`

---

## 2. Phase 2 — web (this sprint, after CLI)

| Step | Work | Done when |
| --- | --- | --- |
| P2.0 | `web/app.py` FastAPI, `web/static/index.html` drop zone | Photocopier copy on the page |
| P2.1 | `POST /jobs` saves PDF, background convert, job id UUID | curl can upload |
| P2.2 | `GET /jobs/{id}` JSON with status and download path | Polling works |
| P2.3 | Markdown download route | Browser downloads `.md` |
| P2.4 | `GET /health` | Test green |
| P2.5 | README uvicorn one-liner | Present |
| P2.6 | Commit 4, push | SHA recorded |

Phase 2 uses the Phase 1 engine. It must not reimplement OCR.

Bootstrap (Commit 3) sits **between** Phase 1 and Phase 2 in git history even though it is used by both: `scripts/deploy.py` plus GitHub Actions `pytest` on 3.11 and 3.12.

---

## 3. Phase 2b — managed Drive (not this sprint's code)

Scheduled after this repository is in daily use.

| Step | Work | Explicitly out of this sprint |
| --- | --- | --- |
| P2b.1 | Google Drive inbound watcher writing into `0_01_RAW_PDF` | No Drive client ships here |
| P2b.2 | Make.com / n8n posting to `POST /jobs` | No scenario JSON ships here |
| P2b.3 | IBM Docling adapter behind `--engine docling` | Interface only, no fake adapter |
| P2b.4 | Confidentiality review for any cloud OCR | Legal, not code |

If someone asks "does it watch Drive?", the answer is "specified, not built".

---

## 4. Bootstrap plan (Commit 3)

`python scripts/deploy.py --vault PATH` must:

1. Resolve whether `PATH` is already a SLIP root or a parent that should receive `SLIP_DOCUMENT_PROCESSING/`.
2. Create the ten directories.
3. Copy or clone this tool into `Convert-PDF-TO-MARKDOWN-01`. If that folder already has a working tree (this vault), skip destructive overwrite of `legacy/` and `.venv`; only ensure package files exist.
4. Place a thin copy or README pointer at `90_00_PROJECT_TOOLING/pdf-to-markdown` **without duplicating `.venv`**.
5. `pip install -e .` into the active interpreter or a created `.venv` under the tool folder.
6. Write `Lawyer-Instruction-Guide-v1-DD-MM-YYYY-HH-MI-SS.md` using Asia/Calcutta time and exactly three Title-Case words.

`deploy.ps1` and `deploy.sh` are wrappers that call the Python script (PowerShell wrapper must not rely on `$` variables expanding incorrectly; prefer `param()` and splatting, or just `py -3 scripts/deploy.py --vault ...`).

CI workflow `.github/workflows/test.yml`:

- on push/pull_request
- matrix Python 3.11, 3.12
- `pip install -e ".[dev,web]"` then `pytest`

Tesseract may be absent on GitHub-hosted runners. Tests that need OCR should skip if the binary is missing; the generated text-layer and table PDFs must pass **without** OCR.

---

## 5. Risk register

| Risk | Mitigation |
| --- | --- |
| Org push rejected | `gh` is logged in as `anilsatyagraha` with `repo` and `workflow` scopes; do not fork |
| PowerShell strips `$` | Ship `.py` files; wrappers call `py -3` |
| Existing `.venv` (2674 files) committed by accident | `.gitignore` first; never `git add -A` on commit 1–4 |
| `find_tables` misses legal grids | TSV bucket fallback + UNRECOVERED |
| Citation regex eats ATTRIBUTE | Word-boundary `ATR` only |
| Double convert on retry | `DONE` short-circuit in `registry.should_convert` |
| Vault path blocked for some tools | Shell + Python only on `D:\satyagraha\VAULT` |

## 6. Definition of done (this sprint)

- Four commits on `main`, pushed, not forced.
- Five docs with exact filenames in commit 1.
- `pytest` passing on the working machine.
- Web `/health` green.
- No client documents in the repository.
- Production tree lives at `Convert-PDF-TO-MARKDOWN-01` and a non-venv copy or pointer under `90_00_PROJECT_TOOLING/pdf-to-markdown`.
