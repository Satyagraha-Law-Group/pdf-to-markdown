# -*- coding: utf-8 -*-
"""Emit MD GUBERNATIO convert report for a date window (IST)."""
from __future__ import annotations
import argparse
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
STATUS_RANK = {
    "NEW": 1, "PROCESSING": 2, "NEEDS_REVIEW": 3, "AWAITING_APPROVAL": 4,
    "APPROVED": 5, "DUPLICATE": 0, "ERROR": 3,
}

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--days", nargs="+", required=True, help="YYYY-MM-DD IST")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    days = set(args.days)
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    by_sha = {}
    for r in con.execute("SELECT * FROM documents"):
        d = dict(r)
        act = None
        for k in ("approved_at", "converted_at", "first_seen_at"):
            dt = parse_ts(d.get(k))
            if dt and dt.date().isoformat() in days:
                act = dt
                break
        if not act:
            continue
        sha = (d.get("sha256") or "").strip().lower()
        if not sha:
            continue
        d["_activity"] = act
        prev = by_sha.get(sha)
        if prev is None or STATUS_RANK.get(str(d.get("status") or "").upper(), -1) >= STATUS_RANK.get(str(prev.get("status") or "").upper(), -1):
            by_sha[sha] = d
    rows = sorted(by_sha.values(), key=lambda r: (r["_activity"], r.get("original_filename") or ""))
    now = datetime.now(IST)
    stamp = now.strftime("%d-%m-%Y-%H-%M-%S")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    md_path = args.out_dir / f"SLG-Gubernatio-Convert-Report-v-1-0-{stamp}.md"
    lines = [
        "# GUBERNATIO Convert Report",
        "",
        f"- Generated: `{now.isoformat(timespec='seconds')}`",
        f"- Window: {', '.join(sorted(days))}",
        f"- Documents (SHA deduped): **{len(rows)}**",
        "",
        "| S.No | Date | INPUT_RAW PDF | STATUS |",
        "| ---: | --- | --- | --- |",
    ]
    for i, r in enumerate(rows, 1):
        lines.append(
            f"| {i} | {r['_activity'].strftime('%d-%b-%Y')} | `{r.get('original_filename') or '—'}` | **{r.get('status')}** |"
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    (args.out_dir / "LATEST-Gubernatio-Convert-Report.md").write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    print("wrote", md_path, "rows", len(rows))

if __name__ == "__main__":
    main()
