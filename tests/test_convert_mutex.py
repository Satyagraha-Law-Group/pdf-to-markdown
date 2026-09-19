"""Convert-run mutex: lock file + CONVERT_LEASE."""
from __future__ import annotations

from pathlib import Path

from slip_pdf_md.convert_mutex import (
    ConvertBusy,
    acquire_convert_mutex,
    release_convert_mutex,
)


def test_second_acquire_busy(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SLIP_CONVERT_MUTEX_DIR", str(tmp_path / "mutex"))
    db = tmp_path / "reg.sqlite"
    hold = acquire_convert_mutex(db)
    try:
        try:
            acquire_convert_mutex(db)
            assert False, "expected ConvertBusy"
        except ConvertBusy:
            pass
    finally:
        release_convert_mutex(hold)
    hold2 = acquire_convert_mutex(db)
    release_convert_mutex(hold2)
