import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from web.app import app


def test_health_ok():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["product"] == "SLIP PDF to Markdown Ingestion Tool"
    assert "SLIP" in body["family"]
