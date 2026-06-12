"""Integration tests for authentication flows.

Requires: running API + DATABASE_URL set (same as other integration tests).
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_URL = os.environ.get("INTEGRATION_API_URL", "http://localhost:5000").rstrip("/")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DATABASE_URL must be set (project .env)",
)


def _api(method: str, path: str, *, json: dict | None = None, token: str | None = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, f"{API_URL}{path}", headers=headers, json=json, timeout=15)


def _unique_email(prefix: str = "auth-test") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


def test_register_returns_token_and_user():
    resp = _api(
        "POST",
        "/api/auth/register",
        json={"email": _unique_email(), "password": "AuthTest123!", "fullName": "Test User"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "token" in body
    assert body["user"]["email"].endswith("@example.com")
    assert body["user"]["isAdmin"] is False


def test_register_sets_full_name():
    email = _unique_email("named")
    resp = _api(
        "POST",
        "/api/auth/register",
        json={"email": email, "password": "AuthTest123!", "fullName": "Jane Doe"},
    )
    assert resp.status_code == 201
    assert resp.json()["user"]["fullName"] == "Jane Doe"


def test_register_duplicate_email_rejected():
    email = _unique_email("dup")
    payload = {"email": email, "password": "AuthTest123!", "fullName": "Dup User"}
    first = _api("POST", "/api/auth/register", json=payload)
    assert first.status_code == 201

    second = _api("POST", "/api/auth/register", json=payload)
    assert second.status_code in (400, 409, 422), second.text


def test_register_missing_password_rejected():
    resp = _api(
        "POST",
        "/api/auth/register",
        json={"email": _unique_email("nopass"), "fullName": "No Pass"},
    )
    assert resp.status_code in (400, 422), resp.text


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def test_login_success():
    email = _unique_email("login")
    password = "LoginTest123!"
    _api(
        "POST",
        "/api/auth/register",
        json={"email": email, "password": password, "fullName": "Login User"},
    )
    resp = _api("POST", "/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "token" in body
    assert body["user"]["email"] == email


def test_login_wrong_password_rejected():
    email = _unique_email("wrongpw")
    _api(
        "POST",
        "/api/auth/register",
        json={"email": email, "password": "Correct123!", "fullName": "Test"},
    )
    resp = _api("POST", "/api/auth/login", json={"email": email, "password": "Wrong999!"})
    assert resp.status_code in (400, 401), resp.text


def test_login_unknown_email_rejected():
    resp = _api(
        "POST",
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "Whatever123!"},
    )
    assert resp.status_code in (400, 401), resp.text


# ---------------------------------------------------------------------------
# /api/me
# ---------------------------------------------------------------------------


def test_me_returns_current_user():
    email = _unique_email("me")
    reg = _api(
        "POST",
        "/api/auth/register",
        json={"email": email, "password": "MeTest123!", "fullName": "Me User"},
    )
    assert reg.status_code == 201
    token = reg.json()["token"]

    resp = _api("GET", "/api/me", token=token)
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["email"] == email


def test_me_requires_auth():
    resp = _api("GET", "/api/me")
    assert resp.status_code == 401


def test_patch_me_updates_profile():
    email = _unique_email("patch-me")
    reg = _api(
        "POST",
        "/api/auth/register",
        json={"email": email, "password": "PatchMe123!", "fullName": "Before Name"},
    )
    assert reg.status_code == 201
    token = reg.json()["token"]

    resp = _api(
        "PATCH",
        "/api/me",
        token=token,
        json={"fullName": "After Name", "phone": "+1 514 555 0100"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user"]["email"] == email
    assert body["user"]["fullName"] == "After Name"
    assert body["user"]["phone"] == "+1 514 555 0100"


def test_patch_me_blank_profile_fields_become_null():
    reg = _api(
        "POST",
        "/api/auth/register",
        json={
            "email": _unique_email("patch-blank"),
            "password": "PatchBlank123!",
            "fullName": "Blank User",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["token"]

    resp = _api(
        "PATCH",
        "/api/me",
        token=token,
        json={"fullName": "   ", "phone": ""},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user"]["fullName"] is None
    assert body["user"]["phone"] is None


def test_patch_me_requires_auth():
    resp = _api("PATCH", "/api/me", json={"fullName": "No Auth"})
    assert resp.status_code == 401
