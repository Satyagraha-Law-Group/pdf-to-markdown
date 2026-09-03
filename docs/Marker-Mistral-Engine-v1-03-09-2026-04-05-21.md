# Satyagraha Law Group

**PDF to Markdown**  ·  SLIP  ·  Legal Research  ·  Practitioner-Scholar

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

[https://www.satyagraha.com](https://www.satyagraha.com)

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

---
<!-- Related documents: Obsidian wiki links AND GitHub relative links -->
<!-- [[README]] [[Mistral-Engine-Guide]] [[Marker-Mistral-Engine]] [[Product-Requirements-Spec]] [[System-Design-Document]] [[Implementation-Plan-Guide]] [[System-Architecture-Diagram]] [[Process-Workflow-Guide]] -->

## Related documents

- [[README]] — [Product overview](../README.md)
- [[Mistral-Engine-Guide]] — [Lawyer user guide](Mistral-Engine-Guide-v1-03-09-2026-04-39-31.md)
- [[Marker-Mistral-Engine]] — [Mistral engine mapping](Marker-Mistral-Engine-v1-03-09-2026-04-05-21.md)
- [[Product-Requirements-Spec]] — [Requirements](Product-Requirements-Spec-v1-02-09-2026-22-55-00.md)
- [[System-Design-Document]] — [Design](System-Design-Document-v1-02-09-2026-22-55-00.md)
- [[Implementation-Plan-Guide]] — [Plan](Implementation-Plan-Guide-v1-02-09-2026-22-55-00.md)
- [[System-Architecture-Diagram]] — [Architecture](System-Architecture-Diagram-v1-02-09-2026-22-55-00.md)
- [[Process-Workflow-Guide]] — [Workflow](Process-Workflow-Guide-v1-02-09-2026-22-55-00.md)
# Marker Mistral Engine

Satyagraha Law Group — PDF to Markdown (SLIP)

This note mirrors the [Obsidian OCR-AI (marker-api) plugin](https://community.obsidian.md/plugins/marker-api) README, mapped onto `slip-pdf-md`.

## Introduction

The Obsidian plugin converts PDFs to rich Markdown by calling Marker (self-hosted, datalab.to, or a local Python API) **or** MistralAI OCR. It recommends MistralAI: a free API key, no GPU, strong tables and formulas.

SLIP already converts locally with PyMuPDF + Tesseract (`--engine pymupdf`). That path never leaves the machine. This engine adds the plugin's MistralAI option as `--engine mistral`.

> [!IMPORTANT]
> `--engine mistral` needs a MistralAI API key. Without it, use the default local engine. The PDF is uploaded to Mistral's servers for processing.

Related services:

- [Marker Project](https://github.com/VikParuchuri/marker) (AI PDF conversion + Python API)
- [datalab.to](https://www.datalab.to/) (hosted Marker API)
- [Marker API Docker](https://hub.docker.com/r/wirawan/marker-api) (self-host, NVIDIA GPU)
- [Marker API](https://github.com/adithya-s-k/marker-api)
- [MistralAI](https://console.mistral.ai/) (OCR API used here)
- [Obsidian OCR-AI source](https://github.com/L3-N0X/obsidian-marker)

## Features

- OCR of scanned PDFs into Markdown (tables, formulas, reading order)
- Same Mistral call sequence as the plugin: upload file (`purpose=ocr`) → signed URL → `mistral-ocr-latest` → optional delete
- SLIP routing unchanged: SHA-256 identity, duplicates, `--force`, citation repair, 90% sample-page fidelity gate, run log
- Page bodies land under `## Page N` like the local engine
- `llm_*` stay 0 (Mistral OCR is billed per page). `mistral_pages_processed` is logged
- Default convert is still local. Mistral is opt-in

## Why this engine

1. The plugin's own testing ranks MistralAI first for quality versus easy setup
2. No GPU, no Docker, no Marker Python server
3. Useful when Tesseract smears commentary, or when a real grid/formula page needs a second pass
4. Legal default stays on-box: nothing is uploaded unless `--engine mistral` is set

## Requirements

1. Working `slip-pdf-md` install (Python 3.11+, PyMuPDF, Tesseract for the default engine and the fidelity gate)
2. A MistralAI API key from [console.mistral.ai/api-keys](https://console.mistral.ai/api-keys)
3. Network access to `https://api.mistral.ai`

## Setup

1. Create a MistralAI API key
2. Set it in the environment (never commit it, never pass it on the CLI):

```text
setx MISTRAL_API_KEY "your-key"
```

Open a new terminal so the variable is visible. `slip-pdf-md doctor --vault "..."` reports whether the key is set. Missing key is not a doctor failure; it only blocks `--engine mistral`.

3. Convert one file:

```text
slip-pdf-md convert --vault "D:\satyagraha\VAULT\Satyagraha Law Group\SLIP_DOCUMENT_PROCESSING" --input "path\to\file.pdf" --engine mistral --force
```

Aliases: `mistral`, `mistralai`, `mistral-ocr`.

### Which solution should I use?

| Solution | Pros | Cons |
| --- | --- | --- |
| **Local PyMuPDF + Tesseract (default)** | Nothing leaves the machine. No API cost. Already verified on the Arbitration scan (99.1% companion recall). | Weaker on formulas, dense grids, and some photocopies |
| **MistralAI OCR (`--engine mistral`)** | Same path the Obsidian plugin recommends. Strong tables and formulas. API key only. | Uploads the PDF to Mistral (stored at least 24 hours unless deleted). Needs network. Per-page billing on Mistral's side |
| **Hosted Marker / datalab.to** | Marker-quality, no GPU | Paid. Not wired in this drop |
| **Self-hosted Marker (Docker / Python API)** | Full control, no cloud upload | GPU/CPU heavy. Not wired in this drop |

> [!NOTE]
> **MistralAI privacy.** The PDF is uploaded for OCR. Mistral may store it at least 24 hours. SLIP deletes the upload after conversion unless `SLIP_MISTRAL_DELETE_UPLOAD=0`. For privileged or sealed papers, stay on the local engine.

## Settings

Mapped from the plugin's MistralAI settings. Keys are environment variables, not a GUI.

| Setting | Default | Description |
| --- | --- | --- |
| `MISTRAL_API_KEY` (or `MISTRALAI_API_KEY`) | unset | API key. Required for `--engine mistral` |
| `--engine` | `pymupdf` | `pymupdf` / `mistral` / `mistralai` / `mistral-ocr` |
| `SLIP_MISTRAL_INCLUDE_IMAGES` | `0` | `1` asks Mistral for `include_image_base64` (plugin: Extract content ≠ text only) |
| `SLIP_MISTRAL_IMAGE_LIMIT` | `0` | Max images (0 = no limit). Plugin: Image limit |
| `SLIP_MISTRAL_IMAGE_MIN_SIZE` | `0` | Min image height/width. Plugin: Image minimum size |
| `SLIP_MISTRAL_DELETE_UPLOAD` | `1` | Delete the uploaded file after OCR. Plugin default is keep; SLIP default is delete |
| Paginate | always | SLIP already inserts `## Page N`. Plugin's `paginate` toggle (`---`) is not used |
| `--force` | off | Reconvert a DONE SHA |
| `--repair-citations` | off | Conservative ATR→AIR after OCR |
| Write metadata | always | SLIP YAML front matter |

## How the call works

Matches `src/converters/mistralaiConverter.ts` in [L3-N0X/obsidian-marker](https://github.com/L3-N0X/obsidian-marker):

1. `POST /v1/files` with `purpose=ocr`
2. `GET /v1/files/{id}/url`
3. `POST /v1/ocr` with `model=mistral-ocr-latest`, `document.type=document_url`, `include_image_base64`
4. Map `pages[].markdown` into a SLIP ConversionResult
5. `DELETE /v1/files/{id}` when delete-upload is on

Official OCR docs: [Document AI OCR processor](https://docs.mistral.ai/studio/document-processing/basic_ocr).

## Usage

```text
slip-pdf-md doctor --vault "<SLIP root>"
slip-pdf-md convert --vault "<SLIP root>" --input "<pdf>" --engine mistral --force --repair-citations
```

Do not point this at a privileged scan until the key, billing, and privacy note are accepted. The local Tesseract path remains the default for the vault.

## Troubleshooting

- `MistralAI engine needs MISTRAL_API_KEY` — key missing in this terminal
- HTTP 401 — bad or revoked key
- HTTP 429 / 402 — rate or billing limit on the Mistral account
- Empty markdown / NEEDS_REVIEW — API returned no pages; check `70_99_NEEDS_REVIEW`
- Fidelity gate fail — sample-page Tesseract recall under 90%. Read the `.fidelity.md` note. Not always a Mistral failure (Tesseract can disagree with a better OCR)
- Large PDFs — Mistral has document size/page limits; split if the API refuses the upload

## Acknowledgements

- [Obsidian OCR-AI / marker-api](https://community.obsidian.md/plugins/marker-api) by l3-n0x
- [Marker](https://github.com/VikParuchuri/marker)
- [MistralAI OCR](https://mistral.ai/)

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
