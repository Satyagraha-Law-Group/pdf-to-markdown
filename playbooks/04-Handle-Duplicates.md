# SKILL: Handle duplicate PDFs

**Satyagraha Law Group** — PDF to Markdown  
**Playbook:** 04-Handle-Duplicates  
**Rule:** filename is not identity. SHA-256 is. No AI deletion of duplicates.

## Goal

Explain and route repeats. Keep the bytes.

## Parameters

| Name | Required |
| --- | --- |
| `{{SLIP_ROOT}}` | yes |

## What the tool already did

On `convert`, a PDF whose SHA-256 is `DONE` was copied to `50_90_DUPLICATES` with a `.sidecar.md` naming:

- duplicate filename
- hash
- original filename
- canonical Markdown path
- timestamp

The first conversion in `20_03_CLEAN_MARKDOWN` was left untouched.

## Steps for an agent

1. List `{{SLIP_ROOT}}/50_90_DUPLICATES`.
2. Open each `.sidecar.md`. Summarise for the lawyer: "this is the same document as X".
3. Do **not** `unlink`, `rm`, shred, or git-ignore the duplicate out of existence as a cleanup step.
4. Do **not** run convert again on that hash expecting a second Markdown.
5. If the lawyer says the second file is actually a **different scan**, hash it. Different bytes ⇒ new document; convert is correct.

## Verification

- Registry still has one `documents` row per SHA-256.
- Two or more `sightings` rows for that hash.
- Duplicate files still on disk.

## Stop conditions

Any request to "remove dupes", "keep only the latest filename", or "let the model decide which copy to keep" is out of scope. Route, sidecar, stop.
