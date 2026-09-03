"""Environment checks: Python, PyMuPDF, Tesseract, SLIP folders, Mistral key, registry."""

from __future__ import annotations

import shutil
import sys

from slip_pdf_md.engines.pymupdf_engine import TESSERACT_WINDOWS, configure_tesseract
from slip_pdf_md.paths import SLIP_DIR_NAMES, SlipPaths
from slip_pdf_md.registry import Registry, RegistryCorrupt
from slip_pdf_md.secrets import mistral_key_status


def run_doctor(paths: SlipPaths | None = None) -> dict:
    checks = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    add("python", sys.version_info >= (3, 11), sys.version.split()[0])

    try:
        import fitz

        add("pymupdf", True, getattr(fitz, "version", ("ok",))[0] if isinstance(getattr(fitz, "version", None), tuple) else str(getattr(fitz, "VersionBind", "ok")))
    except Exception as exc:
        add("pymupdf", False, str(exc))

    tess = None
    if TESSERACT_WINDOWS.exists():
        tess = str(TESSERACT_WINDOWS)
    else:
        tess = shutil.which("tesseract")
    configure_tesseract()
    add("tesseract", bool(tess), tess or "not found (OCR of scanned pages will fail)")

    try:
        import pytesseract  # noqa: F401

        add("pytesseract", True, "import ok")
    except Exception as exc:
        add("pytesseract", False, str(exc))

    vault_root = paths.root if paths is not None else None
    add("mistral_api_key", True, mistral_key_status(vault_root=vault_root))

    if paths is not None:
        missing = [name for name in SLIP_DIR_NAMES if not (paths.root / name).is_dir()]
        add("slip_folders", not missing, "all present" if not missing else "missing: " + ", ".join(missing))
        writable = False
        try:
            probe = paths.root / ".slip_write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            writable = True
        except Exception as exc:
            add("write_access", False, str(exc))
        else:
            add("write_access", writable, str(paths.root))
        add("registry_path", True, str(paths.registry_path))
        try:
            registry = Registry(paths.registry_path)
            health = registry.health()
            registry.close()
            add(
                "registry_integrity",
                health["integrity_ok"],
                f"documents={health['documents']} sightings={health['sightings']} GUBERNATIO={health.get('gubernatio', 0)}",
            )
            add("registry_backup", health["backup_exists"], health["backup_path"])
            if health["restored_from_backup"]:
                add("registry_restored", True, "live sqlite was missing; restored from .bak")
            from slip_pdf_md.key_lease import SENTINEL_NAME, sentinel_path

            sent = sentinel_path(paths.registry_dir)
            add(
                "mistral_key_lease_sentinel",
                True,
                "absent (free)" if not sent.exists() else f"present {SENTINEL_NAME} (a Mistral convert may be RUNNING)",
            )
        except RegistryCorrupt as exc:
            add("registry_integrity", False, str(exc))

    return {
        "ok": all(c["ok"] for c in checks if c["name"] not in {"tesseract", "mistral_api_key"}),
        "checks": checks,
    }


def format_doctor(report: dict) -> str:
    lines = ["Satyagraha Law Group — PDF to Markdown — doctor", ""]
    for check in report["checks"]:
        mark = "OK" if check["ok"] else "FAIL"
        lines.append(f"[{mark}] {check['name']}: {check['detail']}")
    lines.append("")
    lines.append("overall: " + ("ok" if report["ok"] else "not ok"))
    return "\n".join(lines)
