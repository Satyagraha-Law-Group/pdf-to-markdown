# Satyagraha Law Group

**PDF to Markdown** · SLIP · Legal Research · Practitioner-Scholar

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

[https://www.satyagraha.com](https://www.satyagraha.com)

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

---

# SLG Convert Learnings — GODI full episode (18–19 Sep 2026)

**Document:** `SLG-Convert-Learnings-v-1-0-19-09-2026-18-35-03.md`  
**Written:** `2026-09-19T18:35:03+05:30`  
**Audience:** Future Spock / agents / lawyers operating `Convert-PDF-TO-MARKDOWN-01`  
**Supersedes:** `SLG-Convert-Learnings-v-1-0-19-09-2026-14-49-22.md` (afternoon draft — morning annexures only)

## 1. What we ran (validated)

Project **GODI** / client **DR. SHEKAR**. GUBERNATIO validated **22 / 22 APPROVED** converts for work since 18 Sep 2026:

| Block | Count | Engine path | Notes |
| --- | ---: | --- | --- |
| Rights Issue Letters of Offer | 10 | Mistral | All APPROVED |
| Email/fwd PDFs (GODI pack) | 4 | Mistral | Includes `12-39-14_GODI PVT LMT` |
| Annexures I–IV + Response | 6 | Mistral; AOA→Gemini hybrid; III+Response→raster+Mistral | Annexure IV SHA = LOO #9 (dedupe) |
| GODI PVT LMT bank statement | 1 | Mistral native kept; raster@220dpi Mistral `--force` scored worse | Eye-compare kept native |
| **Total unique intake** | **22** | | Staged under operator TO-DO |

Intake staging folder (operator):

`C:\Users\SATYAGRAHA\Downloads\TO-DO\GODI-19-09-2026 15-47-34\PROCESSED_PDF`  
`C:\Users\SATYAGRAHA\Downloads\TO-DO\GODI-19-09-2026 15-47-34\APPROVED_MARKDOWN`

## 2. Standing rules (do these every time)

### R-01 — Always ask engine before convert / `--force`
Two options only: **Local Tesseract** (`--engine pymupdf`) vs **Mistral AI** (`--engine mistral`). Do not start until Anil picks (unless he already named the engine in the same turn). Skill: convert-engine-choice.

### R-02 — Fidelity gate ≠ absolute accuracy
Gate = **token overlap vs local Tesseract** (threshold ~0.90). Readable Mistral/Gemini at ~0.70–0.75 can still be the better legal draft. Eye-compare; ask approve override / Gemini / dual-file. Blind `--force` rarely jumps 0.71→0.90.

### R-03 — Mistral Empty PDF → raster then Mistral `--force`
If Mistral returns 0 pages / `# Empty PDF` while the PDF opens locally: rasterize pages **~200–220 dpi** to an image PDF, then Mistral `--force`. Do not loop native Mistral alone.

### R-04 — Raster naming: `_raster` before the real extension
Use `Name_raster.pdf` / `Name_raster.md`. **Never** mid-name `.raster.` (multi-dot extensions are forbidden — standing Anil rule 19 Sep 2026).

### R-05 — Raster Mistral can be worse than native Mistral
GODI PVT LMT: native Mistral ~0.74 kept; raster Mistral ~0.64 discarded after eye-compare. **Keep the better human-judged draft**, not the newer file.

### R-06 — Tesseract-on-raster can false-pass `AWAITING_APPROVAL`
Local Tesseract convert of a raster self-compares into a false pass. Quarantine those artifacts; do not treat as a real win.

### R-07 — PowerShell CLI hygiene
- Set `MISTRAL_API_KEY` in the shell environment before spawn.
- Pipe empty stdin: `'' | python -m slip_pdf_md ...` (avoids interactive hang).
- Separate stdout/stderr log files.
- If `SECRETS.txt` holds a **dummy** Mistral key, restore from a dated `SECRETS-*.txt` backup — **never print** the value.

### R-08 — Long AOA (~70 pp): escalate to Gemini hybrid
Mistral ~0.71 → Gemini vision page OCR (probe live model; `gemini-3.1-flash-lite` worked 18 Sep 2026). **RECITATION** pages → Tesseract fill; document hybrid in front matter. Verify `GEMINI_API_KEY` length after load (may be empty name).

### R-09 — Approve close-out
CLI approve + CLEAN front matter `APPROVED` + lint `PROJECT-NAME` / `CLIENT` + PDFs to `60_90_PROCESSED`. Sync GUBERNATIO/documents for **both original and raster SHA** if both exist. **No invented Layer-2 case briefs.**

### R-10 — SHA-256 dedupe before reconverting
Annexure IV Letter of Offer was **byte-identical** to Rights Issue LOO #9 (Shekar Vislavath). Check SHA before spending another convert.

### R-11 — Quarantine superseded OCR
Move under `99_98_QUARANTINE\YYYY-MM-DD_*` with README, delete-by deadline, calendar 15-min reviews, escalate if not deleted.

### R-12 — Lint before approve
Fix OCR typos (e.g. email `SHEKARAN174` → `SHEKARANI74`), stamp PROJECT / CLIENT.

## 3. Decision tree

```
PDF in 0_01_RAW_PDF
  → Ask engine (Tesseract vs Mistral) unless already named
  → SHA-256 against known APPROVED (skip if duplicate)
  → Convert
  → If Mistral Empty PDF and local text/OCR exists:
        rasterize 200-220dpi as Name_raster.pdf → Mistral --force
  → If NEEDS_REVIEW and draft looks good:
        eye-compare; ask override vs Gemini vs dual-file
  → If raster Mistral worse than native:
        keep native; quarantine raster artifacts
  → If Tesseract-on-raster AWAITING_APPROVAL:
        treat as false-pass; quarantine
  → Lint PROJECT-NAME / CLIENT
  → On Anil "approved": CLI approve + CLEAN FM APPROVED
        + sync GUBERNATIO for original (+ raster SHA if any)
        + PDF to PROCESSED
  → Stop Layer 1 (no invented briefs)
```

## 4. Paths

- Tool home: `D:\satyagraha\VAULT\SLIP_DOCUMENT_PROCESSING\Convert-PDF-TO-MARKDOWN-01`
- Vault root: `D:\satyagraha\VAULT\SLIP_DOCUMENT_PROCESSING`
- CLEAN: `20_03_CLEAN_MARKDOWN`
- NEEDS_REVIEW: `70_99_NEEDS_REVIEW`
- PROCESSED: `60_90_PROCESSED`
- Quarantine: `99_98_QUARANTINE`
- Secrets (names only): `SECRETS.txt` in tool home; firm map under Satyagraha Law Group guides
- GUBERNATIO DB: under `90_00_PROJECT_TOOLING\pdf-to-markdown\` (Document-Hash-Registry-*.sqlite)

## 5. Checklist before next hard scan convert

- [ ] Engine chosen by Anil
- [ ] Secrets present and non-empty (length check only)
- [ ] SHA dedupe against APPROVED set
- [ ] Note page_count / text layer
- [ ] If Empty PDF from Mistral → `_raster` path
- [ ] If fidelity < 0.9 → explain gate; ask override vs Gemini vs dual-file
- [ ] Eye-compare raster vs native before discarding either
- [ ] After approve → CLEAN FM + GUBERNATIO sync (all SHAs) + PROCESSED PDFs
- [ ] Dual-write durable facts to Spock memory + Mnemoverse (`user:anil`, `project:slg-website`)

---

Satyagraha Law Group publishes a SLIP PDF to Markdown Ingestion Tool. It does not publish a library.

**Satyagraha Law Group** · SLIP PDF to Markdown Ingestion Tool · SLIP

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

[https://www.satyagraha.com](https://www.satyagraha.com)

## Convert-run mutex (19-09-2026-21-52-02)

Deployed dual mutex: `CONVERT.lock` + **CONVERT_LEASE**. Module `convert_mutex.py`. CLI `--steal-convert-lock` for stale holders only.
