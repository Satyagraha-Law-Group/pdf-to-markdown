"""SHA-256 document registry. Filename is not identity."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from slip_pdf_md.naming import iso_calcutta

STATUS_NEW = "NEW"
STATUS_PROCESSING = "PROCESSING"
STATUS_DONE = "DONE"
STATUS_NEEDS_REVIEW = "NEEDS_REVIEW"
VALID_STATUS = {STATUS_NEW, STATUS_PROCESSING, STATUS_DONE, STATUS_NEEDS_REVIEW}

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    sha256            TEXT PRIMARY KEY,
    original_filename TEXT NOT NULL,
    source_path       TEXT,
    status            TEXT NOT NULL,
    engine            TEXT,
    page_count        INTEGER,
    output_path       TEXT,
    first_seen_at     TEXT NOT NULL,
    converted_at      TEXT,
    last_error        TEXT
);

CREATE TABLE IF NOT EXISTS sightings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    sha256     TEXT NOT NULL,
    filename   TEXT NOT NULL,
    seen_at    TEXT NOT NULL,
    routed_to  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
"""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Registry:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def get(self, sha256: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM documents WHERE sha256 = ?", (sha256,)
        ).fetchone()
        return dict(row) if row else None

    def count_documents(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS n FROM documents").fetchone()
        return int(row["n"])

    def count_sightings(self, sha256: str | None = None) -> int:
        if sha256:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM sightings WHERE sha256 = ?", (sha256,)
            ).fetchone()
        else:
            row = self._conn.execute("SELECT COUNT(*) AS n FROM sightings").fetchone()
        return int(row["n"])

    def see(self, path: Path, routed_to: str, sha256: str | None = None) -> dict:
        """Record a sighting. Inserts the document row only on first hash."""
        path = Path(path)
        sha256 = sha256 or sha256_file(path)
        existing = self.get(sha256)
        now = iso_calcutta()
        if existing is None:
            self._conn.execute(
                """
                INSERT INTO documents (
                    sha256, original_filename, source_path, status, first_seen_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (sha256, path.name, str(path), STATUS_NEW, now),
            )
        self._conn.execute(
            """
            INSERT INTO sightings (sha256, filename, seen_at, routed_to)
            VALUES (?, ?, ?, ?)
            """,
            (sha256, path.name, now, routed_to),
        )
        self._conn.commit()
        row = self.get(sha256)
        assert row is not None
        return row

    def should_convert(self, sha256: str) -> bool:
        row = self.get(sha256)
        if row is None:
            return True
        if row["status"] == STATUS_DONE:
            return False
        return True

    def set_status(
        self,
        sha256: str,
        status: str,
        *,
        engine: str | None = None,
        page_count: int | None = None,
        output_path: str | None = None,
        last_error: str | None = None,
    ) -> None:
        if status not in VALID_STATUS:
            raise ValueError(f"invalid status: {status}")
        converted_at = iso_calcutta() if status in {STATUS_DONE, STATUS_NEEDS_REVIEW} else None
        self._conn.execute(
            """
            UPDATE documents
               SET status = ?,
                   engine = COALESCE(?, engine),
                   page_count = COALESCE(?, page_count),
                   output_path = COALESCE(?, output_path),
                   last_error = ?,
                   converted_at = COALESCE(?, converted_at)
             WHERE sha256 = ?
            """,
            (status, engine, page_count, output_path, last_error, converted_at, sha256),
        )
        self._conn.commit()

    def list_by_status(self, status: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM documents WHERE status = ? ORDER BY first_seen_at",
            (status,),
        ).fetchall()
        return [dict(r) for r in rows]

    def all_documents(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM documents ORDER BY first_seen_at"
        ).fetchall()
        return [dict(r) for r in rows]
