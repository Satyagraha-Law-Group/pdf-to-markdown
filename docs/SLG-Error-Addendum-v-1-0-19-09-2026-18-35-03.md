# Satyagraha Law Group

**PDF to Markdown** · SLIP · Legal Research · Practitioner-Scholar

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

[https://www.satyagraha.com](https://www.satyagraha.com)

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

---

# Error / symptom addendum — convert learnings `19-09-2026-18-35-03`

Extends `Error-Code-Catalog-v1-03-09-2026-12-25-29` and supersedes `SLG-Error-Addendum-v-1-0-19-09-2026-14-49-22`.  
Full narrative: `SLG-Convert-Learnings-v-1-0-19-09-2026-18-35-03.md`.

| Code | Severity | Symptom | Suggested resolution |
| --- | --- | --- | --- |
| SLIP-E-023 | HIGH | Mistral convert writes Empty PDF / page_count 0 while PDF opens locally | Rasterize pages 200-220 dpi → `Name_raster.pdf` → convert `--engine mistral --force` |
| SLIP-E-024 | MEDIUM | Fidelity NEEDS_REVIEW (~0.7) on readable cloud OCR | Explain Tesseract-overlap gate; ask approve / Gemini / dual-file; avoid useless force loops |
| SLIP-E-025 | HIGH | Gemini `finish_reason=RECITATION` empty page | Re-OCR that page with Tesseract or alternate vision; mark hybrid in front matter |
| SLIP-E-026 | HIGH | `GEMINI_API_KEY` / `MISTRAL_API_KEY` listed but length 0 or dummy | Reload via secret-request / dated SECRETS backup into env; never echo value |
| SLIP-E-027 | MEDIUM | Model 404 / retired (e.g. gemini-2.0-flash) | List models for the key; prefer current lite/flash that accepts new users |
| SLIP-E-028 | MEDIUM | Gemini/Mistral 503 high demand | Exponential backoff; try lite model; serialize page batches |
| SLIP-E-029 | MEDIUM | `approve` closed registry but CLEAN still AWAITING_APPROVAL | Patch CLEAN front matter; verify path was canonical `.md` not raster-only |
| SLIP-E-030 | LOW | CopyToBox/FromBox refuses vault path | Stage under Downloads/Documents then Shell copy into vault |
| SLIP-E-031 | HIGH | Raster Mistral fidelity **worse** than native Mistral | Eye-compare; keep native; quarantine raster MD/PDF; do not auto-prefer newer |
| SLIP-E-032 | HIGH | Tesseract-on-raster false-pass `AWAITING_APPROVAL` | Quarantine; gate is self-compare — not a real approval win |
| SLIP-E-033 | MEDIUM | PowerShell convert hangs on interactive engine prompt | Pipe empty stdin; pass `--engine`; set API key in env before spawn |
| SLIP-E-034 | MEDIUM | Mid-name `.raster.` multi-dot filenames | Rename to `_raster` before real extension; standing naming rule |
| SLIP-E-035 | MEDIUM | GUBERNATIO original SHA still NEEDS_REVIEW after CLEAN APPROVED | Sync documents/GUBERNATIO for original **and** raster SHA on approve |
| SLIP-E-036 | LOW | Lookalike PDF reconverted unnecessarily | SHA-256 dedupe against APPROVED set before convert (Annexure IV = LOO #9 case) |

---

Satyagraha Law Group publishes a SLIP PDF to Markdown Ingestion Tool. It does not publish a library.

**Satyagraha Law Group** · SLIP PDF to Markdown Ingestion Tool · SLIP

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

[https://www.satyagraha.com](https://www.satyagraha.com)
