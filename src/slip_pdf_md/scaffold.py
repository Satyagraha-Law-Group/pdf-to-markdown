"""Create the ten SLIP folders. Used by CLI init and scripts/deploy.py."""

from __future__ import annotations

from pathlib import Path

from slip_pdf_md.paths import SLIP_DIR_NAMES, SlipPaths, looks_like_slip_root


def resolve_slip_root(vault: Path) -> Path:
    vault = Path(vault).expanduser().resolve()
    if looks_like_slip_root(vault):
        return vault
    nested = vault / "SLIP_DOCUMENT_PROCESSING"
    return nested


def create_slip_tree(vault: Path) -> SlipPaths:
    root = resolve_slip_root(Path(vault))
    root.mkdir(parents=True, exist_ok=True)
    paths = SlipPaths(root)
    for name in SLIP_DIR_NAMES:
        (root / name).mkdir(parents=True, exist_ok=True)
        gitkeep = root / name / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("", encoding="utf-8")
    paths.registry_dir.mkdir(parents=True, exist_ok=True)
    return paths
