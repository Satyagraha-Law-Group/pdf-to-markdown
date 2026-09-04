# Satyagraha Law Group

**SLIP PDF to Markdown Ingestion Tool**  ·  SLIP  ·  Legal Research  ·  Practitioner-Scholar

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

[https://www.satyagraha.com](https://www.satyagraha.com)

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

---

# Frequently Asked Questions

Satyagraha Law Group — SLIP PDF to Markdown Ingestion Tool.
Plain answers, taken from what the test suite actually proves.

## 1. What does this tool do?

It is the SLIP PDF to Markdown Ingestion Tool for legal PDFs. You put a PDF in, wait, and open a Markdown file. It does not write a case brief and it does not invent table cells.

## 2. How is this repository organized?

It is a Python application. `src/slip_pdf_md` holds the CLI, convert pipeline, engines, registry, and support modules. `tests` proves behavior. `web` holds the FastAPI app. `docs` and `playbooks` hold guides. `scripts` holds helper commands. Packaging and dependencies live in `pyproject.toml`.

## 3. How does the tool know two files are the same?

It hashes the PDF bytes (SHA-256). The filename is not identity. A rename months later is still the same document.

## 4. What is GUBERNATIO?

GUBERNATIO is Latin for governance, steering, direction, and administration. It is the master record after the hash. The identity registry stays one row per hash so several people and devices do not clog it.

## 5. When is a file finished?

When convert succeeds, the markdown is only staged. Status is awaiting approval. A Satyagraha lawyer must approve. Only then is GUBERNATIO closed for downstream work.

## 6. What if I drop the same PDF under a new name?

It is converted once. The second copy is parked in Duplicates with a note pointing at the first markdown. The tool never deletes duplicates.

## 7. Do I have to use Mistral?

No. In a terminal the tool always asks: 1 Local Tesseract (nothing uploaded) or 2 Mistral AI (the PDF is uploaded). Privileged papers stay on the local engine.

## 8. Why is Mistral often better?

For many scans it is faster and cleaner than local Tesseract, especially tables and formulas. It uploads the file, so you choose it on purpose.

## 9. Will tomorrow's Docling or Claude key work the same way?

The lease is built for any remote API. Today the provider is Mistral. The same fingerprint-and-provider slot is ready for Docling, Google, Claude, Hermes, or Reducto.

## 10. Are API keys stored in the database?

Never. GUBERNATIO stores only a SHA-256 fingerprint of the key and which provider it belongs to. A raw key is refused.

## 11. What is the sentinel file?

A zero-byte lock file next to the database named exactly SLG-pdf_to_md_file_naming_convention.text. It stops two jobs using the same key at once.

## 12. What if convert says HALT?

Someone else is already using that same API key. Your PDF stays in RAW. Wait, or use a different key. After fifteen minutes an abandoned lock is treated as free.

## 13. Does local Tesseract take that lock?

No. Only a remote API convert takes a key lease.

## 14. What happens to a very large PDF?

At Ready for Doc Link, a file over 100 pages or 100 MB is split. You still get one markdown. Extra part files are deleted. The original PDF is kept under Processed.

## 15. What is NEEDS_REVIEW?

The engine will not stand behind the extract. The file is routed for a human look. It may be converted again.

## 16. Where do real keys live?

In gitignored SECRETS.txt. The example template never overwrites a real key file. Keys are never committed.

## 17. Can downstream tools use a file that is only processed?

Not as a closed record. Downstream should wait until a lawyer has approved, so GUBERNATIO shows the loop is closed.

## 18. How do I see what is waiting on me?

Run the awaiting-approval report. It lists processed files that a lawyer has not yet approved.

## 19. How do I approve a file?

Run approve with the SHA-256 (or the markdown file) and your name. GUBERNATIO then records who approved and when.

## 20. Will a failed computer lose the register?

The live sqlite has a sibling backup. If the live file is deleted, the next open restores it. If both copies are gone, it can rebuild from markdown front matter.

## 21. Does the markdown remember the source?

Yes. YAML front matter carries the source filename, SHA-256, engine, page count, status, and convert time. The body uses Page N headings.

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
