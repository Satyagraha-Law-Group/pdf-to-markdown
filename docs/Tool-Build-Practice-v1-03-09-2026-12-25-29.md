# Satyagraha Law Group

**SLIP PDF to Markdown Ingestion Tool**  ·  SLIP  ·  Legal Research  ·  Practitioner-Scholar

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

[https://www.satyagraha.com](https://www.satyagraha.com)

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

---

# Tool Build Practice

Best practices learned while building the SLIP PDF to Markdown Ingestion Tool. Apply these to every new Satyagraha Law Group tool.

1. **One sqlite book.** Identity, GUBERNATIO, TEST_CASES, TEST_RUNS, PROCESS_RUNS, and ERROR_CODES live together and share the sibling `.bak`.
2. **Tests upsert the catalog first.** A new test case is a row in TEST_CASES (`TC-XXX-NNN` stays stable). Reports are generated from the tables, not from a disposable pytest dump.
3. **Two reports every run.** Test-Suite-Summary (totals, recent runs) and Test-Suite-Detailed (every case plus files processed that day).
4. **Process metrics on every convert.** Day, filename, PDF pages, markdown pages, API key type (`local_tesseract` or provider), status, approved yes/no.
5. **Error codes before features ship.** `SLIP-E-NNN`, type, HIGH/MEDIUM/LOW, message, suggested resolution. Publish Error-Code-Catalog markdown and HTML.
6. **Satyagraha header and footer** on every doc and report (Rig Veda, Aristotle, research disclaimer, site index / Calendly / channels).
7. **Wiki graph.** Related files use Obsidian `[[Name]]` plus relative hrefs so HTML readers can click through.
8. **Three-word names.** `Word1-Word2-Word3-vN-DD-MM-YYYY-HH-MI-SS`. Living files keep the first-created stamp.
9. **Never store raw API keys.** Fingerprint plus provider only. Sentinel lease for remote APIs.
10. **Memory.** Update Tool-Creation-Memory (global) and Session-Learning-Notes (session) in place after each slice. Git only after Anil approves.
11. **Engine choice.** Before convert (including `--force`), ask 1 Local Tesseract or 2 Mistral AI. Do not pick `--engine` yourself.

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
