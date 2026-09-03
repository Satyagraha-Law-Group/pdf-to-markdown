# Satyagraha Law Group

**SLIP PDF to Markdown Ingestion Tool**  ·  SLIP  ·  Legal Research  ·  Practitioner-Scholar

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

[https://www.satyagraha.com](https://www.satyagraha.com)

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

---

# Lawyer User Guide

This is the hub for converting a PDF to Markdown in the Satyagraha Law Group SLIP vault.
Open this file in Obsidian to see the graph: every wiki link (the bracket-name form) is a real related file.
On the web, use the HTML twin of this guide — each wiki name is a clickable file.

<!-- Related documents: Obsidian wiki links AND relative file links -->
<!-- [[README]] [[Lawyer-User-Guide]] [[Lawyer-Instruction-Guide]] [[Mistral-Engine-Guide]] [[Marker-Mistral-Engine]] [[Product-Requirements-Spec]] [[System-Design-Document]] [[Implementation-Plan-Guide]] [[System-Architecture-Diagram]] [[Process-Workflow-Guide]] [[Slip-Markdown-Glossary]] [[Convert-Pipeline-Flowchart]] [[Slip-Product-Faqs]] [[Test-Suite-Summary]] [[Test-Suite-Detailed]] [[Error-Code-Catalog]] [[Tool-Build-Practice]] [[02-Convert-Documents]] [[01-Deploy-Scaffold]] [[03-Audit-Quality]] [[04-Handle-Duplicates]] [[05-Repair-Markdown]] [[Tool-Creation-Memory]] [[Session-Learning-Notes]] -->

## Related documents

- [[README]] — [Product overview](../README.md)
- [[Lawyer-User-Guide]] — [User guide hub](Lawyer-User-Guide-v1-03-09-2026-12-13-51.md)
- [[Lawyer-Instruction-Guide]] — [Lawyer instruction](../Lawyer-Instruction-Guide.md)
- [[Mistral-Engine-Guide]] — [Mistral engine guide](Mistral-Engine-Guide-v1-03-09-2026-04-39-31.md)
- [[Marker-Mistral-Engine]] — [Mistral engine mapping](Marker-Mistral-Engine-v1-03-09-2026-04-05-21.md)
- [[Product-Requirements-Spec]] — [Requirements](Product-Requirements-Spec-v1-02-09-2026-22-55-00.md)
- [[System-Design-Document]] — [Design](System-Design-Document-v1-02-09-2026-22-55-00.md)
- [[Implementation-Plan-Guide]] — [Plan](Implementation-Plan-Guide-v1-02-09-2026-22-55-00.md)
- [[System-Architecture-Diagram]] — [Architecture](System-Architecture-Diagram-v1-02-09-2026-22-55-00.md)
- [[Process-Workflow-Guide]] — [Workflow](Process-Workflow-Guide-v1-02-09-2026-22-55-00.md)
- [[Slip-Markdown-Glossary]] — [Glossary](Slip-Markdown-Glossary-v1-03-09-2026-08-35-00.md)
- [[Convert-Pipeline-Flowchart]] — [Pipeline flowchart](Convert-Pipeline-Flowchart-v1-03-09-2026-06-48-52.html)
- [[Slip-Product-Faqs]] — [FAQs](Slip-Product-Faqs-v1-03-09-2026-12-01-53.md)
- [[Test-Suite-Summary]] — [Test suite summary](Test-Suite-Summary-v1-03-09-2026-12-01-53.md)
- [[Test-Suite-Detailed]] — [Detailed test report](Test-Suite-Detailed-v1-03-09-2026-12-25-29.md)
- [[Error-Code-Catalog]] — [Error code table](Error-Code-Catalog-v1-03-09-2026-12-25-29.md)
- [[Tool-Build-Practice]] — [Tool-building best practices](Tool-Build-Practice-v1-03-09-2026-12-25-29.md)
- [[02-Convert-Documents]] — [Convert playbook](../playbooks/02-Convert-Documents.md)
- [[01-Deploy-Scaffold]] — [Deploy playbook](../playbooks/01-Deploy-Scaffold.md)
- [[03-Audit-Quality]] — [Audit playbook](../playbooks/03-Audit-Quality.md)
- [[04-Handle-Duplicates]] — [Duplicates playbook](../playbooks/04-Handle-Duplicates.md)
- [[05-Repair-Markdown]] — [Repair playbook](../playbooks/05-Repair-Markdown.md)
- [[Tool-Creation-Memory]] — [Tool memory](../Tool-Creation-Memory-v1-03-09-2026-05-05-24.md)
- [[Session-Learning-Notes]] — [Session notes](../Session-Learning-Notes-v1-03-09-2026-05-05-24.md)

## What this product does

[[README]] is the product overview. You drop a PDF in RAW. The tool hashes the bytes,
asks GUBERNATIO whether this file is new, converts it to Markdown, and stages the
result for a lawyer to approve. Filename is not identity. SHA-256 of the PDF bytes is.

Terms live in [[Slip-Markdown-Glossary]]. The pipeline picture is [[Convert-Pipeline-Flowchart]].
Requirements are [[Product-Requirements-Spec]]. Design is [[System-Design-Document]].
Architecture is [[System-Architecture-Diagram]]. The implementation sequence is [[Implementation-Plan-Guide]].

## Convert a PDF

Day-to-day steps are in [[02-Convert-Documents]]. First-time folders are [[01-Deploy-Scaffold]].
Quality after convert is [[03-Audit-Quality]]. A second copy of the same bytes is [[04-Handle-Duplicates]].
Repair of already-written Markdown is [[05-Repair-Markdown]]. The narrative flow is [[Process-Workflow-Guide]].

Before every convert the tool asks which engine:

- `1` Local Tesseract — nothing is uploaded
- `2` Mistral AI — the PDF is uploaded. Details in [[Mistral-Engine-Guide]] and [[Marker-Mistral-Engine]].

```text
slip-pdf-md convert --vault "D:\satyagraha\VAULT\Satyagraha Law Group\SLIP_DOCUMENT_PROCESSING"
```

## Token usage for each convert

Each PDF-to-Markdown run stores **token usage for that file** in four places:

- the identity table `documents.token_usage` (latest convert of this SHA-256)
- **GUBERNATIO** `token_usage` on the convert row (this run)
- Conversion-Run-Log and Conversion-Runs-Journal next to the registry
- YAML front matter `token_usage` on the Markdown itself, plus the session convert summary

Local Tesseract uses zero LLM tokens. The column still records `markdown_tokens_estimate`
(output size, chars/4) and `equivalent_internal_total_tokens` (1,105 vision tokens per page
plus that markdown estimate). Mistral OCR is billed per page: `mistral_pages_processed`.

Inspect:

```text
slip-pdf-md registry gubernatio --vault PATH
```

## GUBERNATIO

GUBERNATIO is the Latin noun for the system of governance, steering, direction, and administration.
It is the entry gate after SHA-256. One row per file-event (this filename, this host, this agent,
this step). `documents` stays one row per hash.

A successful convert stages Markdown as `AWAITING_APPROVAL`. The loop is not closed until a
Satyagraha lawyer runs `slip-pdf-md approve`. Then status is `APPROVED`.
Lawyer-facing command notes are in [[Lawyer-Instruction-Guide]].

## Test runs and error codes

TEST_CASES is the source of truth for every test scenario. New tests upsert that table first.
Each pytest run appends TEST_RUNS / TEST_RESULTS and republishes [[Test-Suite-Summary]] and [[Test-Suite-Detailed]].
Each convert appends PROCESS_RUNS: the day, the filename, PDF pages, markdown pages, API key type, and whether a lawyer has approved.
Classified product errors live in [[Error-Code-Catalog]] (HIGH / MEDIUM / LOW). New features register a code there.
How we build tools this way is [[Tool-Build-Practice]].

## Tests, FAQs, memory

Numbered test cases: [[Test-Suite-Summary]]. Plain-English questions: [[Slip-Product-Faqs]].
How the tool was built: [[Tool-Creation-Memory]]. This session: [[Session-Learning-Notes]].

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
