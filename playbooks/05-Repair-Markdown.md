# SKILL: Repair Markdown (mechanical only)

**Satyagraha Law Group** — PDF to Markdown  
**Playbook:** 05-Repair-Markdown  
**Depends on:** 03-Audit-Quality  
**Rule:** Layer 1 is a photocopy. Do not invent table cells. Do not brief the case.

## Goal

Apply conservative OCR repairs and document UNRECOVERED tables. Promote a `NEEDS_REVIEW` file only when a retry actually extracted text.

## Parameters

| Name | Required | Default |
| --- | --- | --- |
| `{{SLIP_ROOT}}` | yes | |
| `{{PYTHON}}` | no | `py -3` |
| `{{REPAIR_CITATIONS}}` | no | `true` for this playbook |

## Citation map (and the ATTRIBUTE trap)

When `--repair-citations` is on:

| OCR | Legal | Must not |
| --- | --- | --- |
| `ATR` as a whole word | `AIR` | change `ATTRIBUTE` |
| `L]` | `LJ` | |
| `AIL)` | `All.` | |
| `Caleutta` | `Calcutta` | |
| `Jnarkhand` | `Jharkhand` | |
| `I71-B` | `171-B` | |

## Steps

1. Read audit flags, especially `UNRECOVERED_TABLE`, `EMPTY_BODY`, `STALE_PROCESSING`.
2. If Tesseract was missing, install it (Windows default `C:\Program Files\Tesseract-OCR\tesseract.exe`) and retry **only** hashes in `NEEDS_REVIEW` by placing the original PDF back in `0_01_RAW_PDF`. `DONE` hashes will duplicate-route, not reconvert.
3. Re-run convert with `--repair-citations` for new or review hashes.
4. For UNRECOVERED tables: leave the callout. You may recover a table only from visible glyphs in the PDF (re-OCR a clip). You may **not** guess a cell from context, statute knowledge, or "what a limitation table usually contains".
5. Collapse leftover TOC leaders (`........`) if the engine missed them. Demote true running headers to `<!-- running header: … -->`.
6. Do not fill `30_04_CASE_BRIEFS`.

## Verification

- `ATTRIBUTE` still appears where it did in the source.
- Every guessed-looking table cell is absent; callouts remain honest.
- Front matter `processing_status` matches the tray (`DONE` in `20_03`, `NEEDS_REVIEW` in `70_99`).

## Stop conditions

- "Just make the table complete" without pixels → refuse.
- Rewriting legal prose for style → refuse.
