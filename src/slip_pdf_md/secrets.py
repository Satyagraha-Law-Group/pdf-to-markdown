"""Load Mistral (and later) API keys from a local SECRETS file.

Real SECRETS files are gitignored. Setup writes a dummy SECRETS.txt and a
committed SECRETS.example. Never print secret values.
"""

from __future__ import annotations

import os
from pathlib import Path

DUMMY_KEY = "replace-with-your-mistral-api-key"
EXAMPLE_NAME = "SECRETS.example"
SECRETS_NAME = "SECRETS.txt"
EXAMPLE_BODY = """# SLIP PDF to Markdown — local secrets (gitignored copy is SECRETS.txt)
# Get a key: https://console.mistral.ai/api-keys
# This example is safe to commit. Do not put a real key here.

MISTRAL_API_KEY=replace-with-your-mistral-api-key
"""

DUMMY_BODY = """# Local secrets. This file is gitignored. Do not commit it.
# Replace the dummy value with your real Mistral API key.

MISTRAL_API_KEY=replace-with-your-mistral-api-key
"""


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()
    return value


def parse_secrets_text(text: str) -> dict[str, str]:
    """Parse KEY=value, setx KEY value, or a bare key line."""
    found: dict[str, str] = {}
    for raw in (text or "").splitlines() or [text or ""]:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lower = line.lower()
        if lower.startswith("setx "):
            rest = line[5:].strip()
            parts = rest.split(None, 1)
            if len(parts) == 2:
                found[parts[0].strip()] = _unquote(parts[1])
            continue
        if lower.startswith("set "):
            rest = line[4:].strip()
            if "=" in rest:
                key, val = rest.split("=", 1)
                found[key.strip()] = _unquote(val)
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            if key.startswith("export "):
                key = key[7:].strip()
            found[key] = _unquote(val)
            continue
        if len(line) >= 16 and " " not in line:
            found.setdefault("MISTRAL_API_KEY", line)
    return found


def candidate_secret_files(tool_root: Path | None = None, vault_root: Path | None = None) -> list[Path]:
    roots: list[Path] = []
    if tool_root:
        roots.append(Path(tool_root))
    if vault_root:
        v = Path(vault_root)
        roots.append(v)
        roots.append(v / "90_00_PROJECT_TOOLING" / "pdf-to-markdown")
        roots.append(v / "Convert-PDF-TO-MARKDOWN-01")
    here = Path(__file__).resolve().parents[2]
    roots.append(here)
    seen: set[Path] = set()
    files: list[Path] = []
    for root in roots:
        try:
            root = root.resolve()
        except OSError:
            continue
        if root in seen or not root.is_dir():
            continue
        seen.add(root)
        for name in (SECRETS_NAME, "SECRETS", ".env"):
            path = root / name
            if path.is_file():
                files.append(path)
        try:
            files.extend(sorted(root.glob("SECRETS-*.txt"), key=lambda p: p.stat().st_mtime, reverse=True))
        except OSError:
            pass
    # de-dupe preserving order
    out: list[Path] = []
    seen_f: set[Path] = set()
    for path in files:
        try:
            key = path.resolve()
        except OSError:
            key = path
        if key in seen_f:
            continue
        seen_f.add(key)
        out.append(path)
    return out


def load_secrets(
    tool_root: Path | None = None,
    vault_root: Path | None = None,
    *,
    into_environ: bool = True,
) -> dict[str, str]:
    merged: dict[str, str] = {}
    for path in candidate_secret_files(tool_root, vault_root):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        parsed = parse_secrets_text(text)
        for key, val in parsed.items():
            if not val:
                continue
            existing = merged.get(key, "")
            if val == DUMMY_KEY and existing and existing != DUMMY_KEY:
                continue
            if val != DUMMY_KEY or key not in merged:
                merged[key] = val
    if into_environ:
        for key, val in merged.items():
            if val and val != DUMMY_KEY and not os.environ.get(key):
                os.environ[key] = val
    return merged


def mistral_key_status(tool_root: Path | None = None, vault_root: Path | None = None) -> str:
    env = (os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRALAI_API_KEY") or "").strip()
    if env and env != DUMMY_KEY:
        return "set (environment)"
    loaded = load_secrets(tool_root, vault_root, into_environ=False)
    val = (loaded.get("MISTRAL_API_KEY") or loaded.get("MISTRALAI_API_KEY") or "").strip()
    if not val:
        return "not set (needed for --engine mistral)"
    if val == DUMMY_KEY:
        return "dummy placeholder in SECRETS.txt (replace with a real key)"
    return "set (SECRETS file)"


def write_secret_templates(tool_root: Path) -> dict[str, Path]:
    """Create SECRETS.example (safe) and SECRETS.txt (gitignored dummy if missing)."""
    tool_root = Path(tool_root)
    tool_root.mkdir(parents=True, exist_ok=True)
    example = tool_root / EXAMPLE_NAME
    secrets = tool_root / SECRETS_NAME
    example.write_text(EXAMPLE_BODY, encoding="utf-8")
    created_dummy = False
    if not secrets.exists():
        secrets.write_text(DUMMY_BODY, encoding="utf-8")
        created_dummy = True
    return {"example": example, "secrets": secrets, "created_dummy": created_dummy}  # type: ignore[dict-item]
