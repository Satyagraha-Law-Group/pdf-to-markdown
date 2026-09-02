# SKILL: Audit Markdown quality

**Satyagraha Law Group** — PDF to Markdown  
**Playbook:** 03-Audit-Quality  
**Depends on:** 02-Convert-Documents

## Goal

Flag extracts the photocopier should not silently bless. Write one three-word-named report.

## Parameters

| Name | Required |
| --- | --- |
| `{{SLIP_ROOT}}` | yes |
| `{{PYTHON}}` | no |

## Steps

1. Run:

```text
{{PYTHON}} -m slip_pdf_md audit --vault "{{SLIP_ROOT}}"
```

2. Confirm the report filename matches:

`Word1-Word2-Word3-vN-DD-MM-YYYY-HH-MI-SS.ext`

Exactly three Title-Case words, hyphens only, 24-hour Asia/Calcutta. The tool writes `Audit-Quality-Report-v1-…md` under `90_00_PROJECT_TOOLING/pdf-to-markdown/`.

3. Read flags:

| Flag | Meaning |
| --- | --- |
| `MISSING_FRONT_MATTER` | Not a product output |
| `NO_PAGE_HEADINGS` | Lost `## Page N` contract |
| `EMPTY_BODY` | Blank photocopy |
| `UNRECOVERED_TABLE` | Honest gap — do not invent cells |
| `ORPHAN_DONE` | Registry says DONE but file missing |
| `STALE_PROCESSING` | Crash residue |

4. Move truly bad files' attention to `70_99_NEEDS_REVIEW`. Do not delete `20_03` files unless a lawyer asks.

## Verification

- Report exists and matches the regex in `slip_pdf_md.naming.REPORT_NAME_RE`.
- Report mentions Satyagraha Law Group.

## Stop conditions

- Do not auto-rewrite legal prose with an LLM "to improve quality". Repair is playbook 05, mechanical only.
