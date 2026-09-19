# -*- coding: utf-8 -*-
"""GUBERNATIO date-window report — Markdown only into vault reports."""
from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
DB_DEFAULT = Path(
    r"D:\satyagraha\VAULT\SLIP_DOCUMENT_PROCESSING\90_00_PROJECT_TOOLING"
    r"\pdf-to-markdown\Document-Hash-Registry-v1-03-09-2026-05-56-17.sqlite"
)
OUT_DEFAULT = Path(r"D:\satyagraha\VAULT\Satyagraha Law Group\reports")


def parse_ts(s):
    if not s:
        return None
    t = str(s).strip()
    try:
        if t.endswith("Z"):
            dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST)
        return dt.astimezone(IST)
    except Exception:
        return None


def activity_dt(row: dict):
    for k in ("converted_at", "approved_at", "first_seen_at", "seen_at", "heartbeat_at"):
        dt = parse_ts(row.get(k))
        if dt:
            return dt, k
    return None, None


def main():
    ap = argparse.ArgumentParser(description="GUBERNATIO run insight (Markdown only)")
    ap.add_argument("--from", dest="date_from", required=True, help="YYYY-MM-DD inclusive IST")
    ap.add_argument("--to", dest="date_to", required=True, help="YYYY-MM-DD inclusive IST")
    ap.add_argument("--db", dest="db", default=str(DB_DEFAULT))
    ap.add_argument("--out", dest="out", default=str(OUT_DEFAULT))
    ap.add_argument("--machine", default="")
    ap.add_argument("--agent", default="")
    ap.add_argument("--status", default="")
    args = ap.parse_args()

    date_from = args.date_from.strip()[:10]
    date_to = args.date_to.strip()[:10]
    if date_from > date_to:
        raise SystemExit("DATE_FROM must be <= DATE_TO")

    now = datetime.now(IST)
    stamp = now.strftime("%d-%m-%Y-%H-%M-%S")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows_raw = [dict(r) for r in con.execute("SELECT * FROM GUBERNATIO")]
    in_window = []
    for r in rows_raw:
        dt, _ = activity_dt(r)
        if not dt:
            continue
        day = dt.date().isoformat()
        if not (date_from <= day <= date_to):
            continue
        if args.machine and (r.get("host") or "") != args.machine:
            continue
        if args.agent and (r.get("agent") or "") != args.agent:
            continue
        if args.status and (r.get("status") or "").upper() != args.status.upper():
            continue
        r["_activity"] = dt
        in_window.append(r)

    by_file = {}
    for r in in_window:
        key = (r.get("sha256") or "").strip().lower() or (r.get("filename") or "").lower()
        prev = by_file.get(key)
        if prev is None or r["_activity"] >= prev["_activity"]:
            by_file[key] = r

    def counts(key):
        d = {}
        for r in in_window:
            k = r.get(key) or "UNKNOWN"
            if key == "status":
                k = str(k).upper()
            d[k] = d.get(k, 0) + 1
        return d

    status_counts = counts("status")
    engine_counts = counts("engine")
    machine_counts = counts("host")
    agent_counts = counts("agent")

    pr = 0
    for r in con.execute("SELECT run_day FROM PROCESS_RUNS"):
        day = (r[0] or "")[:10]
        if date_from <= day <= date_to:
            pr += 1
    con.close()

    sample_sql = f"""SELECT
  id, filename, status, engine, page_count,
  host AS machine_name, agent AS agent_name,
  source_path AS input_path, output_path,
  first_seen_at, converted_at, approved_at, seen_at, last_error, token_usage
FROM GUBERNATIO
WHERE date(COALESCE(converted_at, approved_at, first_seen_at, seen_at))
      BETWEEN date('{date_from}') AND date('{date_to}')
ORDER BY COALESCE(converted_at, approved_at, first_seen_at, seen_at), filename;"""

    def esc(s):
        return str(s).replace("|", "\\|")

    attempts = len(in_window)
    distinct = len(by_file)
    base = f"SLG-Gubernatio-Run-Insight-v-1-0-{stamp}"
    md_path = out_dir / f"{base}.md"

    lines = [
        "# Satyagraha Law Group",
        "",
        "**TOOLS · Convert-PDF-TO-MARKDOWN-01 · GUBERNATIO**",
        "",
        "आ नो भद्राः क्रतवो यन्तु विश्वतः",
        "",
        "*Let noble thoughts come to us from every side. — Rig Veda*",
        "",
        "*The law is reason, free from passion.*",
        "",
        "> Research project — not legal advice, not a solicitation.",
        "",
        "---",
        "",
        "# GUBERNATIO Run Insight — Convert-PDF-TO-MARKDOWN-01",
        "",
        f"**Document:** `{base}.md`",
        f"**Generated:** `{now.isoformat(timespec='seconds')}`",
        f"**Window (IST):** **{date_from}** → **{date_to}** (inclusive)",
        f"**Source DB:** `{args.db}`",
        "",
        "## Answer",
        "",
        f"- **Distinct PDF files:** **{distinct}**",
        f"- **GUBERNATIO attempt rows:** **{attempts}**",
        f"- **PROCESS_RUNS rows:** **{pr}**",
        "",
        "## Sample query (GUBERNATIO)",
        "",
        "```sql",
        sample_sql,
        "```",
        "",
        "## Breakdown — attempts by status",
        "",
        "| Status | Attempts |",
        "| --- | ---: |",
    ]
    for st, n in sorted(status_counts.items(), key=lambda x: (-x[1], str(x[0]))):
        lines.append(f"| `{esc(st)}` | {n} |")
    lines += ["", "## Breakdown — attempts by engine", "", "| Engine | Attempts |", "| --- | ---: |"]
    for en, n in sorted(engine_counts.items(), key=lambda x: (-x[1], str(x[0]))):
        lines.append(f"| `{esc(en)}` | {n} |")
    lines += ["", "## Breakdown — attempts by machine", "", "| Machine | Attempts |", "| --- | ---: |"]
    for m, n in sorted(machine_counts.items(), key=lambda x: (-x[1], str(x[0]))):
        lines.append(f"| `{esc(m)}` | {n} |")
    lines += ["", "## Breakdown — attempts by agent", "", "| Agent | Attempts |", "| --- | ---: |"]
    for a, n in sorted(agent_counts.items(), key=lambda x: (-x[1], str(x[0]))):
        lines.append(f"| `{esc(a)}` | {n} |")
    lines += [
        "",
        "## Detail — GUBERNATIO rows in window",
        "",
        "| # | Activity (IST) | Filename | Status | Engine | Pages | Machine | Agent |",
        "| ---: | --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for i, r in enumerate(sorted(in_window, key=lambda x: (x["_activity"], x.get("filename") or "")), 1):
        lines.append(
            "| {i} | {act} | `{fn}` | `{st}` | `{en}` | {pg} | `{host}` | `{ag}` |".format(
                i=i,
                act=r["_activity"].strftime("%d-%b-%Y %H:%M"),
                fn=esc(r.get("filename") or "—"),
                st=esc(r.get("status") or "—"),
                en=esc(r.get("engine") or "—"),
                pg=r.get("page_count") if r.get("page_count") is not None else "—",
                host=esc(r.get("host") or "—"),
                ag=esc(r.get("agent") or "—"),
            )
        )
    lines += [
        "",
        "## Notes",
        "",
        "- Activity date = first non-empty among `converted_at`, `approved_at`, `first_seen_at`, `seen_at` (IST).",
        "- Attempts follow the append-only ledger (retries count).",
        "- Distinct files collapse by `sha256` (fallback: filename).",
        "- Markdown only — vault file-based viewing under `reports`.",
        "",
        "---",
        "",
        "Satyagraha Law Group · GUBERNATIO",
        "",
    ]
    text = "\n".join(lines)
    md_path.write_text(text, encoding="utf-8")
    (out_dir / "LATEST-Gubernatio-Run-Insight.md").write_text(text, encoding="utf-8")
    print(str(md_path))
    print(f"distinct={distinct} attempts={attempts} process_runs={pr}")


if __name__ == "__main__":
    main()
