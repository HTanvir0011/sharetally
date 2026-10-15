import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PASSWORDS = {"reviewer": ("reviewer.demo", "review-demo-2026"), "clerk": ("clerk.demo", "clerk-demo-2026"),
             "auditor": ("auditor.demo", "audit-demo-2026")}


@pytest.fixture()
def app_client(tmp_path, monkeypatch):
    monkeypatch.setenv("SHARETALLY_DB", str(tmp_path / "test.db"))
    monkeypatch.setenv("SHARETALLY_PBKDF2_ITERATIONS", "1000")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    from sharetally import web
    from sharetally.config import Settings
    monkeypatch.setattr(web, "settings", Settings())
    from fastapi.testclient import TestClient
    with TestClient(web.app) as client:
        yield client


def login(client, role):
    username, password = PASSWORDS[role]
    page = client.get("/login")
    token = re.search(r'name="login_csrf" value="([^"]+)"', page.text).group(1)
    response = client.post("/login", data={"username": username, "password": password, "login_csrf": token,
                                           "next": "/dashboard"}, follow_redirects=False)
    assert response.status_code == 303, response.text
    return csrf_of(client)


def csrf_of(client):
    return re.search(r'name="csrf-token" content="([^"]+)"', client.get("/dashboard").text).group(1)


@pytest.fixture()
def seeded_conn():
    from sharetally import db, synthetic
    conn = db.connect(":memory:")
    db.init_schema(conn)
    db.seed(conn, synthetic.build_dataset())
    yield conn
    conn.close()
