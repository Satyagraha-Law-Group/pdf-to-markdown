# Satyagraha Law Group

**SLIP PDF to Markdown Ingestion Tool**  ·  SLIP  ·  Legal Research  ·  Practitioner-Scholar

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

[https://www.satyagraha.com](https://www.satyagraha.com)

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

---

# Error Code Catalog

Satyagraha Law Group — SLIP PDF to Markdown Ingestion Tool.
Classified errors. New features register a code here before they ship.

- written_at: 2026-09-03T13:38:55+05:30
- codes: 18

| Error code | Type | Category | Error message | Suggested resolution |
| --- | --- | --- | --- | --- |
| `SLIP-E-001` | registry | **HIGH** | Live sqlite failed integrity_check and the sibling backup could not repair it. | Run slip-pdf-md registry restore --vault PATH. If both copies are gone, rebuild from markdown front matter. |
| `SLIP-E-002` | secrets | **HIGH** | A remote-API convert was requested but no API key is available. | Put the key in gitignored SECRETS.txt or the environment. Local Tesseract needs no key. |
| `SLIP-E-003` | security | **HIGH** | A raw API key was offered to GUBERNATIO. Only a SHA-256 fingerprint is stored. | Pass api_key_fingerprint(key), never the secret. Confirm SECRETS.txt is gitignored. |
| `SLIP-E-004` | lease | **HIGH** | Convert HALTed because the same API-key fingerprint is already in use. | Wait until the other agent finishes, or use a different key. Abandoned leases free after 15 minutes. RAW is unmoved. |
| `SLIP-E-005` | fidelity | **HIGH** | Markdown failed the fidelity gate against the PDF. Status is NEEDS_REVIEW. | Open the NEEDS_REVIEW note. Repair citations or reconvert with the other engine. Do not treat the file as approved. |
| `SLIP-E-006` | convert | **HIGH** | Conversion raised an exception. The PDF is routed to NEEDS_REVIEW. | Read the .error.md next to the file. Fix the engine or the PDF and convert again. |
| `SLIP-E-007` | lease | **HIGH** | The key-lease sentinel file could not be created exclusively. | Confirm the sentinel name is exactly SLG-pdf_to_md_file_naming_convention.text next to the sqlite, not inside it. |
| `SLIP-E-008` | approve | **HIGH** | Approve was called on a document whose status cannot be closed. | Only AWAITING_APPROVAL or NEEDS_REVIEW may be approved. Check GUBERNATIO for the current status. |
| `SLIP-E-010` | duplicate | **MEDIUM** | This PDF bytes were already extracted. The inbound file is parked in DUPLICATES. | Use the canonical markdown. Do not reconvert unless a lawyer passes --force and chooses an engine. |
| `SLIP-E-011` | split | **MEDIUM** | The PDF exceeded 100 pages or 100 MB and was split at READY. | This is expected. Confirm one merged markdown and that part PDFs were deleted after a clean convert. |
| `SLIP-E-012` | lease | **MEDIUM** | An expired RUNNING lease was treated as free so the next convert could proceed. | No action if the previous agent finished. If two converts overlapped, inspect GUBERNATIO lease rows. |
| `SLIP-E-013` | output | **MEDIUM** | The destination markdown already existed; a SHA-prefixed filename was used. | Open the SHA-prefixed file. Consider --force only after a lawyer chooses the engine. |
| `SLIP-E-014` | tables | **MEDIUM** | One or more tables were not recovered into markdown pipe tables. | Inspect the page. Use Mistral for scans, or repair with the table-recovery playbook. |
| `SLIP-E-015` | engine | **MEDIUM** | Tesseract is not installed. Scanned pages will not OCR on the local engine. | Install Tesseract, or convert with Mistral AI (the PDF is uploaded). |
| `SLIP-E-016` | backup | **MEDIUM** | The live registry was missing and was restored from the sibling .bak. | Confirm Document-Hash-Registry-vN-stamp.sqlite and its .bak both exist after the restore. |
| `SLIP-E-020` | empty | **LOW** | A PDF page had no extractable text after OCR. | Confirm the scan is readable. Reconvert with the other engine if the page should have text. |
| `SLIP-E-021` | naming | **LOW** | A generated artifact did not match the three-word filename convention. | Use Word1-Word2-Word3-vN-DD-MM-YYYY-HH-MI-SS. Do not rename pipeline folders. |
| `SLIP-E-022` | wiki | **LOW** | A documentation wiki link does not resolve to a file. | Add the file or the WIKI_CATALOG entry, then re-run the user-guide integrity check. |

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
