# SKILL: Convert PDFs to Markdown

**Satyagraha Law Group** — PDF to Markdown  
**Playbook:** 02-Convert-Documents  
**Depends on:** 01-Deploy-Scaffold

## Goal

Convert every new PDF in `0_01_RAW_PDF` into Layer 1 Markdown in `20_03_CLEAN_MARKDOWN`. Same bytes, different name = once.

## Parameters

| Name | Required | Default |
| --- | --- | --- |
| `{{SLIP_ROOT}}` | yes | the folder that contains `0_01_RAW_PDF` |
| `{{PYTHON}}` | no | `py -3` / `python3` |
| `{{REPAIR_CITATIONS}}` | no | `false` |

## Steps

1. Confirm PDFs are in `{{SLIP_ROOT}}/0_01_RAW_PDF`. Do not rename that folder.
2. Run doctor if Tesseract status is unknown.
3. Convert:

```text
{{PYTHON}} -m slip_pdf_md convert --vault "{{SLIP_ROOT}}"
```

If `{{REPAIR_CITATIONS}}` is true, add `--repair-citations`. That maps ATR→AIR (never ATTRIBUTE), L]→LJ, AIL)→All., Caleutta, Jnarkhand, I71-B→171-B.

4. Read the CLI summary line `converted=… duplicates=… needs_review=…`.
5. Tell the lawyer: open `{{SLIP_ROOT}}/20_03_CLEAN_MARKDOWN`.
6. Do not write case briefs. `30_04_CASE_BRIEFS` and `40_05_PROJECT_BRIEFS` stay empty.

## Routing you must honour

- New SHA-256 → copy `10_02_READY_FOR_DOCLING` → Markdown in `20_03_CLEAN_MARKDOWN` → original to `60_90_PROCESSED`.
- Known `DONE` SHA-256 → `50_90_DUPLICATES` + sidecar. **Do not convert again. Do not delete.**
- Failure / empty extract → `70_99_NEEDS_REVIEW`.

## Verification

- Each `DONE` Markdown has YAML front matter with `document_type`, `source_file`, `source_sha256`, `processing_status`, `engine`, `page_count`, `converted_at`.
- Body uses `## Page N`.
- Retries of a `DONE` hash did not create a second Markdown.

## Stop conditions

- Asking you to "just delete the dupes" → refuse, point at playbook 04.
- Asking you to invent table cells → refuse; leave `UNRECOVERED` callouts.
