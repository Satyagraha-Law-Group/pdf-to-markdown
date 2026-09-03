# Satyagraha Law Group

**PDF to Markdown**  ·  SLIP  ·  Legal Research  ·  Practitioner-Scholar

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

[https://www.satyagraha.com](https://www.satyagraha.com)

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

---
<!-- Related documents: Obsidian wiki links AND GitHub relative links -->
<!-- [[README]] [[Slip-Markdown-Glossary]] [[Mistral-Engine-Guide]] [[Process-Workflow-Guide]] [[System-Architecture-Diagram]] -->

## Related documents

- [[README]] — [Product overview](../README.md)
- [[Slip-Markdown-Glossary]] — [Glossary](Slip-Markdown-Glossary-v1-03-09-2026-08-35-00.md)
- [[Mistral-Engine-Guide]] — [Lawyer user guide](Mistral-Engine-Guide-v1-03-09-2026-04-39-31.md)
- [[Process-Workflow-Guide]] — [Workflow](Process-Workflow-Guide-v1-02-09-2026-22-55-00.md)
- [[System-Architecture-Diagram]] — [Architecture](System-Architecture-Diagram-v1-02-09-2026-22-55-00.md)
- [[Convert-Pipeline-Flowchart]] — [Happy-path flowchart](Convert-Pipeline-Flowchart-v1-03-09-2026-06-48-52.html)

# Slip Markdown Glossary

Terms for Satyagraha Law Group PDF to Markdown (SLIP). Filename is not identity.

## GUBERNATIO

**GUBERNATIO** is the proper Latin noun meaning *the system of governance, steering, direction, and administration*.

In this product it is a SQLite table named `GUBERNATIO` inside the Document-Hash-Registry database. After SHA-256, every file sighting (including a hash already `DONE`) appends a row with **this filename** and the same kind of fields as the identity registry: status, engine, page count, output path, host, agent, step, timestamps.

`documents` stays **one row per SHA-256**. GUBERNATIO is the **entry gate**. After SHA-256, convert asks GUBERNATIO “already DONE?” If yes, the file is parked as a duplicate and the identity registry is updated second. `documents` is identity only.

After convert finishes, both `documents` and `GUBERNATIO` are updated.

List it:

```text
slip-pdf-md registry gubernatio --vault "PATH/TO/SLIP_DOCUMENT_PROCESSING"
```

## Identity and routing

| Term | Meaning |
| --- | --- |
| SHA-256 | Hash of the PDF **bytes**. The document. A rename months later is still the same file. |
| Document-Hash-Registry | Living sqlite under `90_00_PROJECT_TOOLING/pdf-to-markdown/`. One `documents` row per hash. Stamp is first-created time. |
| `.bak` | Sibling backup of that sqlite, rewritten after every successful change. |
| sighting | One observation of a filename for a hash. Thin table. GUBERNATIO is the rich steering table. |
| AWAITING_APPROVAL | Convert finished. Markdown is staged. Identity registry says processed. GUBERNATIO loop is **not** closed. |
| APPROVED | A Satyagraha lawyer closed the GUBERNATIO loop. Downstream may use the file. |
| DONE | Legacy closed loop (already approved). Treated like APPROVED. |
| NEEDS_REVIEW | The engine will not stand behind the extract. |
| `--force` | Reconvert even when the hash is already DONE. |
| `[DUP]` | Terminal notice for a DONE hash. Filename is not identity. |


## Mistral key lease

Lawyers and agents (Claude, ChatGPT, Grok, Gemini, Hermes, a VPS) must not dual-use the **same** Mistral API key. Different keys may run in parallel. Local Tesseract does **not** take a lease.

| Term | Meaning |
| --- | --- |
| Key fingerprint | SHA-256 of the API key. GUBERNATIO stores this, never the raw key. |
| Sentinel | Zero-byte exclusive-create file **next to** the sqlite (not inside it). Exact name: `SLG-pdf_to_md_file_naming_convention.text` |
| RUNNING | This fingerprint is converting. Another job using the same key **HALT**s. RAW is not moved. |
| TTL | Default 15 minutes. Override with `SLIP_KEY_LEASE_SECONDS` in tests. An expired RUNNING lease is free; the next lawyer is not stuck. |
| Heartbeat | Written after each part convert so a long split job does not expire mid-run. |
| Release | Always, on success and on NEEDS_REVIEW. Does not mark the file DONE. |
| HALT | Status when the same key is already RUNNING and unexpired. |


## Lawyer approval (human in the loop)

Convert is only staging. `documents` (identity) records that the file was processed. **GUBERNATIO is not closed** until a lawyer approves.

```text
slip-pdf-md report --vault "PATH"
slip-pdf-md approve --vault "PATH" --sha256 SHA256 --by "Lawyer Name"
```

## Remote API keys (never stored)

GUBERNATIO stores a SHA-256 **fingerprint** and an `api_provider` (`mistral` today; `docling`, `google`, `claude`, `hermes`, `reducto` later). A raw key is refused. Same fingerprint is exclusive. Different fingerprints may run in parallel. Local Tesseract takes no lease.

## Folders (do not rename)

| Folder | Role |
| --- | --- |
| `0_01_RAW_PDF` | Drop zone. |
| `10_02_READY_FOR_DOCLING` | Queue. New files move here **before** OCR, as `YYYY-MM-DD / Stem / Stem.pdf`. |
| `20_03_CLEAN_MARKDOWN` | Faithful Layer 1 markdown. One merged file even when the PDF was split. |
| `50_90_DUPLICATES` | Same SHA-256, dated buckets. Whole file, unchanged. No split. |
| `60_90_PROCESSED` | Successful unique originals: `YYYY-MM-DD / Stem / Stem.pdf`. |
| `70_99_NEEDS_REVIEW` | Extracts the engine will not stand behind. |
| `90_00_PROJECT_TOOLING` | Registry, GUBERNATIO, logs, session summaries. |

## Split at READY

| Term | Meaning |
| --- | --- |
| Cap | 100 pages or 100 MB. No convert job may exceed either. |
| Part | A split PDF of at most 100 pages and 100 MB, in `Stem / parts /`. |
| Merge | Part markdown joined into one file. `## Page N` continues 1..N. |
| Stem folder | Folder named as the filename without extension. |

## Engines

| Term | Meaning |
| --- | --- |
| Local Tesseract | `--engine pymupdf`. Nothing uploaded. Privileged papers stay here. |
| Mistral AI | `--engine mistral`. Uploads the PDF. Tables and formulas. Needs `SECRETS.txt`. |
| `SECRETS*` | Gitignored real keys. `SECRETS.example` is the dummy template. |

## Memory files (fallback for the assistant)

Do not pile every fact into the assistant's internal memory. The durable copies live in the tool folder:

| File | Role |
| --- | --- |
| `Tool-Creation-Memory-v1-03-09-2026-05-05-24.md` | Tool-folder / global standing rules and architecture. Stamp is first-created time. |
| `Session-Learning-Notes-v1-03-09-2026-05-05-24.md` | Session-specific notes for this convert work. Stamp is first-created time. |

If the assistant's memory is clogged, read those two files.

---

Satyagraha Law Group publishes a SLIP PDF to Markdown Ingestion Tool. It does not publish a library.

**Satyagraha Law Group**  ·  SLIP PDF to Markdown Ingestion Tool  ·  SLIP

Founded by Anil B. (Lawyer), Satyagraha Law Group provides legal services for seekers looking for help by searching for Corporate Law, Civil Law, Criminal Law, Writs, High Court Lawyer, NRI Lawyer, Lawyer In Hyderabad, India.

Need Legal Help. [Click here](https://calendly.com/anil-satyagraha/15min).

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

[https://www.satyagraha.com](https://www.satyagraha.com)

This site is built from **real-world experience helping clients seeking Justice**, case by case — based on our work involving Legal Research, Drafting, Pleadings, Representation and beyond.

Explore further: [Website](https://www.satyagraha.com) · [YouTube](https://www.youtube.com/@satyagrahalawgroup2002) · [Udemy Courses](https://www.udemy.com/user/anil-b-23/) · [LinkedIn](https://www.linkedin.com/in/anilsatyagraha/) · [Facebook](https://www.facebook.com/satyagrahalawgroup) · [Twitter / X](https://twitter.com/_satyagraha) · [WordPress](https://satyagrahalawgroup.wordpress.com/) · [Instagram](https://www.instagram.com/satyagrahalawgroup/) · [Pinterest](https://in.pinterest.com/satyagrahalawgroup/) · [Tumblr](https://www.tumblr.com/blog/satyagrahalawgroup) · [SoundCloud](https://soundcloud.com/satyagrahalawgroup) · [Podomatic](http://anil-satyagraha.podomatic.com/) · [Newsletter](https://satyagraha.substack.com/) · [WhatsApp](https://api.whatsapp.com/send?phone=917095776633)

Need Legal Help? [Click Here For Next Steps](https://calendly.com/anil-satyagraha/15min)
