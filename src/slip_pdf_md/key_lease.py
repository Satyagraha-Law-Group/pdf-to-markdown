"""Remote-API key lease. Sentinel lives next to GUBERNATIO, never inside sqlite.

The sentinel filename is Anil's exact name:
SLG-pdf_to_md_file_naming_convention.text

GUBERNATIO stores only a SHA-256 fingerprint of a key, never the key.
The provider (mistral today; docling, google, claude, hermes, reducto later)
is stored beside the fingerprint so the same machinery leases any remote API.
Same fingerprint stays exclusive. Different fingerprints may run in parallel.
Expired RUNNING leases are treated as free so the next lawyer is not stuck.
Local engines (pymupdf / Tesseract) take no lease.
"""

from __future__ import annotations

import hashlib
import os
import re
from datetime import timedelta
from pathlib import Path

from slip_pdf_md.naming import iso_calcutta, now_calcutta
from slip_pdf_md.secrets import DUMMY_KEY

SENTINEL_NAME = "SLG-pdf_to_md_file_naming_convention.text"
LEASE_RUNNING = "RUNNING"
LEASE_FREE = "FREE"
LEASE_TTL_SECONDS = 15 * 60
FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")

LOCAL_ENGINE_NAMES = {"pymupdf", "tesseract", "local"}
MISTRAL_ENGINE_NAMES = {"mistral", "mistralai", "mistral-ocr"}
REMOTE_API_ENGINES = MISTRAL_ENGINE_NAMES | {
    "docling",
    "google",
    "claude",
    "hermes",
    "reducto",
    "anthropic",
}

PROVIDER_KEY_ENVS = {
    "mistral": ("MISTRAL_API_KEY", "MISTRALAI_API_KEY"),
    "mistralai": ("MISTRAL_API_KEY", "MISTRALAI_API_KEY"),
    "mistral-ocr": ("MISTRAL_API_KEY", "MISTRALAI_API_KEY"),
    "docling": ("DOCLING_API_KEY",),
    "google": ("GOOGLE_API_KEY", "GOOGLE_OCR_API_KEY"),
    "claude": ("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"),
    "anthropic": ("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"),
    "hermes": ("HERMES_API_KEY",),
    "reducto": ("REDUCTO_API_KEY",),
}


def normalize_engine(engine_name: str | None) -> str:
    return (engine_name or "").lower().replace("_", "-").strip()


def uses_remote_api(engine_name: str | None) -> bool:
    name = normalize_engine(engine_name)
    if not name or name in LOCAL_ENGINE_NAMES:
        return False
    if name in REMOTE_API_ENGINES:
        return True
    return name.endswith("-api")


def uses_mistral(engine_name: str | None) -> bool:
    return normalize_engine(engine_name) in MISTRAL_ENGINE_NAMES


def api_provider(engine_name: str | None) -> str:
    name = normalize_engine(engine_name)
    if name in MISTRAL_ENGINE_NAMES:
        return "mistral"
    return name or "remote"


def lease_ttl_seconds() -> int:
    raw = os.environ.get("SLIP_KEY_LEASE_SECONDS", "").strip()
    if raw.isdigit():
        return max(1, int(raw))
    return LEASE_TTL_SECONDS


def api_key_fingerprint(key: str) -> str:
    return hashlib.sha256((key or "").encode("utf-8")).hexdigest()


def require_fingerprint(value: str | None) -> str | None:
    """Refuse anything that is not a 64-char SHA-256 hex digest."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if not FINGERPRINT_RE.match(text.lower()):
        raise ValueError(
            "GUBERNATIO refuses to store a secret. Pass a SHA-256 fingerprint only."
        )
    return text.lower()


def current_remote_key(engine_name: str | None = None, *, vault_root: Path | None = None) -> str:
    provider = api_provider(engine_name)
    env_names = PROVIDER_KEY_ENVS.get(provider, ())
    for name in env_names:
        env = (os.environ.get(name) or "").strip()
        if env:
            return env
    from slip_pdf_md.secrets import load_secrets

    loaded = load_secrets(vault_root=vault_root, into_environ=False)
    for name in env_names:
        got = (loaded.get(name) or "").strip()
        if got:
            return got
    return ""


def current_mistral_key(*, vault_root: Path | None = None) -> str:
    return current_remote_key("mistral", vault_root=vault_root)


def is_dummy_key(key: str) -> bool:
    return bool(key) and key.strip() == DUMMY_KEY


def sentinel_path(registry_dir: Path) -> Path:
    return Path(registry_dir) / SENTINEL_NAME


def _parse_iso(value: str | None):
    if not value:
        return None
    text = str(value).strip()
    try:
        from datetime import datetime

        return datetime.fromisoformat(text)
    except ValueError:
        return None


def lease_is_expired(expires_at: str | None, *, now=None) -> bool:
    moment = now or now_calcutta()
    exp = _parse_iso(expires_at)
    if exp is None:
        return True
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=moment.tzinfo)
    return moment >= exp


def touch_sentinel_exclusive(path: Path) -> bool:
    """Create the zero-byte sentinel. False if it already exists."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(str(path), flags)
    except FileExistsError:
        return False
    except OSError:
        return False
    try:
        os.close(fd)
    except OSError:
        pass
    return True


def remove_sentinel(path: Path) -> None:
    try:
        Path(path).unlink()
    except OSError:
        pass


def expiry_stamp(*, ttl: int | None = None) -> str:
    seconds = ttl if ttl is not None else lease_ttl_seconds()
    return iso_calcutta(now_calcutta() + timedelta(seconds=seconds))
