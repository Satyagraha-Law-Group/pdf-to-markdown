# Process Workflow Guide

**Satyagraha Law Group**  
**Product:** PDF to Markdown  
**Family:** SLIP — Satyagraha Law Group Legal Intelligence Platform  
**Document:** Process-Workflow-Guide-v1-02-09-2026-22-55-00  
**Audience:** lawyers, clerks, and any LLM executing the playbooks

---

## 1. Happy path (photocopier)

1. Put one or more PDFs into `0_01_RAW_PDF`.
2. Run `slip-pdf-md convert --vault <SLIP root>` (or drop the file on the Phase 2 web page and wait).
3. Open the sibling file in `20_03_CLEAN_MARKDOWN`.

If you use an LLM, start at `playbooks/01-Deploy-Scaffold.md` with  
`{{REPO_URL}} = https://github.com/Satyagraha-Law-Group/pdf-to-markdown`.

That is the entire lawyer-facing workflow. The rest of this guide is what happens inside, including duplicates, retries, and `NEEDS_REVIEW`.

---

## 2. End-to-end sequence

```
drop PDF
  → SHA-256
    → route
      → convert (or skip)
        → audit flags
          → 20_03_CLEAN_MARKDOWN    or    70_99_NEEDS_REVIEW
```

### Step A — Drop

A human or watcher places files in `0_01_RAW_PDF`. Nested subfolders are allowed; the converter walks them recursively. Do not rename the folder.

### Step B — Hash

For each `*.pdf` the tool reads all bytes and computes SHA-256. The hash is the document. The filename is a caption. Two files named `IPC.pdf` and `ipc (1).pdf` with identical bytes are **one** document.

### Step C — Route

| Registry says | Route | Convert? |
| --- | --- | --- |
| never seen | copy to `10_02_READY_FOR_DOCLING`; status `NEW` then `PROCESSING` | Yes |
| `DONE` | copy to `50_90_DUPLICATES` plus sidecar; original may move to `60_90_PROCESSED` | **No** |
| `PROCESSING` (crash) | do not create a second row; resume | Yes, once |
| `NEEDS_REVIEW` | keep one row; retry writes a new attempt | Yes, replacing the review file on success |

Sidecar contents (Markdown):

- duplicate filename
- SHA-256
- first-seen original filename
- path to canonical Markdown if `DONE`
- timestamp (Asia/Calcutta)

The duplicate **file is not deleted**. No playbook, CLI flag, or "smart cleanup" removes it.

### Step D — Convert

Engine order per page:

1. `find_tables` → pipe table if cells are real.
2. PDF text layer → paragraphs.
3. Tesseract OCR if the text layer is empty.
4. Tesseract TSV buckets if a grid is suspected.
5. `UNRECOVERED TABLE REGION` callout if a grid is suspected but cells cannot be recovered.

Then:

- YAML front matter (`document_type`, `source_file`, `source_sha256`, `processing_status`, `engine`, `page_count`, `converted_at`).
- `## Page N` for every page.
- Leader collapse.
- Running headers to HTML comments.
- Optional `--repair-citations`.

Windows OCR binary: `C:\Program Files\Tesseract-OCR\tesseract.exe`.

### Step E — Write

- Success → `20_03_CLEAN_MARKDOWN/{stem}.md`, status `DONE`, RAW file moved to `60_90_PROCESSED`.
- Failure or empty extract the engine will not stand behind → `70_99_NEEDS_REVIEW/`, status `NEEDS_REVIEW`.

Layer 2 folders `30_04_CASE_BRIEFS` and `40_05_PROJECT_BRIEFS` are not written.

### Step F — Audit flags

`slip-pdf-md audit` walks clean Markdown and review folders and flags:

| Flag | Meaning | Typical action |
| --- | --- | --- |
| `MISSING_FRONT_MATTER` | File is not a product output | Re-run convert or ignore stray files |
| `HASH_MISMATCH` | Front matter SHA ≠ registry | Treat as `NEEDS_REVIEW` |
| `NO_PAGE_HEADINGS` | Lost page contract | Re-run convert |
| `EMPTY_BODY` | Photocopier produced a blank | Scan quality / OCR doctor |
| `UNRECOVERED_TABLE` | Honest gap in a grid | Human or playbook 05; do not invent cells |
| `ORPHAN_DONE` | Status `DONE` but Markdown missing | Repair status or retry under review rules |
| `STALE_PROCESSING` | Crash residue | Resume convert |

Audit writes `Audit-Quality-Report-vN-DD-MM-YYYY-HH-MI-SS.md` (three Title-Case words, 24-hour Asia/Calcutta).

---

## 3. Duplicates in practice

Scenario: clerk drops `Contract-Scan.pdf`. Convert succeeds. Later a lawyer drops `contract scan (final).pdf` with the same bytes.

What the lawyer sees:

- `20_03_CLEAN_MARKDOWN/Contract-Scan.md` — unchanged, still the only conversion.
- `50_90_DUPLICATES/contract scan (final).pdf` — the second physical file, kept.
- `50_90_DUPLICATES/contract scan (final).pdf.sidecar.md` — explains why it was not converted again.

What never happens:

- Silent overwrite of the Markdown with a second slightly different OCR.
- Deletion of the second PDF because "we already have it".
- A new registry row.

If the second file is **not** the same bytes (re-scan, different crop), it is a new hash and converts independently. That is correct: it is a different photocopy.

---

## 4. Retries

| Starting status | Command | Result |
| --- | --- | --- |
| `DONE` | `convert` again with the same file still in RAW (or re-dropped) | Duplicate path; Markdown untouched |
| `DONE` | `convert --force` is **not provided** in Phase 1 | Avoid accidental double-convert. Re-convert requires flipping status via a documented review path |
| `NEEDS_REVIEW` | `convert` | Engine runs once more; success promotes to `20_03` and `DONE` |
| `PROCESSING` | `convert` after crash | Resume; still one Markdown target |
| `NEW` | n/a | Immediately moves to `PROCESSING` |

There is no `--force` in this sprint on purpose. Double-convert of a `DONE` hash is a defect.

---

## 5. NEEDS_REVIEW vs CLEAN_MARKDOWN

`20_03_CLEAN_MARKDOWN` is the lawyer-trusted tray. Anything in it should have front matter `processing_status: DONE`.

`70_99_NEEDS_REVIEW` is the exception tray. Reasons include:

- Tesseract missing on a scanned page.
- Exception inside PyMuPDF.
- Zero pages of recoverable text.
- Audit-promoted files (`EMPTY_BODY`, `HASH_MISMATCH`).

A human (or playbook 05) inspects review files. They may:

- Install Tesseract and retry.
- Supply a better scan.
- Manually type a table and leave an editorial note. The tool itself will not guess the table.

---

## 6. Web workflow (Phase 2)

1. Open http://127.0.0.1:8000
2. Drop a PDF on the page.
3. The browser `POST`s `/jobs` and polls `GET /jobs/{id}`.
4. When status is `DONE`, download Markdown.
5. If a SLIP vault is configured, the same routing rules apply (duplicates included). If not, the job uses an isolated mini-vault so the page still works on a developer laptop.

`GET /health` is for operators and CI, not for lawyers.

---

## 7. First-time vault workflow

```
python scripts/deploy.py --vault "D:\satyagraha\VAULT\Satyagraha Law Group"
```

or, if the SLIP root already exists:

```
python scripts/deploy.py --vault "D:\satyagraha\VAULT\Satyagraha Law Group\SLIP_DOCUMENT_PROCESSING"
```

Deploy creates folders, installs the package, and writes `Lawyer-Instruction-Guide-v1-…md` beside the tool. Then return to §1.

---

## 8. Filename convention for generated docs and logs

Exactly three Title-Case words, hyphens only, no underscores, no spaces, four-digit year, 24-hour Asia/Calcutta:

`Word1-Word2-Word3-vN-DD-MM-YYYY-HH-MI-SS.ext`

Examples:

- `Audit-Quality-Report-v1-02-09-2026-22-55-00.md`
- `Lawyer-Instruction-Guide-v1-02-09-2026-22-55-00.md`

Do **not** rename pipeline folders `0_01_RAW_PDF` and siblings to fit this convention. Those names are the SLIP contract.

---

## 9. Stop conditions (for humans and agents)

Stop and ask a lawyer before:

- Deleting anything from `50_90_DUPLICATES`.
- Sending a client PDF to a cloud OCR API.
- Committing a PDF or `MASTER_MACDONE.md` to git.
- Force-pushing `main`.
- Filling `30_04_CASE_BRIEFS` from this tool.

The photocopier copies. It does not advocate, brief, or shred.
