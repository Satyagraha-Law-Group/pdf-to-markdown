# Satyagraha Law Group

**TOOLS · Convert-PDF-TO-MARKDOWN-01 · CONVERT_LEASE (convert-only)**

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

> Research project — not legal advice, not a solicitation.

---

# Convert-run mutex — convert-only (does not block other tools)

**Stamp:** 19-09-2026-21-55-53

## Org model

| Concern | Store | Scope |
| --- | --- | --- |
| Audit / control of **all** firm jobs | **GUBERNATIO** (append-only ledger) | Org-wide — Convert, Publish-to-Website, Markdown-to-HTML, future tools |
| One Convert process at a time | `CONVERT.lock` + **CONVERT_LEASE**.sqlite | **Convert-PDF-TO-MARKDOWN-01 only** |

## Non-interference rule

While Convert holds its mutex, **Publish-to-Website**, **Markdown-to-HTML**, and any other tool **may run at the same time**. They keep writing/reading **GUBERNATIO** (and their own runtime) without waiting on Convert.

Convert's lease database is **not** the Document-Hash-Registry and **not** the **GUBERNATIO** DB:

`D:\satyagraha\VAULT\TOOLS\_runtime-state\Convert-PDF-TO-MARKDOWN-01\CONVERT_LEASE.sqlite`

Lock file (same folder): `CONVERT.lock`

## Future tools

Each tool that needs single-flight behaviour gets its **own** `_runtime-state\<ToolName>\` lock + lease DB. Do not put tool mutexes inside **GUBERNATIO**. Use **GUBERNATIO** for job audit rows only.

---

Satyagraha Law Group
