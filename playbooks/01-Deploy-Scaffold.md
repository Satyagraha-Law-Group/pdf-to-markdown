# SKILL: Deploy SLIP PDF-to-Markdown scaffold

**Satyagraha Law Group** — PDF to Markdown  
**Family:** SLIP — Satyagraha Law Group Legal Intelligence Platform  
**Playbook:** 01-Deploy-Scaffold  
**For:** any LLM / coding agent  
**Does not:** commit client PDFs, force-push, delete duplicates, call cloud OCR

## Goal

Install this product into a vault so a lawyer can Drop PDF → Wait → Open Markdown.

## Parameters

| Name | Required | Example |
| --- | --- | --- |
| `{{REPO_URL}}` | yes | `https://github.com/Satyagraha-Law-Group/pdf-to-markdown` |
| `{{VAULT}}` | yes | `D:\satyagraha\VAULT\Satyagraha Law Group` |
| `{{PYTHON}}` | no | `py -3` on Windows, `python3` elsewhere |

If `{{VAULT}}` already contains `0_01_RAW_PDF`, treat it as the SLIP root. Otherwise create `{{VAULT}}/SLIP_DOCUMENT_PROCESSING/`.

## Steps

1. Clone or pull `{{REPO_URL}}`. Prefer the existing working copy at `Convert-PDF-TO-MARKDOWN-01` if it is already this product.
2. Do **not** run `git config`. Do not force-push. Do not commit `.venv` or `*.pdf`.
3. Run:

```text
{{PYTHON}} scripts/deploy.py --vault "{{VAULT}}"
```

Windows alternative: `py -3 scripts/deploy.py --vault "{{VAULT}}"`  
Wrappers: `scripts/deploy.ps1` and `scripts/deploy.sh`.

4. Deploy must:
   - create the ten SLIP folders (do not rename them)
   - copy or keep the tool in `Convert-PDF-TO-MARKDOWN-01`
   - put a pointer or copy **without `.venv`** under `90_00_PROJECT_TOOLING/pdf-to-markdown`
   - `pip install -e .`
   - write `Lawyer-Instruction-Guide-vN-DD-MM-YYYY-HH-MI-SS.md` (exactly three Title-Case words, Asia/Calcutta, 24-hour)
5. Run `{{PYTHON}} -m slip_pdf_md doctor --vault "<SLIP root>"`.
6. Stop. Next playbook is `02-Convert-Documents.md`.

## Verification

- Folders exist: `0_01_RAW_PDF`, `10_02_READY_FOR_DOCLING`, `20_03_CLEAN_MARKDOWN`, `30_04_CASE_BRIEFS`, `40_05_PROJECT_BRIEFS`, `50_90_DUPLICATES`, `60_90_PROCESSED`, `70_99_NEEDS_REVIEW`, `90_00_PROJECT_TOOLING`, `Convert-PDF-TO-MARKDOWN-01`.
- `doctor` reports PyMuPDF import OK. Tesseract may be missing; warn, do not invent OCR.
- No client PDF was copied into git.

## Stop conditions

- Path is not writable → report and stop.
- `{{REPO_URL}}` is not the Satyagraha Law Group repo and the user did not name a fork → stop. Do not silently fork.
