import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-pytest-only-0123456789")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("LOCAL_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", "100000")
    from backend.app import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def signup(client, name="alice"):
    """Create a dummy user and return auth headers."""
    r = client.post("/api/register", json={"name": name.title(), "username": name, "email": f"{name}@example.com",
                                           "password": "Dummy#Pass123"})
    assert r.status_code == 201, r.text
    tok = client.post("/api/login", json={"email": f"{name}@example.com", "password": "Dummy#Pass123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def make_skill(client, h, name="Photography", category="Photography"):
    return client.post("/api/skills", headers=h, json={"skill_name": name, "category": category}).json()["skill_id"]
