"""SLG file-naming convention for every generated artifact.

Standing Satyagraha rule (Anil):

    SLG-<Word1>-<Word2>-<Word3>-v-<version>-<subversion>-dd-mm-yyyy-hh-mm-ss.ext

- Prefix: SLG-
- At most three Title-Case alphanumeric words (1–3 allowed; tool reports use exactly three)
- Version and sub-version are integers (default 1 and 0)
- Timestamp is Asia/Calcutta (IST), 24-hour
- Hyphens only (no spaces/underscores in the stamped name)

Converted Markdown from a PDF uses words derived from the PDF stem (≤3), then the same stamp.
Living files (registry DB, append-only logs) keep the first-created stamp via resolve_generated_path.
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

# 1–3 Title-Case words after SLG-, then v-<ver>-<sub>-stamp.ext
SLG_NAME_RE = re.compile(
    r"^SLG-(?:[A-Z][A-Za-z0-9]*)(?:-[A-Z][A-Za-z0-9]*){0,2}"
    r"-v-\d+-\d+"
    r"-\d{2}-\d{2}-\d{4}-\d{2}-\d{2}-\d{2}"
    r"\.[A-Za-z0-9]+$"
)

# Back-compat alias used by older tests/callers
REPORT_NAME_RE = SLG_NAME_RE


def now_calcutta() -> datetime:
    return datetime.now(TZ)


def iso_calcutta(moment: datetime | None = None) -> str:
    moment = moment or now_calcutta()
    return moment.isoformat(timespec="seconds")


def stamp(moment: datetime | None = None) -> str:
    moment = moment or now_calcutta()
    return moment.strftime("%d-%m-%Y-%H-%M-%S")


def _one_title(part: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]", "", part or "")
    if not token:
        raise ValueError(f"empty word in filename: {part!r}")
    return token[0].upper() + token[1:]


def _title_words(*parts: str) -> list[str]:
    words = [_one_title(p) for p in parts if str(p or "").strip()]
    if not words:
        raise ValueError("need at least one Title-Case word after SLG-")
    if len(words) > 3:
        words = words[:3]
    return words


def words_from_stem(stem: str, *, fallback: str = "Document") -> list[str]:
    """Derive ≤3 Title-Case words from a PDF/markdown stem.

    Pure-numeric tokens (e.g. time prefixes like 12-39-14) are skipped so names
    stay Title-Case after SLG-.
    """
    raw = re.sub(r"[_\.]+", "-", str(stem or "").strip())
    raw = re.sub(r"[^A-Za-z0-9\-]+", "-", raw)
    parts = [p for p in raw.split("-") if p]
    expanded: list[str] = []
    for part in parts:
        if part.isdigit():
            continue
        pieces = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|[A-Za-z]+\d*|\d+[A-Za-z]+", part)
        if pieces:
            expanded.extend(pieces)
        elif re.search(r"[A-Za-z]", part):
            expanded.append(part)
    words: list[str] = []
    for part in expanded:
        if part.isdigit():
            continue
        try:
            words.append(_one_title(part))
        except ValueError:
            continue
        if len(words) == 3:
            break
    if not words:
        words = [_one_title(fallback)]
    return words


def slg_filename(
    *words: str,
    ext: str = "md",
    version: int = 1,
    subversion: int = 0,
    moment: datetime | None = None,
) -> str:
    """Build an SLG- stamped filename from 1–3 words."""
    cleaned = _title_words(*words)
    ext = ext.lstrip(".")
    mid = "-".join(cleaned)
    name = f"SLG-{mid}-v-{int(version)}-{int(subversion)}-{stamp(moment)}.{ext}"
    if not SLG_NAME_RE.match(name):
        raise ValueError(f"filename failed SLG convention: {name}")
    return name


def three_word_filename(
    word1: str,
    word2: str,
    word3: str,
    ext: str = "md",
    version: int = 1,
    subversion: int = 0,
    moment: datetime | None = None,
) -> str:
    """Tool reports: exactly three words under the SLG- rule (back-compat name)."""
    return slg_filename(
        word1,
        word2,
        word3,
        ext=ext,
        version=version,
        subversion=subversion,
        moment=moment,
    )


def convert_output_filename(
    pdf_name: str,
    *,
    ext: str = "md",
    version: int = 1,
    subversion: int = 0,
    moment: datetime | None = None,
    suffix_word: str | None = None,
) -> str:
    """Markdown (or note) name derived from the source PDF, SLG- stamped.

    suffix_word, if set, replaces the last derived word (e.g. Error, Fidelity)
    so sidecars stay in the same convention.
    """
    stem = Path(pdf_name).stem
    # Drop a trailing _raster from stem words for cleaner titles
    if stem.lower().endswith("_raster"):
        stem = stem[: -len("_raster")]
    words = words_from_stem(stem)
    if suffix_word:
        title = _one_title(suffix_word)
        if len(words) >= 3:
            words = words[:2] + [title]
        else:
            words = words + [title]
            words = words[:3]
    return slg_filename(
        *words,
        ext=ext,
        version=version,
        subversion=subversion,
        moment=moment,
    )


def resolve_generated_path(
    folder: Path,
    word1: str,
    word2: str,
    word3: str,
    ext: str,
    *,
    legacy_names: tuple[str, ...] = (),
    moment: datetime | None = None,
    version: int = 1,
    subversion: int = 0,
) -> Path:
    """Return existing living SLG file, migrate legacy, or create a new stamped path.

    First-created stamp is kept so registries/logs are not renamed every write.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    ext = ext.lstrip(".")
    words = _title_words(word1, word2, word3)
    prefix = f"SLG-{'-'.join(words)}-v-{int(version)}-{int(subversion)}-"
    # Also accept prior three-word (no SLG-) living files as legacy
    old_prefix = f"{words[0]}-{words[1]}-{words[2]}-v"
    matches = []
    for path in folder.iterdir():
        if not path.is_file():
            continue
        if path.suffix.lower() != f".{ext.lower()}":
            continue
        if path.name.startswith(prefix) and SLG_NAME_RE.match(path.name):
            matches.append(path)
    if matches:
        return sorted(matches, key=lambda p: (p.stat().st_mtime, p.name))[0]

    # Migrate old three-word living file if present
    old_matches = [
        path
        for path in folder.iterdir()
        if path.is_file()
        and path.name.startswith(old_prefix)
        and path.suffix.lower() == f".{ext.lower()}"
    ]
    if old_matches:
        src = sorted(old_matches, key=lambda p: (p.stat().st_mtime, p.name))[0]
        when = datetime.fromtimestamp(src.stat().st_mtime, TZ)
        dest = folder / three_word_filename(
            *words, ext=ext, version=version, subversion=subversion, moment=when
        )
        if not dest.exists():
            src.rename(dest)
        return dest if dest.exists() else src

    for legacy in legacy_names:
        src = folder / legacy
        if not src.is_file():
            continue
        when = datetime.fromtimestamp(src.stat().st_mtime, TZ)
        dest = folder / three_word_filename(
            *words, ext=ext, version=version, subversion=subversion, moment=when
        )
        if dest.exists():
            return dest
        src.rename(dest)
        return dest

    return folder / three_word_filename(
        *words, ext=ext, version=version, subversion=subversion, moment=moment
    )

# Back-compat aliases
