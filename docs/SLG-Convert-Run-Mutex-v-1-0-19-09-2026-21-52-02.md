# Satyagraha Law Group

**TOOLS · Convert-PDF-TO-MARKDOWN-01 · CONVERT_LEASE · GUBERNATIO**

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

> Research project — not legal advice, not a solicitation.

---

# Convert-run mutex (both layers deployed)

**Stamp:** 19-09-2026-21-52-02  
**Module:** `src/slip_pdf_md/convert_mutex.py`  
**CLI:** `slip-pdf-md convert` acquires before work; `--steal-convert-lock` only for stale/dead holders.

## Goal

Only **one** Convert-PDF-TO-MARKDOWN convert process may run at a time (Spock, Hermes, or a human CLI), so RAW/CLEAN routing and **GUBERNATIO** appends do not race.

## Layer 1 — lock file (same machine)

Path:

`D:\\satyagraha\\VAULT\\TOOLS\\_runtime-state\\Convert-PDF-TO-MARKDOWN-01\\CONVERT.lock`

- Created with exclusive create (`O_CREAT|O_EXCL`).
- Holds JSON: run_id, host, agent, pid, timestamps.
- Cleared on clean release; stale if PID dead or TTL expired.

## Layer 2 — **CONVERT_LEASE** (SQLite singleton)

Table **CONVERT_LEASE** (id=1) in the Document-Hash-Registry database:

| Column | Role |
| --- | --- |
| lease_status | **HELD** / **FREE** |
| host / agent / pid / run_id | Who holds the convert |
| acquired_at / heartbeat_at / expires_at | Liveness |
| lock_path | Points at CONVERT.lock |

Heartbeats refresh `expires_at` (default TTL 30 minutes; override `SLIP_CONVERT_LEASE_SECONDS`).

## Relationship to **GUBERNATIO** / API-key lease

- **GUBERNATIO** remains the per-document append-only ledger (and API-key fingerprint leases via existing key_lease).
- **CONVERT_LEASE** gates the *whole convert command* across agents/processes.
- Do not confuse the two.

## Failure behaviour

- Second convert → exit code 2, message names holder host/agent/pid/run_id.
- Crash → lock + lease go stale; next convert may steal if PID dead / TTL past (or `--steal-convert-lock`).

## Optional later

Fleet-wide: same **CONVERT_LEASE** row when registry DB is shared; lock file remains per-machine first line of defence.

---

Satyagraha Law Group · Convert-PDF-TO-MARKDOWN-01
