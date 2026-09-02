# Satyagraha Law Group

# PDF to Markdown (SLIP Document Ingestion)

**Family:** SLIP — Satyagraha Law Group Legal Intelligence Platform  
**Tool name:** PDF to Markdown  
**Layer:** Layer 1 — faithful extract (not case briefs)

This is the photocopier for legal PDFs. It does not summarise, argue, or invent cells. It turns a PDF into Markdown you can open, search, and hand to an LLM.

## Lawyer use (three steps)

1. **Put PDFs in** `0_01_RAW_PDF`
2. **Run convert** (or wait if the web app / watcher is running)
3. **Open** `20_03_CLEAN_MARKDOWN`

That is the whole product for a lawyer: **Drop PDF → Wait → Open Markdown**.

Duplicates are never deleted by the tool. The same file under a different name is converted once. Filename is not identity; SHA-256 is.

---

## For an LLM agent (do this next)

Open [`playbooks/01-Deploy-Scaffold.md`](playbooks/01-Deploy-Scaffold.md) and point the agent at this GitHub repository:

**https://github.com/Satyagraha-Law-Group/pdf-to-markdown**

The playbooks are SKILL-style, parameterized, and work with any LLM. Sequence:

1. `playbooks/01-Deploy-Scaffold.md` — create the ten SLIP folders and install the tool
2. `playbooks/02-Convert-Documents.md` — run the local engine
3. `playbooks/03-Audit-Quality.md` — write a three-word-named quality report
4. `playbooks/04-Handle-Duplicates.md` — route repeats to `50_90_DUPLICATES` (never delete)
5. `playbooks/05-Repair-Markdown.md` — citation OCR repairs and UNRECOVERED table callouts

---

## CLI (Phase 1)

From this folder, with Python 3.11+ and Tesseract OCR installed:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -e ".[dev]"
slip-pdf-md doctor
slip-pdf-md init --vault "PATH/TO/SLIP_DOCUMENT_PROCESSING"
slip-pdf-md convert --vault "PATH/TO/SLIP_DOCUMENT_PROCESSING" --repair-citations
slip-pdf-md audit --vault "PATH/TO/SLIP_DOCUMENT_PROCESSING"
```

Equivalent module form: `python -m slip_pdf_md convert ...`

**Windows Tesseract:** the engine looks for `C:\Program Files\Tesseract-OCR\tesseract.exe` automatically.

### What convert does

- Hashes every PDF (SHA-256). The hash is the document identity.
- New files are copied to `10_02_READY_FOR_DOCLING`, converted, and written to `20_03_CLEAN_MARKDOWN` with YAML front matter and `## Page N` headings.
- Duplicate hashes go to `50_90_DUPLICATES` with a sidecar that points at the first conversion. They are **not** converted again.
- Failures and thin extracts go to `70_99_NEEDS_REVIEW`.
- Status in the SQLite registry: `NEW` → `PROCESSING` → `DONE` or `NEEDS_REVIEW`.
- Retries never double-convert a `DONE` hash.

Optional `--repair-citations` applies conservative OCR fixes (ATR→AIR but never ATTRIBUTE; L]→LJ; AIL)→All.; Caleutta; Jnarkhand; I71-B→171-B).

---

## Web app (Phase 2)

Same engine, lawyer-facing drop zone.

```bash
pip install -e ".[web]"
uvicorn web.app:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 — drop a PDF, wait, download Markdown.  
`GET /health` is the liveness probe. `POST /jobs` uploads. `GET /jobs/{id}` polls. Download the `.md` from the job payload.

Phase 2b (Google Drive watcher, Make.com, IBM Docling as a swap-in engine) is specified in the design documents. It is **not** implemented in this repository.

---

## Bootstrap a vault

```bash
python scripts/deploy.py --vault "PATH/TO/VAULT_OR_SLIP_ROOT"
```

PowerShell: `./scripts/deploy.ps1 -Vault "PATH"`  
Bash: `./scripts/deploy.sh --vault "PATH"`

Deploy creates the ten SLIP folders, copies this tool into `Convert-PDF-TO-MARKDOWN-01` (and a pointer under `90_00_PROJECT_TOOLING`), runs `pip install -e .`, and writes a `Lawyer-Instruction-Guide` using the three-word filename convention.

---

## SLIP folder contract

| Folder | Role |
| --- | --- |
| `0_01_RAW_PDF` | Drop zone. You put files here. |
| `10_02_READY_FOR_DOCLING` | Accepted new PDFs queued for the engine. |
| `20_03_CLEAN_MARKDOWN` | Faithful Markdown (Layer 1). |
| `30_04_CASE_BRIEFS` | Empty in this tool. Layer 2, out of scope. |
| `40_05_PROJECT_BRIEFS` | Empty in this tool. Layer 2, out of scope. |
| `50_90_DUPLICATES` | Same SHA-256, different name or re-drop. Sidecar, no second convert. |
| `60_90_PROCESSED` | Originals moved after a successful convert. |
| `70_99_NEEDS_REVIEW` | Engine could not stand behind the extract. |
| `90_00_PROJECT_TOOLING` | Registry, this tool, install notes. |
| `Convert-PDF-TO-MARKDOWN-01` | Working copy of this product. |

Do not rename these folders.

---

## Documents in this repository

Thorough specifications live in `docs/`:

- Product requirements
- System design (engines, registry, security, engine adapter)
- Implementation plan
- System architecture (Mermaid)
- Process workflow (drop → hash → route → convert → audit)

---

## Tests

```bash
pytest
```

Coverage includes registry uniqueness, a generated text-layer PDF, a generated table PDF, citation regex, scaffold folder creation, audit report naming, and `/health`.

---

## Confidentiality

Client PDFs never belong in git. `.gitignore` blocks `*.pdf`, `.venv/`, `markdown/`, `MASTER_MACDONE.md`, and repair dumps. The public GitHub repository is the tool, not the evidence.

---

© 2026 Satyagraha Law Group. MIT License.
