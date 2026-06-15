"""FastAPI auth/me routes — TestClient smoke + DB integration.

Requires DATABASE_URL in project .env (same as other integration tests).
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

os.environ.setdefault("FLASK_DEBUG", "1")
os.environ["RATELIMIT_ENABLED"] = "0"

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DATABASE_URL must be set (project .env)",
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    from metropolis.main import app

    app.state.limiter.enabled = False
    with TestClient(app) as test_client:
        yield test_client


def _unique_email(prefix: str = "fastapi-auth") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_register_returns_token_and_user(client: TestClient) -> None:
    resp = client.post(
        "/api/auth/register",
        json={"email": _unique_email(), "password": "AuthTest123!", "fullName": "Test User"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "success"
    assert "token" in body
    assert body["user"]["isAdmin"] is False
    assert body["user"]["hasListings"] is False


def test_register_duplicate_email_rejected(client: TestClient) -> None:
    email = _unique_email("dup")
    payload = {"email": email, "password": "AuthTest123!", "fullName": "Dup User"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 400
    assert resp.json()["status"] == "validation_error"


def test_register_missing_fields_validation_error(client: TestClient) -> None:
    resp = client.post("/api/auth/register", json={"email": _unique_email("nopass")})
    assert resp.status_code == 400
    assert resp.json()["status"] == "validation_error"


def test_login_success(client: TestClient) -> None:
    email = _unique_email("login")
    password = "LoginTest123!"
    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "fullName": "Login User"},
    )
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["email"] == email


def test_login_wrong_password_rejected(client: TestClient) -> None:
    email = _unique_email("wrongpw")
    client.post(
        "/api/auth/register",
        json={"email": email, "password": "Correct123!", "fullName": "Test"},
    )
    resp = client.post("/api/auth/login", json={"email": email, "password": "Wrong999!"})
    assert resp.status_code == 400
    assert resp.json()["status"] == "validation_error"


def test_me_requires_auth(client: TestClient) -> None:
    resp = client.get("/api/me")
    assert resp.status_code == 401
    assert resp.json()["status"] == "error"


def test_me_returns_current_user(client: TestClient) -> None:
    email = _unique_email("me")
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": "MeTest123!", "fullName": "Me User"},
    )
    token = reg.json()["token"]
    resp = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    user = resp.json()["user"]
    assert user["email"] == email
    assert user["fullName"] == "Me User"
    assert user["hasEmail"] is True


def test_patch_me_updates_profile(client: TestClient) -> None:
    email = _unique_email("patch")
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": "PatchMe123!", "fullName": "Before"},
    )
    token = reg.json()["token"]
    resp = client.patch(
        "/api/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"fullName": "After Name", "about": "Hello world"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["fullName"] == "After Name"
    assert resp.json()["user"]["about"] == "Hello world"


def test_patch_me_rejects_unknown_fields(client: TestClient) -> None:
    email = _unique_email("patch-extra")
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": "PatchMe123!", "fullName": "User"},
    )
    token = reg.json()["token"]
    resp = client.patch(
        "/api/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"fullName": "Ok", "unexpectedField": "nope"},
    )
    assert resp.status_code == 400
    assert resp.json()["status"] == "validation_error"
