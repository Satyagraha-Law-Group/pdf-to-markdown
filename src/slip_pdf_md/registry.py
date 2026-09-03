"""SHA-256 document registry. Filename is not identity.

The live database is Document-Hash-Registry-vN-DD-MM-YYYY-HH-MI-SS.sqlite
under 90_00_PROJECT_TOOLING/pdf-to-markdown/ (stamp is first-created time).
A sibling .bak with the same three-word stem is rewritten after every change.
If the live file is deleted, the next open restores from that backup.
Rebuild from Markdown front matter if both copies are gone.
GUBERNATIO is the per-file steering table (filename, host, agent, step).
documents stays one row per SHA-256 so multiple agents do not clog identity.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import socket
import sqlite3
from pathlib import Path

from slip_pdf_md.naming import iso_calcutta

STATUS_NEW = "NEW"
STATUS_PROCESSING = "PROCESSING"
STATUS_AWAITING_APPROVAL = "AWAITING_APPROVAL"
STATUS_APPROVED = "APPROVED"
STATUS_DONE = "DONE"  # legacy closed loop; new converts use AWAITING_APPROVAL then APPROVED
STATUS_NEEDS_REVIEW = "NEEDS_REVIEW"
STATUS_REJECTED = "REJECTED"
VALID_STATUS = {
    STATUS_NEW,
    STATUS_PROCESSING,
    STATUS_AWAITING_APPROVAL,
    STATUS_APPROVED,
    STATUS_DONE,
    STATUS_NEEDS_REVIEW,
    STATUS_REJECTED,
}
# Convert finished, markdown staged. Do not reconvert.
EXTRACTED_STATUSES = {STATUS_AWAITING_APPROVAL, STATUS_APPROVED, STATUS_DONE}
# Lawyer closed the GUBERNATIO loop. Downstream may use the file.
CLOSED_STATUSES = {STATUS_APPROVED, STATUS_DONE}

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
    last_error        TEXT,
    token_usage       TEXT
);

CREATE TABLE IF NOT EXISTS sightings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    sha256     TEXT NOT NULL,
    filename   TEXT NOT NULL,
    seen_at    TEXT NOT NULL,
    routed_to  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);

CREATE TABLE IF NOT EXISTS "GUBERNATIO" (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    sha256            TEXT NOT NULL,
    filename          TEXT NOT NULL,
    source_path       TEXT,
    status            TEXT NOT NULL,
    engine            TEXT,
    page_count        INTEGER,
    output_path       TEXT,
    routed_to         TEXT,
    first_seen_at     TEXT,
    converted_at      TEXT,
    last_error        TEXT,
    seen_at           TEXT NOT NULL,
    host              TEXT,
    agent             TEXT,
    step              TEXT NOT NULL,
    api_key_fingerprint TEXT,
    api_provider      TEXT,
    lease_status      TEXT,
    heartbeat_at      TEXT,
    expires_at        TEXT,
    approved_by       TEXT,
    approved_at       TEXT,
    token_usage       TEXT
);
CREATE INDEX IF NOT EXISTS idx_gubernatio_sha ON "GUBERNATIO"(sha256);
CREATE INDEX IF NOT EXISTS idx_gubernatio_filename ON "GUBERNATIO"(filename);
CREATE INDEX IF NOT EXISTS idx_gubernatio_seen ON "GUBERNATIO"(seen_at);
"""



class RegistryCorrupt(RuntimeError):
    """Live SQLite failed integrity_check and backup could not repair it."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def backup_path(db_path: Path) -> Path:
    """Same three-word stem, extension .bak (Document-Hash-Registry-vN-stamp.bak)."""
    return Path(db_path).with_suffix(".bak")


def format_duplicate_notice(
    existing: dict,
    *,
    inbound_name: str,
    sidecar: str | None,
    sightings: int,
) -> str:
    """Lawyer-facing terminal block for a SHA-256 hit months later."""
    first = existing.get("original_filename") or "(unknown)"
    first_seen = existing.get("first_seen_at") or "(unknown)"
    converted = existing.get("converted_at") or "(not yet converted)"
    pages = existing.get("page_count")
    engine = existing.get("engine") or "(unknown)"
    canonical = existing.get("output_path") or existing.get("output") or "(none)"
    sha = existing.get("sha256") or ""
    lines = [
        "  [DUP] same PDF bytes as a file already converted (filename is not identity)",
        f"       this_file: {inbound_name}",
        f"       first_seen_as: {first}",
        f"       first_seen_at: {first_seen}",
        f"       converted_at: {converted}",
        f"       engine: {engine}  pages: {pages if pages is not None else '?'}",
        f"       canonical_markdown: {canonical}",
        f"       sha256: {sha}",
        f"       sightings_including_this: {sightings}",
    ]
    if sidecar:
        lines.append(f"       sidecar: {sidecar}")
    return "\n".join(lines)


class Registry:
    def __init__(self, db_path: Path, *, restore_if_missing: bool = True):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.bak_path = backup_path(self.db_path)
        self.restored_from_backup = False
        self._conn: sqlite3.Connection | None = None

        if restore_if_missing and not self.db_path.exists() and self.bak_path.exists():
            shutil.copy2(self.bak_path, self.db_path)
            self.restored_from_backup = True

        self._connect()
        if not self.integrity_ok():
            repaired = self._restore_from_backup_locked()
            if not repaired or not self.integrity_ok():
                raise RegistryCorrupt(
                    f"registry failed integrity_check: {self.db_path}. "
                    "Run: slip-pdf-md registry restore --vault ... "
                    "or: slip-pdf-md registry rebuild --vault ..."
                )
        self._write_notice()

    def _connect(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()
        self._ensure_gubernatio_lease_columns()
        self._ensure_token_usage_columns()
        from slip_pdf_md.catalog import ensure_catalog
        ensure_catalog(self.conn)
        self._backfill_gubernatio_if_empty()

    @property
    def conn(self) -> sqlite3.Connection:
        assert self._conn is not None
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def integrity_ok(self) -> bool:
        try:
            row = self.conn.execute("PRAGMA integrity_check").fetchone()
        except sqlite3.Error:
            return False
        if row is None:
            return False
        return str(row[0]).lower() == "ok"

    def health(self) -> dict:
        bak = self.bak_path.exists()
        return {
            "path": str(self.db_path),
            "exists": self.db_path.exists(),
            "integrity_ok": self.integrity_ok(),
            "backup_path": str(self.bak_path),
            "backup_exists": bak,
            "documents": self.count_documents(),
            "sightings": self.count_sightings(),
            "gubernatio": self.count_gubernatio(),
            "restored_from_backup": self.restored_from_backup,
        }

    def backup(self, dest: Path | None = None) -> Path:
        dest = Path(dest) if dest is not None else self.bak_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".tmp")
        if tmp.exists():
            tmp.unlink()
        bck = sqlite3.connect(str(tmp))
        try:
            self.conn.backup(bck)
        finally:
            bck.close()
        tmp.replace(dest)
        return dest

    def _backup_quiet(self) -> None:
        try:
            self.backup()
        except Exception:
            pass

    def _restore_from_backup_locked(self) -> bool:
        if not self.bak_path.exists():
            return False
        self.close()
        shutil.copy2(self.bak_path, self.db_path)
        self.restored_from_backup = True
        self._connect()
        return True

    def restore_from_backup(self) -> bool:
        if not self.bak_path.exists():
            return False
        return self._restore_from_backup_locked() and self.integrity_ok()

    def _write_notice(self) -> None:
        from slip_pdf_md.naming import resolve_generated_path
        notice = resolve_generated_path(
            self.db_path.parent,
            "Registry",
            "Safety",
            "Notice",
            "txt",
            legacy_names=("Do-Not-Delete-This-File.txt",),
        )
        if notice.exists():
            return
        notice.write_text(
            "\n".join(
                [
                    "Satyagraha Law Group — PDF to Markdown (SLIP)",
                    "",
                    "DO NOT DELETE the Document-Hash-Registry .sqlite or matching .bak.",
                    "They remember every PDF by SHA-256 so a renamed file months later is still a duplicate.",
                    "",
                    "If the live sqlite is missing, the tool restores it from the matching .bak.",
                    "If both are corrupt or gone:",
                    "  slip-pdf-md registry restore --vault PATH",
                    "  slip-pdf-md registry rebuild --vault PATH",
                    "  slip-pdf-md doctor --vault PATH",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def get(self, sha256: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM documents WHERE sha256 = ?", (sha256,)
        ).fetchone()
        return dict(row) if row else None

    def count_documents(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS n FROM documents").fetchone()
        return int(row["n"])

    def count_sightings(self, sha256: str | None = None) -> int:
        if sha256:
            row = self.conn.execute(
                "SELECT COUNT(*) AS n FROM sightings WHERE sha256 = ?", (sha256,)
            ).fetchone()
        else:
            row = self.conn.execute("SELECT COUNT(*) AS n FROM sightings").fetchone()
        return int(row["n"])

    def see(self, path: Path, routed_to: str, sha256: str | None = None) -> dict:
        """Record a sighting. Inserts the document row only on first hash."""
        path = Path(path)
        sha256 = sha256 or sha256_file(path)
        existing = self.get(sha256)
        now = iso_calcutta()
        if existing is None:
            self.conn.execute(
                """
                INSERT INTO documents (
                    sha256, original_filename, source_path, status, first_seen_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (sha256, path.name, str(path), STATUS_NEW, now),
            )
        self.conn.execute(
            """
            INSERT INTO sightings (sha256, filename, seen_at, routed_to)
            VALUES (?, ?, ?, ?)
            """,
            (sha256, path.name, now, routed_to),
        )
        self.conn.commit()
        row = self.get(sha256)
        assert row is not None
        self.gubernatio_record(
            sha256=sha256,
            filename=path.name,
            source_path=str(path),
            status=row.get("status") or STATUS_NEW,
            engine=row.get("engine"),
            page_count=row.get("page_count"),
            output_path=row.get("output_path"),
            routed_to=routed_to,
            first_seen_at=row.get("first_seen_at"),
            converted_at=row.get("converted_at"),
            last_error=row.get("last_error"),
            step="sighting",
        )
        self._backup_quiet()
        return row

    def should_convert(self, sha256: str) -> bool:
        row = self.get(sha256)
        if row is None:
            return True
        if row["status"] in EXTRACTED_STATUSES:
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
        token_usage: str | dict | None = None,
    ) -> None:
        if status not in VALID_STATUS:
            raise ValueError(f"invalid status: {status}")
        converted_at = iso_calcutta() if status in {
            STATUS_DONE,
            STATUS_AWAITING_APPROVAL,
            STATUS_APPROVED,
            STATUS_NEEDS_REVIEW,
        } else None
        from slip_pdf_md.runlog import dumps_token_usage

        token_json = dumps_token_usage(token_usage)
        self.conn.execute(
            """
            UPDATE documents
               SET status = ?,
                   engine = COALESCE(?, engine),
                   page_count = COALESCE(?, page_count),
                   output_path = COALESCE(?, output_path),
                   last_error = ?,
                   converted_at = COALESCE(?, converted_at),
                   token_usage = COALESCE(?, token_usage)
             WHERE sha256 = ?
            """,
            (status, engine, page_count, output_path, last_error, converted_at, token_json, sha256),
        )
        self.conn.commit()
        row = self.get(sha256) or {}
        self.gubernatio_record(
            sha256=sha256,
            filename=row.get("original_filename") or "",
            source_path=row.get("source_path"),
            status=status,
            engine=row.get("engine"),
            page_count=row.get("page_count"),
            output_path=row.get("output_path"),
            routed_to=None,
            first_seen_at=row.get("first_seen_at"),
            converted_at=row.get("converted_at"),
            last_error=row.get("last_error"),
            step=f"status_{status}",
            token_usage=token_json or row.get("token_usage"),
        )
        self._backup_quiet()

    def list_by_status(self, status: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM documents WHERE status = ? ORDER BY first_seen_at",
            (status,),
        ).fetchall()
        return [dict(r) for r in rows]

    def all_documents(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM documents ORDER BY first_seen_at"
        ).fetchall()
        return [dict(r) for r in rows]



    def _backfill_gubernatio_if_empty(self) -> None:
        """One-time: copy legacy sightings into GUBERNATIO when the table is new."""
        if self.count_gubernatio() > 0:
            return
        sightings = self.conn.execute("SELECT * FROM sightings ORDER BY id").fetchall()
        if not sightings:
            return
        host, agent = self.gubernatio_who()
        from slip_pdf_md.naming import iso_calcutta
        now = iso_calcutta()
        for s in sightings:
            doc = self.get(s["sha256"]) or {}
            self.conn.execute(
                """
                INSERT INTO "GUBERNATIO" (
                    sha256, filename, source_path, status, engine, page_count,
                    output_path, routed_to, first_seen_at, converted_at, last_error,
                    seen_at, host, agent, step
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    s["sha256"],
                    s["filename"],
                    doc.get("source_path"),
                    doc.get("status") or "NEW",
                    doc.get("engine"),
                    doc.get("page_count"),
                    doc.get("output_path"),
                    s["routed_to"],
                    doc.get("first_seen_at"),
                    doc.get("converted_at"),
                    doc.get("last_error"),
                    s["seen_at"] or now,
                    host,
                    agent,
                    "backfill_sighting",
                ),
            )
        self.conn.commit()


    def _ensure_gubernatio_lease_columns(self) -> None:
        rows = self.conn.execute('PRAGMA table_info("GUBERNATIO")').fetchall()
        have = {row[1] for row in rows}
        for name, decl in (
            ("api_key_fingerprint", "TEXT"),
            ("api_provider", "TEXT"),
            ("lease_status", "TEXT"),
            ("heartbeat_at", "TEXT"),
            ("expires_at", "TEXT"),
            ("approved_by", "TEXT"),
            ("approved_at", "TEXT"),
        ):
            if name not in have:
                self.conn.execute(f'ALTER TABLE "GUBERNATIO" ADD COLUMN {name} {decl}')
        self.conn.commit()

    def _ensure_token_usage_columns(self) -> None:
        """token_usage is per convert-PDF-to-markdown run (JSON). Live DBs ALTER."""
        for table in ("documents", '"GUBERNATIO"'):
            rows = self.conn.execute(f"PRAGMA table_info({table})").fetchall()
            have = {row[1] for row in rows}
            if "token_usage" not in have:
                self.conn.execute(f"ALTER TABLE {table} ADD COLUMN token_usage TEXT")
        self.conn.commit()

    def gubernatio_is_extracted(self, sha256: str) -> bool:
        """Markdown exists. Do not reconvert. Loop may still be open."""
        q = ",".join("?" * len(EXTRACTED_STATUSES))
        row = self.conn.execute(
            f'SELECT id FROM "GUBERNATIO" WHERE sha256 = ? AND status IN ({q}) LIMIT 1',
            (sha256, *EXTRACTED_STATUSES),
        ).fetchone()
        return row is not None

    def gubernatio_is_done(self, sha256: str) -> bool:
        """Back-compat name for the convert gate: already extracted."""
        return self.gubernatio_is_extracted(sha256)

    def gubernatio_loop_closed(self, sha256: str) -> bool:
        """Lawyer approved (or legacy DONE). Downstream may use the file."""
        q = ",".join("?" * len(CLOSED_STATUSES))
        row = self.conn.execute(
            f'SELECT id FROM "GUBERNATIO" WHERE sha256 = ? AND status IN ({q}) LIMIT 1',
            (sha256, *CLOSED_STATUSES),
        ).fetchone()
        return row is not None

    def gubernatio_done_row(self, sha256: str) -> dict | None:
        q = ",".join("?" * len(EXTRACTED_STATUSES))
        row = self.conn.execute(
            f'SELECT * FROM "GUBERNATIO" WHERE sha256 = ? AND status IN ({q}) ORDER BY id DESC LIMIT 1',
            (sha256, *EXTRACTED_STATUSES),
        ).fetchone()
        return dict(row) if row else None

    def gubernatio_should_convert(self, sha256: str) -> bool:
        """GUBERNATIO is the gate. documents.status is legacy fallback only."""
        if self.gubernatio_is_extracted(sha256):
            return False
        return self.should_convert(sha256)

    def gubernatio_running_lease(self, fingerprint: str) -> dict | None:
        from slip_pdf_md.key_lease import LEASE_RUNNING, lease_is_expired

        if not fingerprint:
            return None
        row = self.conn.execute(
            """
            SELECT * FROM "GUBERNATIO"
             WHERE api_key_fingerprint = ?
             ORDER BY id DESC LIMIT 1
            """,
            (fingerprint,),
        ).fetchone()
        if row is None:
            return None
        data = dict(row)
        if data.get("lease_status") != LEASE_RUNNING:
            return None
        if lease_is_expired(data.get("expires_at")):
            return None
        return data

    def gubernatio_live_leases(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT DISTINCT api_key_fingerprint FROM \"GUBERNATIO\" "
            "WHERE api_key_fingerprint IS NOT NULL AND api_key_fingerprint != ''"
        ).fetchall()
        live = []
        for row in rows:
            held = self.gubernatio_running_lease(row[0])
            if held:
                live.append(held)
        return live

    def acquire_key_lease(
        self,
        *,
        fingerprint: str,
        sentinel: Path,
        sha256: str,
        filename: str,
        ttl_seconds: int | None = None,
        api_provider: str | None = None,
    ) -> dict:
        from slip_pdf_md.key_lease import (
            LEASE_RUNNING,
            expiry_stamp,
            lease_ttl_seconds,
            remove_sentinel,
            require_fingerprint,
            touch_sentinel_exclusive,
        )

        fingerprint = require_fingerprint(fingerprint) or ""
        if not fingerprint:
            return {"ok": False, "reason": "fingerprint"}
        ttl = ttl_seconds if ttl_seconds is not None else lease_ttl_seconds()
        held = self.gubernatio_running_lease(fingerprint)
        host, agent = self.gubernatio_who()
        if held:
            same = held.get("host") == host and held.get("agent") == agent
            if not same:
                return {
                    "ok": False,
                    "reason": "held",
                    "holder_host": held.get("host"),
                    "holder_agent": held.get("agent"),
                    "expires_at": held.get("expires_at"),
                    "sentinel": str(sentinel),
                }
        others = [
            r for r in self.gubernatio_live_leases()
            if r.get("api_key_fingerprint") != fingerprint
        ]
        if Path(sentinel).exists():
            if held and held.get("host") == host and held.get("agent") == agent or others:
                pass
            else:
                remove_sentinel(sentinel)
        if not Path(sentinel).exists() and not others:
            if not touch_sentinel_exclusive(sentinel):
                held2 = self.gubernatio_running_lease(fingerprint)
                if held2 and not (held2.get("host") == host and held2.get("agent") == agent):
                    return {
                        "ok": False,
                        "reason": "held",
                        "holder_host": held2.get("host"),
                        "holder_agent": held2.get("agent"),
                        "expires_at": held2.get("expires_at"),
                        "sentinel": str(sentinel),
                    }
                if not Path(sentinel).exists() and not touch_sentinel_exclusive(sentinel):
                    return {"ok": False, "reason": "sentinel", "sentinel": str(sentinel)}
        now = iso_calcutta()
        expires = expiry_stamp(ttl=ttl)
        self.gubernatio_record(
            sha256=sha256,
            filename=filename,
            step="key_lease_acquire",
            status=STATUS_PROCESSING,
            api_key_fingerprint=fingerprint,
            api_provider=api_provider,
            lease_status=LEASE_RUNNING,
            heartbeat_at=now,
            expires_at=expires,
        )
        return {
            "ok": True,
            "expires_at": expires,
            "sentinel": str(sentinel),
            "fingerprint": fingerprint,
            "api_provider": api_provider,
        }

    def heartbeat_key_lease(self, *, fingerprint: str, sha256: str, filename: str, ttl_seconds: int | None = None, api_provider: str | None = None) -> None:
        from slip_pdf_md.key_lease import (
            LEASE_RUNNING,
            expiry_stamp,
            lease_ttl_seconds,
            require_fingerprint,
        )

        fingerprint = require_fingerprint(fingerprint) or ""
        ttl = ttl_seconds if ttl_seconds is not None else lease_ttl_seconds()
        now = iso_calcutta()
        self.gubernatio_record(
            sha256=sha256,
            filename=filename,
            step="key_lease_heartbeat",
            status=STATUS_PROCESSING,
            api_key_fingerprint=fingerprint,
            lease_status=LEASE_RUNNING,
            heartbeat_at=now,
            expires_at=expiry_stamp(ttl=ttl),
        )

    def release_key_lease(self, *, fingerprint: str, sentinel: Path, sha256: str, filename: str, api_provider: str | None = None) -> None:
        from slip_pdf_md.key_lease import (
            LEASE_FREE,
            remove_sentinel,
            require_fingerprint,
        )

        fingerprint = require_fingerprint(fingerprint) or ""
        row = self.get(sha256) or {}
        self.gubernatio_record(
            sha256=sha256,
            filename=filename,
            step="key_lease_release",
            status=row.get("status") or STATUS_NEW,
            api_key_fingerprint=fingerprint,
            api_provider=api_provider,
            lease_status=LEASE_FREE,
        )
        others = [r for r in self.gubernatio_live_leases() if r.get("api_key_fingerprint") != fingerprint]
        if not others:
            remove_sentinel(sentinel)

    def count_gubernatio(self, sha256: str | None = None) -> int:
        if sha256:
            row = self.conn.execute(
                'SELECT COUNT(*) AS n FROM "GUBERNATIO" WHERE sha256 = ?', (sha256,)
            ).fetchone()
        else:
            row = self.conn.execute('SELECT COUNT(*) AS n FROM "GUBERNATIO"').fetchone()
        return int(row["n"])

    def gubernatio_who(self) -> tuple[str, str]:
        host = os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or socket.gethostname()
        agent = os.environ.get("SLIP_AGENT") or "Spock"
        return str(host), str(agent)

    def gubernatio_record(
        self,
        *,
        sha256: str,
        filename: str,
        step: str,
        status: str,
        source_path: str | None = None,
        engine: str | None = None,
        page_count: int | None = None,
        output_path: str | None = None,
        routed_to: str | None = None,
        first_seen_at: str | None = None,
        converted_at: str | None = None,
        last_error: str | None = None,
        api_key_fingerprint: str | None = None,
        api_provider: str | None = None,
        lease_status: str | None = None,
        heartbeat_at: str | None = None,
        expires_at: str | None = None,
        approved_by: str | None = None,
        approved_at: str | None = None,
        token_usage: str | dict | None = None,
    ) -> int:
        """Append one GUBERNATIO row. Never stores a raw API key."""
        from slip_pdf_md.key_lease import require_fingerprint
        from slip_pdf_md.runlog import dumps_token_usage

        fingerprint = require_fingerprint(api_key_fingerprint)
        host, agent = self.gubernatio_who()
        token_json = dumps_token_usage(token_usage)
        cur = self.conn.execute(
            """
            INSERT INTO "GUBERNATIO" (
                sha256, filename, source_path, status, engine, page_count,
                output_path, routed_to, first_seen_at, converted_at, last_error,
                seen_at, host, agent, step,
                api_key_fingerprint, api_provider, lease_status, heartbeat_at, expires_at,
                approved_by, approved_at, token_usage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sha256,
                filename,
                source_path,
                status,
                engine,
                page_count,
                output_path,
                routed_to,
                first_seen_at,
                converted_at,
                last_error,
                iso_calcutta(),
                host,
                agent,
                step,
                fingerprint,
                api_provider,
                lease_status,
                heartbeat_at,
                expires_at,
                approved_by,
                approved_at,
                token_json,
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def approve(self, sha256: str, *, by: str | None = None) -> dict:
        """Lawyer closes the GUBERNATIO loop. Identity registry is already processed."""
        row = self.get(sha256)
        if row is None:
            raise ValueError("unknown document")
        current = row.get("status")
        if current in CLOSED_STATUSES:
            return dict(row)
        if current not in {STATUS_AWAITING_APPROVAL, STATUS_NEEDS_REVIEW}:
            raise ValueError(f"cannot approve status {current}")
        who = (by or os.environ.get("SLIP_LAWYER") or self.gubernatio_who()[1]).strip()
        now = iso_calcutta()
        self.set_status(sha256, STATUS_APPROVED)
        self.gubernatio_record(
            sha256=sha256,
            filename=row.get("original_filename") or "",
            source_path=row.get("source_path"),
            status=STATUS_APPROVED,
            engine=row.get("engine"),
            page_count=row.get("page_count"),
            output_path=row.get("output_path"),
            first_seen_at=row.get("first_seen_at"),
            converted_at=row.get("converted_at"),
            step="lawyer_approved",
            approved_by=who,
            approved_at=now,
        )
        from slip_pdf_md.catalog import api_key_type_for, markdown_page_count
        self.record_process_run(
            filename=row.get("original_filename") or "",
            sha256=sha256,
            pdf_page_count=row.get("page_count"),
            markdown_page_count=markdown_page_count(row.get("output_path")),
            api_key_type=api_key_type_for(row.get("engine")),
            api_provider=row.get("engine"),
            status=STATUS_APPROVED,
            approved=True,
            token_usage=row.get("token_usage"),
            output_path=row.get("output_path"),
            source="approve",
        )
        return self.get(sha256) or {}


    def record_process_run(self, **kwargs):
        """Append one PROCESS_RUNS row (day, file, pages, API key type, approval)."""
        from slip_pdf_md.catalog import record_process_run as _record
        rid = _record(self.conn, **kwargs)
        self._backup_quiet()
        return rid

    def upsert_test_case(self, **kwargs) -> str:
        from slip_pdf_md.catalog import upsert_test_case as _upsert
        case_id = _upsert(self.conn, **kwargs)
        self._backup_quiet()
        return case_id

    def register_error(self, **kwargs) -> None:
        from slip_pdf_md.catalog import register_error as _reg
        _reg(self.conn, **kwargs)
        self._backup_quiet()

    def write_awaiting_approval_report(self, dest_dir: Path) -> Path:

        from slip_pdf_md.branding import (
            footer_markdown,
            header_markdown,
            with_single_footer,
        )
        from slip_pdf_md.naming import three_word_filename

        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        rows = self.list_by_status(STATUS_AWAITING_APPROVAL)
        path = dest_dir / three_word_filename("Awaiting", "Approval", "Report", ext="md")
        lines = [
            header_markdown(),
            "# Awaiting Approval Report",
            "",
            "Satyagraha Law Group — SLIP PDF to Markdown Ingestion Tool.",
            "These files are processed. Markdown is staged. GUBERNATIO is **not** closed until a lawyer approves.",
            "",
            f"- awaiting_count: {len(rows)}",
            f"- written_at: {iso_calcutta()}",
            "",
            "| sha256 | filename | engine | pages | token_usage | markdown |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        from slip_pdf_md.runlog import token_usage_summary

        for row in rows:
            lines.append(
                f"| `{row.get('sha256')}` | {row.get('original_filename')} | "
                f"{row.get('engine') or ''} | {row.get('page_count') or ''} | "
                f"{token_usage_summary(row.get('token_usage'))} | "
                f"`{row.get('output_path') or ''}` |"
            )
        if not rows:
            lines.append("| (none) |  |  |  |  |  |")
        lines.extend(
            [
                "",
                "Approve:",
                "",
                "```text",
                'slip-pdf-md approve --vault "PATH" --sha256 SHA256 --by "Lawyer Name"',
                "```",
                "",
                footer_markdown(),
            ]
        )
        path.write_text(with_single_footer("\n".join(lines)), encoding="utf-8")
        return path

    def gubernatio_rows(self, sha256: str | None = None, *, limit: int = 200) -> list[dict]:
        if sha256:
            rows = self.conn.execute(
                'SELECT * FROM "GUBERNATIO" WHERE sha256 = ? ORDER BY id DESC LIMIT ?',
                (sha256, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                'SELECT * FROM "GUBERNATIO" ORDER BY id DESC LIMIT ?',
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
