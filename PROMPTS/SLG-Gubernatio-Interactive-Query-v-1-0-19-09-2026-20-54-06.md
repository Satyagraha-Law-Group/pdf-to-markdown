# Satyagraha Law Group

**TOOLS · Convert-PDF-TO-MARKDOWN-01 · GUBERNATIO**

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

[https://www.satyagraha.com](https://www.satyagraha.com)

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

---

# Master Prompt — Interactive GUBERNATIO date-window report (Markdown only)

**Document:** `SLG-Gubernatio-Interactive-Query-v-1-0-19-09-2026-20-54-06.md`  
**Tool:** Convert-PDF-TO-MARKDOWN-01  
**Table:** **GUBERNATIO** (always CAPITAL LETTERS)  
**Output:** Markdown only (no HTML) for Obsidian / file-based viewing under vault `reports`

## Intent

Anil (operator) wants a GUBERNATIO convert-run insight report for an arbitrary date window. The agent **must not invent dates**. It **queries Anil first**, then runs the query, then writes **one Markdown file** into:

`D:\satyagraha\VAULT\Satyagraha Law Group\reports\`

so he can open it in his file-based viewer and scan status / engine / machine / agent / attempt detail.

Fixed-window companion (no ask): `SLG-Gubernatio-Week-Query-v-1-0-19-09-2026-20-42-26.md`

## Step 0 — Ask Anil (required before any DB read)

Collect these fields (start date and from date are the same value; if Anil gives both and they disagree, stop and clarify):

| Field | Parameter | Required | Format | Meaning |
| --- | --- | --- | --- | --- |
| Start date | `DATE_FROM` | yes | `YYYY-MM-DD` | Inclusive window start (IST calendar day) |
| From date | `DATE_FROM` | yes | `YYYY-MM-DD` | Alias of start date |
| To date | `DATE_TO` | yes | `YYYY-MM-DD` | Inclusive window end (IST calendar day) |

Optional filters (defaults = all): `MACHINE_FILTER`, `AGENT_FILTER`, `STATUS_FILTER`, `REPORT_LABEL`.

**Rules**

1. Do **not** run SQL until Anil answers with dates.
2. Normalize to `YYYY-MM-DD`. Reject if `DATE_FROM` > `DATE_TO`.
3. Confirm: `Window IST: {DATE_FROM} → {DATE_TO} (inclusive)`.
4. Never print secrets or API keys.

### Example ask

> For the GUBERNATIO convert report, what is the **start / from date** and the **to date**? (IST calendar, inclusive — e.g. `2026-09-11` and `2026-09-19`.)

## Parameters (after answers)

| Parameter | Example | Notes |
| --- | --- | --- |
| `DATE_FROM` | `2026-09-11` | Inclusive IST |
| `DATE_TO` | `2026-09-19` | Inclusive IST |
| `DB_PATH` | `D:\satyagraha\VAULT\SLIP_DOCUMENT_PROCESSING\90_00_PROJECT_TOOLING\pdf-to-markdown\Document-Hash-Registry-v1-03-09-2026-05-56-17.sqlite` | Live registry until `_runtime-state\GUBERNATIO` cutover |
| `OUTPUT_DIR` | `D:\satyagraha\VAULT\Satyagraha Law Group\reports` | Vault reports (Markdown viewer home) |
| `OUTPUT_FORMAT` | `markdown` | **Markdown only** — do not emit HTML for this prompt |

## Sample SQL (GUBERNATIO)

```sql
-- GUBERNATIO: Convert-PDF-TO-MARKDOWN attempts in operator-chosen window (IST)
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
      BETWEEN date(:date_from) AND date(:date_to)
ORDER BY COALESCE(converted_at, approved_at, first_seen_at, seen_at), filename;
```

If timestamps are mixed / TZ-ambiguous, use Python activity-date logic: first non-empty among `converted_at`, `approved_at`, `first_seen_at`, `seen_at`, convert to IST, filter by calendar date.

Also report **PROCESS_RUNS** count where `run_day` is in the same inclusive window (secondary metric).

## Agent run steps

1. Ask Anil for start/from + to dates (Step 0). Wait.
2. Open `DB_PATH` **read-only**.
3. Query **GUBERNATIO**; apply optional filters.
4. Compute **attempts** (ledger rows) and **distinct_files** (unique `sha256`, else filename); breakdowns by status, engine, machine (`host`), agent.
5. Write **one** Markdown file only:

   `{OUTPUT_DIR}\SLG-Gubernatio-Run-Insight-v-1-0-dd-MM-yyyy-HH-mm-ss.md`

6. Overwrite pointer with the same body:

   `{OUTPUT_DIR}\LATEST-Gubernatio-Run-Insight.md`

7. Tell Anil the absolute path and the two headline numbers. Stop. Do not auto-post elsewhere.

## Markdown body outline (required sections)

1. Satyagraha chrome (Rig Veda / Aristotle / research disclaimer)
2. `# GUBERNATIO Run Insight — Convert-PDF-TO-MARKDOWN-01`
3. Window + generated + source DB
4. `## Answer` (distinct files, attempt rows, PROCESS_RUNS)
5. `## Sample query (GUBERNATIO)`
6. Breakdown tables (status / engine / machine / agent)
7. Detail table of rows
8. Notes (activity-date rule; append-only ledger)

## Helper script (after dates are known)

```text
python D:\satyagraha\VAULT\TOOLS\Convert-PDF-TO-MARKDOWN-01\scripts\gubernatio_interactive_report.py --from YYYY-MM-DD --to YYYY-MM-DD
```

Writes Markdown only into `D:\satyagraha\VAULT\Satyagraha Law Group\reports`.

## Non-goals

- No HTML twin for this prompt
- No Airtable write
- No mutation of GUBERNATIO
- No secrets in the report

---

Satyagraha Law Group · Convert-PDF-TO-MARKDOWN-01 · GUBERNATIO

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

[https://www.satyagraha.com](https://www.satyagraha.com)
