"""Three-word filename convention for generated docs, logs, and the registry.

Word1-Word2-Word3-vN-DD-MM-YYYY-HH-MI-SS.ext
Exactly three Title-Case words. Hyphens only. 24-hour Asia/Calcutta.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
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


def _title_words(word1: str, word2: str, word3: str) -> list[str]:
    cleaned = []
    for part in (word1, word2, word3):
        token = re.sub(r"[^A-Za-z0-9]", "", part)
        if not token:
            raise ValueError(f"empty word in filename: {part!r}")
        cleaned.append(token[0].upper() + token[1:])
    return cleaned


def three_word_filename(
    word1: str,
    word2: str,
    word3: str,
    ext: str = "md",
    version: int = 1,
    moment: datetime | None = None,
) -> str:
    cleaned = _title_words(word1, word2, word3)
    ext = ext.lstrip(".")
    name = f"{cleaned[0]}-{cleaned[1]}-{cleaned[2]}-v{version}-{stamp(moment)}.{ext}"
    if not REPORT_NAME_RE.match(name):
        raise ValueError(f"filename failed convention: {name}")
    return name


def resolve_generated_path(
    folder: Path,
    word1: str,
    word2: str,
    word3: str,
    ext: str,
    *,
    legacy_names: tuple[str, ...] = (),
    moment: datetime | None = None,
) -> Path:
    """Return the existing three-word file, migrate a legacy name, or a new path.

    The first created file keeps its original timestamp in the name so a living
    database or append-only log is not renamed on every write.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    ext = ext.lstrip(".")
    words = _title_words(word1, word2, word3)
    prefix = f"{words[0]}-{words[1]}-{words[2]}-v"
    matches = [
        path
        for path in folder.iterdir()
        if path.is_file()
        and path.name.startswith(prefix)
        and path.suffix.lower() == f".{ext.lower()}"
        and REPORT_NAME_RE.match(path.name)
    ]
    if matches:
        return sorted(matches, key=lambda p: (p.stat().st_mtime, p.name))[0]
    for legacy in legacy_names:
        src = folder / legacy
        if not src.is_file():
            continue
        when = datetime.fromtimestamp(src.stat().st_mtime, TZ)
        dest = folder / three_word_filename(*words, ext=ext, moment=when)
        if dest.exists():
            return dest
        src.rename(dest)
        return dest
    return folder / three_word_filename(*words, ext=ext, moment=moment)
