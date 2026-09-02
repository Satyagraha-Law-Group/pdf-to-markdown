from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def slip_tree(tmp_path):
    from slip_pdf_md.scaffold import create_slip_tree

    return create_slip_tree(tmp_path / "SLIP_DOCUMENT_PROCESSING")
