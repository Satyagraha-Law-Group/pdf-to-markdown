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

- [[README]] — [Product overview](README.md)
- [[Mistral-Engine-Guide]] — [Lawyer user guide](docs/Mistral-Engine-Guide-v1-03-09-2026-04-39-31.md)
- [[Marker-Mistral-Engine]] — [Mistral engine mapping](docs/Marker-Mistral-Engine-v1-03-09-2026-04-05-21.md)
- [[Product-Requirements-Spec]] — [Requirements](docs/Product-Requirements-Spec-v1-02-09-2026-22-55-00.md)
- [[System-Design-Document]] — [Design](docs/System-Design-Document-v1-02-09-2026-22-55-00.md)
- [[Implementation-Plan-Guide]] — [Plan](docs/Implementation-Plan-Guide-v1-02-09-2026-22-55-00.md)
- [[System-Architecture-Diagram]] — [Architecture](docs/System-Architecture-Diagram-v1-02-09-2026-22-55-00.md)
- [[Process-Workflow-Guide]] — [Workflow](docs/Process-Workflow-Guide-v1-02-09-2026-22-55-00.md)
# Satyagraha Law Group

# PDF to Markdown — Lawyer Instruction Guide

**Family:** SLIP — Satyagraha Law Group Legal Intelligence Platform

SLIP PDF to Markdown Ingestion Tool. No Python required after someone has run deploy.

1. Put PDFs in `0_01_RAW_PDF`.
2. Ask whoever keeps the machine to run convert, or open the web page if it is running.
3. Open `20_03_CLEAN_MARKDOWN`. A convert is **staging** until a Satyagraha lawyer runs approve; only then is GUBERNATIO closed for downstream work.

Same PDF under a new name is converted **once**. Duplicates go to `50_90_DUPLICATES` and are never deleted by the tool.

After SHA-256, **GUBERNATIO** (Latin: governance, steering, direction, administration) is the gate: already DONE means duplicate, and the identity registry is updated second. A Mistral convert takes a short key lease so two lawyers cannot spend the same API key at once; if that lease is held you will see **HALT** and the PDF stays in RAW. Local Tesseract does not take a lease. A file over 100 pages or 100 MB is split at Ready for Doc Link. You still get **one** markdown. The extra part files are deleted. The original PDF sits in its own folder under `60_90_PROCESSED`.

![Convert happy-path flowchart](docs/Convert-Pipeline-Flowchart-v1-03-09-2026-06-48-52.png)

- Tool folder: `D:\satyagraha\VAULT\Satyagraha Law Group\SLIP_DOCUMENT_PROCESSING\Convert-PDF-TO-MARKDOWN-01`
- SLIP root: `D:\satyagraha\VAULT\Satyagraha Law Group\SLIP_DOCUMENT_PROCESSING`
- Public repo: https://github.com/Satyagraha-Law-Group/pdf-to-markdown

For an LLM: open `playbooks/01-Deploy-Scaffold.md` and point it at that GitHub URL.

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
