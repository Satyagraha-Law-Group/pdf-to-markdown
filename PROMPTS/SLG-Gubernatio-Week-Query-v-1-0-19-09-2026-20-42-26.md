# Satyagraha Law Group

**TOOLS · Convert-PDF-TO-MARKDOWN-01 · GUBERNATIO**

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

[https://www.satyagraha.com](https://www.satyagraha.com)

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

---

# Master Prompt — GUBERNATIO week query (Convert-PDF-TO-MARKDOWN-01)

**Document:** `SLG-Gubernatio-Week-Query-v-1-0-19-09-2026-20-42-26.md`  
**Tool:** Convert-PDF-TO-MARKDOWN-01  
**Table:** **GUBERNATIO** (CAPITAL LETTERS always)

## Purpose

Answer: *How many files / attempts did Convert-PDF-TO-MARKDOWN process in a date window?*  
Supports fleet reporting later via Airtable sync; today queries local SQLite SoT.

## Parameters

| Parameter | Type | Example | Notes |
| --- | --- | --- | --- |
| `DATE_FROM` | ISO date | `2026-09-11` | Inclusive start (IST calendar) |
| `DATE_TO` | ISO date | `2026-09-19` | Inclusive end (IST calendar) |
| `DB_PATH` | path | Document-Hash-Registry-*.sqlite | Live registry until `_runtime-state\GUBERNATIO` is cut over |
| `COUNT_MODE` | enum | `attempts` \| `distinct_files` | attempts = ledger rows; distinct_files = unique sha256/filename |
| `MACHINE_FILTER` | string/optional | `DESKTOP-IG57K1N` | Empty = all machines |
| `AGENT_FILTER` | string/optional | `Spock` | Empty = all agents |
| `STATUS_FILTER` | string/optional | `APPROVED` | Empty = all statuses |
| `OUTPUT_DIR` | path | `reports/gubernatio` | MD+HTML under tool |

## Sample SQL (GUBERNATIO)

```sql
-- GUBERNATIO: Convert-PDF-TO-MARKDOWN attempts in window (IST calendar dates)
-- Parameters: :date_from, :date_to  (YYYY-MM-DD inclusive)
SELECT
  id,
  filename,
  status,
  engine,
  page_count,
  host AS machine_name,
  agent AS agent_name,
  source_path AS input_path,
  output_path,
  first_seen_at,
  converted_at,
  approved_at,
  seen_at,
  last_error,
  token_usage
FROM GUBERNATIO
WHERE date(COALESCE(converted_at, approved_at, first_seen_at, seen_at))
      BETWEEN date('2026-09-11') AND date('2026-09-19')
ORDER BY COALESCE(converted_at, approved_at, first_seen_at, seen_at), filename;
```

## Agent instructions

1. Open `DB_PATH` read-only.
2. Run the SQL (or equivalent Python activity-date logic if timestamps are mixed TZ).
3. Report both **attempt rows** and **distinct files**.
4. Break down by status, engine, machine (`host`), agent.
5. Emit MD + HTML with SLG naming: `SLG-Gubernatio-Week-Report-v-1-0-dd-MM-yyyy-HH-mm-ss.{md,html}`.
6. Never print secrets or API keys.
7. Table name always **GUBERNATIO**.

## This run's bound parameters

- DATE_FROM: `2026-09-11`
- DATE_TO: `2026-09-19`
- DB_PATH: `D:\satyagraha\VAULT\SLIP_DOCUMENT_PROCESSING\90_00_PROJECT_TOOLING\pdf-to-markdown\Document-Hash-Registry-v1-03-09-2026-05-56-17.sqlite`
- COUNT_MODE: attempts + distinct_files
- MACHINE_FILTER: (none)
- AGENT_FILTER: (none)
- STATUS_FILTER: (none)

---

Satyagraha Law Group publishes firm tools and research systems. It does not publish a client-facing legal advice service through these notes.

**Satyagraha Law Group** · Convert-PDF-TO-MARKDOWN-01 · GUBERNATIO

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

[https://www.satyagraha.com](https://www.satyagraha.com)
