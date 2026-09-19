"""Convert-run mutex: one Convert-PDF-TO-MARKDOWN process at a time.

Scope
-----
This mutex is **tool-local**. It must NOT stop Publish-to-Website, Markdown-to-HTML,
or any other Satyagraha tool from running in parallel.

- Lock file + CONVERT_LEASE sqlite live only under:
  TOOLS/_runtime-state/Convert-PDF-TO-MARKDOWN-01/
- They do **not** lock the org-wide **GUBERNATIO** ledger database.
- **GUBERNATIO** remains the append-only audit/control table for *all* firm tools;
  each tool may write its own job rows there while Convert holds this mutex.

API-key leasing (fingerprint rows on **GUBERNATIO**) is a separate mechanism.
"""

from __future__ import annotations

import json
import os
import socket
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))

LEASE_HELD = "HELD"
LEASE_FREE = "FREE"
DEFAULT_TTL_SECONDS = 30 * 60
LOCK_NAME = "CONVERT.lock"
LEASE_DB_NAME = "CONVERT_LEASE.sqlite"
TOOL_RUNTIME_DIRNAME = "Convert-PDF-TO-MARKDOWN-01"

CONVERT_LEASE_DDL = """
CREATE TABLE IF NOT EXISTS "CONVERT_LEASE" (
    id            INTEGER PRIMARY KEY CHECK (id = 1),
    lease_status  TEXT NOT NULL,
    host          TEXT,
    agent         TEXT,
    pid           INTEGER,
    run_id        TEXT,
    acquired_at   TEXT,
    heartbeat_at  TEXT,
    expires_at    TEXT,
    lock_path     TEXT,
    note          TEXT
);
"""


class ConvertBusy(RuntimeError):
    def __init__(self, message: str, *, holder: dict | None = None):
        super().__init__(message)
        self.holder = holder or {}


@dataclass
class MutexHold:
    run_id: str
    lock_file: Path
    db_path: Path
    host: str
    agent: str
    pid: int
    acquired_at: str
    fd: int | None = None


def _now() -> datetime:
    return datetime.now(IST)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _now()).isoformat(timespec="seconds")


def _ttl_seconds() -> int:
    raw = (os.environ.get("SLIP_CONVERT_LEASE_SECONDS") or "").strip()
    if raw.isdigit():
        return max(60, int(raw))
    return DEFAULT_TTL_SECONDS


def runtime_mutex_dir() -> Path:
    override = (os.environ.get("SLIP_CONVERT_MUTEX_DIR") or "").strip()
    if override:
        return Path(override)
    tools_root = Path(__file__).resolve().parents[3]
    return tools_root / "_runtime-state" / TOOL_RUNTIME_DIRNAME


def lock_path() -> Path:
    return runtime_mutex_dir() / LOCK_NAME


def lease_db_path() -> Path:
    """Dedicated sqlite — never the Document-Hash-Registry / GUBERNATIO DB."""
    override = (os.environ.get("SLIP_CONVERT_LEASE_DB") or "").strip()
    if override:
        return Path(override)
    return runtime_mutex_dir() / LEASE_DB_NAME


def who() -> tuple[str, str, int]:
    host = os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or socket.gethostname()
    agent = os.environ.get("SLIP_AGENT") or os.environ.get("GROK_AGENT") or "Spock"
    return str(host), str(agent), int(os.getpid())


def _pid_alive(pid: int | None) -> bool:
    if not pid or int(pid) <= 0:
        return False
    try:
        if os.name == "nt":
            import ctypes
            handle = ctypes.windll.kernel32.OpenProcess(0x1000, 0, int(pid))
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
            return False
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False
    except Exception:
        return False


def _ensure_lease_table(conn: sqlite3.Connection) -> None:
    conn.execute(CONVERT_LEASE_DDL)
    row = conn.execute('SELECT id FROM "CONVERT_LEASE" WHERE id = 1').fetchone()
    if row is None:
        conn.execute(
            'INSERT INTO "CONVERT_LEASE"(id, lease_status) VALUES (1, ?)',
            (LEASE_FREE,),
        )
    conn.commit()


def _row_to_dict(conn: sqlite3.Connection, row) -> dict | None:
    if row is None:
        return None
    if isinstance(row, sqlite3.Row):
        return dict(row)
    cols = [c[1] for c in conn.execute('PRAGMA table_info("CONVERT_LEASE")').fetchall()]
    return {cols[i]: row[i] for i in range(len(cols))}


def _lease_stale(row: dict | None, *, now: datetime | None = None) -> bool:
    if not row or row.get("lease_status") != LEASE_HELD:
        return True
    now = now or _now()
    exp = row.get("expires_at") or ""
    try:
        exp_dt = datetime.fromisoformat(str(exp).replace("Z", "+00:00"))
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=IST)
        if now > exp_dt.astimezone(IST):
            return True
    except Exception:
        return True
    try:
        pid_i = int(row.get("pid") or 0)
    except (TypeError, ValueError):
        pid_i = 0
    if pid_i and not _pid_alive(pid_i):
        return True
    return False


def _read_lock_meta(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        try:
            return {"raw": path.read_text(encoding="utf-8", errors="replace")[:500]}
        except Exception:
            return {}


def acquire_convert_mutex(
    db_path: Path | None = None,
    *,
    steal_if_stale: bool = True,
    force_steal: bool = False,
    run_id: str | None = None,
) -> MutexHold:
    """Acquire convert-only mutex.

    db_path is ignored. CONVERT_LEASE always uses lease_db_path() under the
    convert runtime folder — never the GUBERNATIO / Document-Hash-Registry DB.
    """
    host, agent, pid = who()
    run_id = run_id or uuid.uuid4().hex[:12]
    ttl = _ttl_seconds()
    acquired_at = _iso()
    expires_at = _iso(_now() + timedelta(seconds=ttl))
    lpath = lock_path()
    lpath.parent.mkdir(parents=True, exist_ok=True)

    lease_db = lease_db_path()
    lease_db.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(lease_db), timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_lease_table(conn)
        row = _row_to_dict(conn, conn.execute('SELECT * FROM "CONVERT_LEASE" WHERE id = 1').fetchone())
        stale = _lease_stale(row)
        if row and row.get("lease_status") == LEASE_HELD and not stale and not force_steal:
            raise ConvertBusy(
                "Convert-PDF-TO-MARKDOWN already running "
                f"(host={row.get('host')} agent={row.get('agent')} pid={row.get('pid')} "
                f"run_id={row.get('run_id')} expires_at={row.get('expires_at')}). "
                "Other Satyagraha tools are unaffected. "
                "Wait, or pass --steal-convert-lock only if that convert PID is dead.",
                holder=row,
            )
        if row and row.get("lease_status") == LEASE_HELD and stale and not steal_if_stale and not force_steal:
            raise ConvertBusy(
                "Stale CONVERT_LEASE present; re-run with --steal-convert-lock.",
                holder=row,
            )

        if lpath.exists():
            meta = _read_lock_meta(lpath)
            try:
                lock_pid_i = int(meta.get("pid") or 0)
            except (TypeError, ValueError):
                lock_pid_i = 0
            lock_alive = _pid_alive(lock_pid_i)
            if lock_alive and not force_steal:
                raise ConvertBusy(
                    f"CONVERT.lock held by live pid={lock_pid_i} agent={meta.get('agent')} "
                    f"host={meta.get('host')}. Other tools may still run. "
                    "Wait or --steal-convert-lock if wrong.",
                    holder=meta,
                )
            if lpath.exists():
                try:
                    lpath.unlink()
                except OSError as exc:
                    raise ConvertBusy(f"Could not clear stale CONVERT.lock: {exc}", holder=meta) from exc

        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(str(lpath), flags)
        except FileExistsError as exc:
            meta = _read_lock_meta(lpath)
            raise ConvertBusy(f"CONVERT.lock create lost race: {meta}", holder=meta) from exc

        payload = {
            "tool": "Convert-PDF-TO-MARKDOWN-01",
            "scope": "convert-only",
            "does_not_block": ["Publish-to-Website", "Markdown-to-HTML", "other SLG tools"],
            "run_id": run_id,
            "host": host,
            "agent": agent,
            "pid": pid,
            "acquired_at": acquired_at,
            "expires_at": expires_at,
            "lease_db": str(lease_db),
            "table": "CONVERT_LEASE",
            "gubernatio": "not locked - org ledger remains writable",
        }
        os.write(fd, (json.dumps(payload, indent=2) + "\n").encode("utf-8"))
        os.close(fd)

        conn.execute(
            """
            UPDATE "CONVERT_LEASE"
               SET lease_status = ?, host = ?, agent = ?, pid = ?, run_id = ?,
                   acquired_at = ?, heartbeat_at = ?, expires_at = ?, lock_path = ?, note = ?
             WHERE id = 1
            """,
            (
                LEASE_HELD,
                host,
                agent,
                pid,
                run_id,
                acquired_at,
                acquired_at,
                expires_at,
                str(lpath),
                "convert-run mutex only; GUBERNATIO and other tools unrestricted",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return MutexHold(
        run_id=run_id,
        lock_file=lpath,
        db_path=lease_db,
        host=host,
        agent=agent,
        pid=pid,
        acquired_at=acquired_at,
        fd=None,
    )


def heartbeat_convert_mutex(hold: MutexHold) -> None:
    ttl = _ttl_seconds()
    hb = _iso()
    exp = _iso(_now() + timedelta(seconds=ttl))
    conn = sqlite3.connect(str(hold.db_path), timeout=30)
    try:
        _ensure_lease_table(conn)
        conn.execute(
            """
            UPDATE "CONVERT_LEASE"
               SET heartbeat_at = ?, expires_at = ?
             WHERE id = 1 AND run_id = ? AND lease_status = ?
            """,
            (hb, exp, hold.run_id, LEASE_HELD),
        )
        conn.commit()
    finally:
        conn.close()
    if hold.lock_file.exists():
        try:
            meta = _read_lock_meta(hold.lock_file)
            meta["heartbeat_at"] = hb
            meta["expires_at"] = exp
            hold.lock_file.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass


def release_convert_mutex(hold: MutexHold | None) -> None:
    if hold is None:
        return
    conn = sqlite3.connect(str(hold.db_path), timeout=30)
    try:
        _ensure_lease_table(conn)
        conn.execute(
            """
            UPDATE "CONVERT_LEASE"
               SET lease_status = ?, heartbeat_at = ?, note = ?
             WHERE id = 1 AND run_id = ?
            """,
            (LEASE_FREE, _iso(), "released; other tools were never blocked", hold.run_id),
        )
        conn.commit()
    finally:
        conn.close()
    try:
        if hold.lock_file.exists():
            meta = _read_lock_meta(hold.lock_file)
            if not meta or meta.get("run_id") == hold.run_id or int(meta.get("pid") or 0) == hold.pid:
                hold.lock_file.unlink()
    except OSError:
        pass


# Back-compat aliases used by cli.py
ConvertBusyError = ConvertBusy
acquire_convert_mutex_alias = acquire_convert_mutex
