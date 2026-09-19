# Satyagraha Law Group

**TOOLS · Convert-PDF-TO-MARKDOWN-01 · GUBERNATIO**

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

> Research project — not legal advice, not a solicitation.

---

# Master Prompt — Post-run GUBERNATIO ask (+ optional Airtable sync)

**When to use:** Immediately after any Convert-PDF-TO-MARKDOWN-01 convert / approve / quarantine episode finishes.

**Table:** **GUBERNATIO** (always CAPITAL LETTERS)

**Default output:** Markdown only → `D:\satyagraha\VAULT\Satyagraha Law Group\reports\`

**Optional feature:** Airtable.com row mirror for the same date window (off until Anil says yes).

## Step A — Ask for the date window (required)

After convert work is reported done, ask Anil (do not invent dates):

> Convert run finished. Want a **GUBERNATIO** run-insight Markdown for a date window?  
> Reply with **DATE_FROM** and **DATE_TO** (IST, inclusive), e.g. `2026-09-01` and `2026-09-19`.  
> Or say **skip**.

- If **skip** → stop. No report. No Airtable.
- If dates given → normalize to `YYYY-MM-DD`, reject if FROM > TO, write the Markdown insight (interactive helper / SQL against local SQLite SoT).

## Step B — Optional Airtable sync (documented feature; default OFF)

After the Markdown report path is shown, ask once:

> Also sync these **GUBERNATIO** rows to **Airtable** for this window? Reply **yes — Airtable** or **no**.

### Rules

1. **Default is no.** Do not sync unless Anil explicitly says yes in that turn.
2. Happy path remains local SQLite (**GUBERNATIO**). Airtable is a **mirror / fleet view**, not the live SoT — no convert latency on the happy path.
3. Sync scope = rows whose activity date (IST) falls in `DATE_FROM`…`DATE_TO` inclusive (same window as the Markdown report).
4. Target: Satyagraha Law Group Airtable base / table named **GUBERNATIO** (or the mapped mirror table documented in Ops Playbook). Upsert by stable key (`sha256` + attempt `id` when present).
5. Credentials: load only via approved secrets map (`mcp-secrets` / local env) after Anil names the env var — **never print tokens**. Prefer OAuth if configured.
6. On success: report Airtable base name, table **GUBERNATIO**, row upsert count, and window. On failure: keep the Markdown report; do not block; tell Anil the error class (auth / network / schema) without secrets.
7. Do **not** push GitHub unless Anil asks.

### Non-goals for this optional step

- Airtable is not a substitute for local SQLite on convert.
- No full DB zip to Airtable (Drive holds DB zips; Airtable holds row mirror + optional Drive file id pointers).
- No secrets in Markdown reports or git.

## Related

- Interactive dates-first prompt: `LATEST-Gubernatio-Interactive-Query.md`
- Fixed week sample: `LATEST-Gubernatio-Week-Query.md`
- Feature note: `docs/LATEST-Gubernatio-Airtable-Optional-Sync.md`
- EOD: Nightly daily-notes wrap asks the same window + optional Airtable yes/no at 23:00 IST.

---

Satyagraha Law Group · Convert-PDF-TO-MARKDOWN-01 · GUBERNATIO