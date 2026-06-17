"""FastAPI auth/me routes — TestClient smoke + DB integration.

Requires DATABASE_URL in project .env (same as other integration tests).
"""

from __future__ import annotations

import os
import uuid

import pytest
from auth_test_helpers import register_and_login, verification_token_for_email
from fastapi.testclient import TestClient

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DATABASE_URL must be set (project .env)",
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    from metropolis.main import create_app

    app = create_app()
    app.state.limiter.enabled = False
    with TestClient(app) as test_client:
        yield test_client


def _unique_email(prefix: str = "fastapi-auth") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_register_returns_token_and_unverified_user(client: TestClient) -> None:
    email = _unique_email()
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": "AuthTest123!", "fullName": "Test User"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "success"
    assert body["token"]
    assert body["user"]["email"] == email
    assert body["user"]["isVerified"] is False


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


def test_register_rejects_weak_password(client: TestClient) -> None:
    resp = client.post(
        "/api/auth/register",
        json={"email": _unique_email("weak"), "password": "short", "fullName": "Weak User"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["status"] == "validation_error"
    assert "8 characters" in body["message"]


def test_register_rejects_password_without_number(client: TestClient) -> None:
    resp = client.post(
        "/api/auth/register",
        json={
            "email": _unique_email("nonum"),
            "password": "NoNumbers!",
            "fullName": "No Num",
        },
    )
    assert resp.status_code == 400
    assert "number" in resp.json()["message"].lower()


def test_register_rejects_password_without_special_character(client: TestClient) -> None:
    resp = client.post(
        "/api/auth/register",
        json={
            "email": _unique_email("nospec"),
            "password": "NoSpecial123",
            "fullName": "No Spec",
        },
    )
    assert resp.status_code == 400
    assert "special character" in resp.json()["message"].lower()


def test_register_ignores_admin_role_escalation(client: TestClient) -> None:
    resp = client.post(
        "/api/auth/register",
        json={
            "email": _unique_email("escalate"),
            "password": "Escalate123!",
            "fullName": "Escalation User",
            "role": "admin",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "success"
    assert body["user"]["isVerified"] is False


def test_login_works_before_email_verified(client: TestClient) -> None:
    email = _unique_email("unverified")
    password = "LoginTest123!"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "fullName": "Login User"},
    )
    assert reg.status_code == 201, reg.text
    assert reg.json()["user"]["isVerified"] is False

    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["isVerified"] is False


def test_resend_verification_for_unverified_user(client: TestClient) -> None:
    email = _unique_email("resend")
    password = "ResendTest123!"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "fullName": "Resend User"},
    )
    assert reg.status_code == 201, reg.text
    token = reg.json()["token"]

    resp = client.post(
        "/api/auth/resend-verification",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "success"


def test_unverified_user_cannot_create_listing(client: TestClient) -> None:
    email = _unique_email("nolist")
    reg = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "NoList123!",
            "fullName": "No List User",
        },
    )
    assert reg.status_code == 201, reg.text
    token = reg.json()["token"]

    resp = client.post(
        "/api/listings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Car",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "dailyRate": 50,
            "pricePerDay": 50,
        },
    )
    assert resp.status_code == 403
    assert resp.json()["message"] == "EMAIL_NOT_VERIFIED"


def test_verify_email_allows_login(client: TestClient) -> None:
    email = _unique_email("verify-login")
    password = "VerifyLogin123!"
    token = register_and_login(
        client,
        DATABASE_URL,
        email=email,
        password=password,
        full_name="Verify Login",
    )
    resp = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["email"] == email


def test_verify_email_invalid_token_rejected(client: TestClient) -> None:
    resp = client.get("/api/auth/verify-email?token=not-a-real-token")
    assert resp.status_code == 400
    assert resp.json()["status"] == "validation_error"


def test_verify_email_is_idempotent(client: TestClient) -> None:
    email = _unique_email("verify-twice")
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": "VerifyTwice123!", "fullName": "Twice User"},
    )
    assert reg.status_code == 201, reg.text
    token = verification_token_for_email(DATABASE_URL, email)

    first = client.get(f"/api/auth/verify-email?token={token}")
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "success"

    second = client.get(f"/api/auth/verify-email?token={token}")
    assert second.status_code == 200, second.text
    assert second.json()["status"] == "success"


def test_login_success(client: TestClient) -> None:
    email = _unique_email("login")
    password = "LoginTest123!"
    register_and_login(
        client,
        DATABASE_URL,
        email=email,
        password=password,
        full_name="Login User",
    )
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["email"] == email


def test_login_wrong_password_rejected(client: TestClient) -> None:
    email = _unique_email("wrongpw")
    password = "Correct123!"
    register_and_login(
        client,
        DATABASE_URL,
        email=email,
        password=password,
        full_name="Test",
    )
    resp = client.post("/api/auth/login", json={"email": email, "password": "Wrong999!"})
    assert resp.status_code == 400
    assert resp.json()["status"] == "validation_error"


def test_login_unknown_email_rejected(client: TestClient) -> None:
    resp = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "Whatever123!"},
    )
    assert resp.status_code == 400
    assert resp.json()["status"] == "validation_error"


def test_me_requires_auth(client: TestClient) -> None:
    resp = client.get("/api/me")
    assert resp.status_code == 401
    assert resp.json()["status"] == "error"


def test_me_returns_current_user(client: TestClient) -> None:
    email = _unique_email("me")
    token = register_and_login(
        client,
        DATABASE_URL,
        email=email,
        password="MeTest123!",
        full_name="Me User",
    )
    resp = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    user = resp.json()["user"]
    assert user["email"] == email
    assert user["fullName"] == "Me User"
    assert user["hasEmail"] is True
    assert user["isVerified"] is True


def test_patch_me_updates_profile(client: TestClient) -> None:
    email = _unique_email("patch")
    token = register_and_login(
        client,
        DATABASE_URL,
        email=email,
        password="PatchMe123!",
        full_name="Before",
    )
    resp = client.patch(
        "/api/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"fullName": "After Name", "about": "Hello world"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["fullName"] == "After Name"
    assert resp.json()["user"]["about"] == "Hello world"


def test_patch_me_blank_profile_fields_become_null(client: TestClient) -> None:
    token = register_and_login(
        client,
        DATABASE_URL,
        email=_unique_email("patch-blank"),
        password="PatchBlank123!",
        full_name="Blank User",
    )
    resp = client.patch(
        "/api/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"fullName": "   ", "phone": ""},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user"]["fullName"] is None
    assert body["user"]["phone"] is None


def test_patch_me_requires_auth(client: TestClient) -> None:
    resp = client.patch("/api/me", json={"fullName": "No Auth"})
    assert resp.status_code == 401


def test_patch_me_rejects_unknown_fields(client: TestClient) -> None:
    email = _unique_email("patch-extra")
    token = register_and_login(
        client,
        DATABASE_URL,
        email=email,
        password="PatchMe123!",
        full_name="User",
    )
    resp = client.patch(
        "/api/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"fullName": "Ok", "unexpectedField": "nope"},
    )
    assert resp.status_code == 400
    assert resp.json()["status"] == "validation_error"


def test_patch_me_rejects_email_and_role_updates(client: TestClient) -> None:
    email = _unique_email("patch-protected")
    token = register_and_login(
        client,
        DATABASE_URL,
        email=email,
        password="PatchProt123!",
        full_name="Protected User",
    )

    email_resp = client.patch(
        "/api/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "hacker@example.com"},
    )
    assert email_resp.status_code == 400
    assert email_resp.json()["status"] == "validation_error"

    role_resp = client.patch(
        "/api/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "admin", "isAdmin": True},
    )
    assert role_resp.status_code == 400
    assert role_resp.json()["status"] == "validation_error"

    me_resp = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    body = me_resp.json()["user"]
    assert body["email"] == email
    assert body["isAdmin"] is False


def test_patch_me_sanitizes_xss_in_full_name(client: TestClient) -> None:
    token = register_and_login(
        client,
        DATABASE_URL,
        email=_unique_email("patch-xss"),
        password="PatchXss123!",
        full_name="Before",
    )
    resp = client.patch(
        "/api/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"fullName": "<script>alert(1)</script>Jane Doe"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["fullName"] == "Jane Doe"
