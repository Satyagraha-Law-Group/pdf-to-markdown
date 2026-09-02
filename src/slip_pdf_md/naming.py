"""Three-word filename convention for generated docs and logs.

Word1-Word2-Word3-vN-DD-MM-YYYY-HH-MI-SS.ext
Exactly three Title-Case words. Hyphens only. 24-hour Asia/Calcutta.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    TZ = ZoneInfo("Asia/Calcutta")
except ZoneInfoNotFoundError:
    try:
        TZ = ZoneInfo("Asia/Kolkata")
    except ZoneInfoNotFoundError:
        TZ = timezone(timedelta(hours=5, minutes=30), name="Asia/Calcutta")

REPORT_NAME_RE = re.compile(
    r"^[A-Z][A-Za-z0-9]*-[A-Z][A-Za-z0-9]*-[A-Z][A-Za-z0-9]*-v\d+"
    r"-\d{2}-\d{2}-\d{4}-\d{2}-\d{2}-\d{2}\.[A-Za-z0-9]+$"
)


def now_calcutta() -> datetime:
    return datetime.now(TZ)


def iso_calcutta(moment: datetime | None = None) -> str:
    moment = moment or now_calcutta()
    return moment.isoformat(timespec="seconds")


def stamp(moment: datetime | None = None) -> str:
    moment = moment or now_calcutta()
    return moment.strftime("%d-%m-%Y-%H-%M-%S")


def three_word_filename(
    word1: str,
    word2: str,
    word3: str,
    ext: str = "md",
    version: int = 1,
    moment: datetime | None = None,
) -> str:
    parts = [word1, word2, word3]
    cleaned = []
    for part in parts:
        token = re.sub(r"[^A-Za-z0-9]", "", part)
        if not token:
            raise ValueError(f"empty word in filename: {part!r}")
        cleaned.append(token[0].upper() + token[1:])
    if len(cleaned) != 3:
        raise ValueError("exactly three Title-Case words required")
    ext = ext.lstrip(".")
    name = f"{cleaned[0]}-{cleaned[1]}-{cleaned[2]}-v{version}-{stamp(moment)}.{ext}"
    if not REPORT_NAME_RE.match(name):
        raise ValueError(f"filename failed convention: {name}")
    return name
