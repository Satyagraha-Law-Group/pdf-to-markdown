# GUBERNATIO — Optional Airtable sync (documented feature)

**Stamp:** 19-09-2026-21-42-00  
**Status:** Documented option — **default OFF** until Anil says yes on a given run  
**Tool:** Convert-PDF-TO-MARKDOWN-01  
**Table:** **GUBERNATIO**

## Why

Local SQLite remains the happy-path source of truth. Airtable is the multi-machine / multi-agent **row mirror** so fleet queries do not lock a live DB on one PC.

## When it may run

1. **Post-run** — after Convert finishes and after the Markdown run-insight is written (or skipped only if Anil skipped the whole insight).
2. **End of day** — Nightly daily-notes wrap (23:00 IST) asks for DATE_FROM / DATE_TO, then optional Airtable yes/no.

## Operator prompts (exact intent)

- Window: DATE_FROM / DATE_TO (IST inclusive) or skip  
- Sync: **yes — Airtable** / **no** (default no)

## Behaviour

| Step | Behaviour |
| --- | --- |
| SoT read | Local **GUBERNATIO** SQLite (read-only for the report/sync select) |
| Markdown | Always allowed when dates given → vault `reports` |
| Airtable | Only if Anil says yes; upsert window rows into Airtable table **GUBERNATIO** |
| Secrets | Point-and-load / OAuth; never print; never commit |
| Failure | Report error class; keep Markdown; do not fail the convert episode |

## Field mapping (minimum)

Mirror append-only ledger fields where present: attempt id, sha256, filename, status, engine, page_count, host (machine), agent, source_path, output_path, first_seen_at, converted_at, approved_at, seen_at, last_error, token_usage, activity_ist.

## Related architecture

See `TOOLS\_runtime-state\_docs\` runtime-state architecture (local SQLite + GitHub SLG-DATABASE manifests + Airtable row mirror + Drive DB zips).

## Implementation note

Live Airtable API upsert is optional and credential-gated. This document defines the feature contract; wiring the connector is a follow-on once base/table IDs and secrets are approved.