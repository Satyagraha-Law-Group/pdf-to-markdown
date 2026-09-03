# SKILL: Convert PDFs to Markdown

**Satyagraha Law Group** — PDF to Markdown  
**Playbook:** 02-Convert-Documents  
**Depends on:** 01-Deploy-Scaffold

## Goal

Convert every new PDF in `0_01_RAW_PDF` into Layer 1 Markdown in `20_03_CLEAN_MARKDOWN`. Same bytes, different name = once.

## Parameters

| Name | Required | Default |
| --- | --- | --- |
| `{{SLIP_ROOT}}` | yes | the folder that contains `0_01_RAW_PDF` |
| `{{PYTHON}}` | no | `py -3` / `python3` |
| `{{REPAIR_CITATIONS}}` | no | `false` |

## Steps

1. Confirm PDFs are in `{{SLIP_ROOT}}/0_01_RAW_PDF`. Do not rename that folder.
2. Run doctor if Tesseract status is unknown.
3. Convert:

```text
{{PYTHON}} -m slip_pdf_md convert --vault "{{SLIP_ROOT}}"
```

If `{{REPAIR_CITATIONS}}` is true, add `--repair-citations`. That maps ATR→AIR (never ATTRIBUTE), L]→LJ, AIL)→All., Caleutta, Jnarkhand, I71-B→171-B.

4. Read the CLI summary line `converted=… duplicates=… needs_review=… halted=…`. `HALTED` means another job holds the same Mistral key lease. The PDF stayed in RAW. Wait or use a different key. Local Tesseract never HALTs for the lease.
5. Converted files are AWAITING_APPROVAL. Markdown is staged. GUBERNATIO is not closed until a lawyer runs slip-pdf-md approve. Use slip-pdf-md report to list them.
6. Tell the lawyer: open `{{SLIP_ROOT}}/20_03_CLEAN_MARKDOWN`.
7. Do not write case briefs. `30_04_CASE_BRIEFS` and `40_05_PROJECT_BRIEFS` stay empty.

## Routing you must honour

- After SHA-256, ask **GUBERNATIO** first (not `documents`). Already DONE → `50_90_DUPLICATES` + sidecar, then update the identity registry. **Do not convert again. Do not delete.**
- New hash, Mistral engine: take the key lease (sentinel `SLG-pdf_to_md_file_naming_convention.text` next to GUBERNATIO). If the same key is RUNNING, return HALT and leave RAW. Local Tesseract skips the lease.
- New SHA-256 → MOVE `10_02_READY_FOR_DOCLING` → Markdown in `20_03_CLEAN_MARKDOWN` → original to `60_90_PROCESSED`. Release the Mistral lease when finished.
- Failure / empty extract → `70_99_NEEDS_REVIEW` and release the lease.

## Verification

- Each `DONE` Markdown has YAML front matter with `document_type`, `source_file`, `source_sha256`, `processing_status`, `engine`, `page_count`, `converted_at`.
- Body uses `## Page N`.
- Retries of a `DONE` hash did not create a second Markdown.

## Stop conditions

- Asking you to "just delete the dupes" → refuse, point at playbook 04.
- Asking you to invent table cells → refuse; leave `UNRECOVERED` callouts.

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
