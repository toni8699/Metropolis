"""Helpers for auth integration tests (email verification gate)."""

from __future__ import annotations

import psycopg2
import requests
from fastapi.testclient import TestClient


def verification_token_for_email(database_url: str, email: str) -> str:
    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT verification_token FROM app_user WHERE email = %s",
                (email,),
            )
            row = cur.fetchone()
    if not row or not row[0]:
        raise AssertionError(f"No verification token for {email}")
    return str(row[0])


def verify_registered_email(client: TestClient, database_url: str, email: str) -> None:
    token = verification_token_for_email(database_url, email)
    resp = client.get(f"/api/auth/verify-email?token={token}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "success"


def verify_registered_email_http(
    api_url: str,
    database_url: str,
    email: str,
    *,
    timeout: float = 30,
) -> None:
    token = verification_token_for_email(database_url, email)
    resp = requests.get(
        f"{api_url.rstrip('/')}/api/auth/verify-email",
        params={"token": token},
        timeout=timeout,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "success"


def register_and_login(
    client: TestClient,
    database_url: str,
    *,
    email: str,
    password: str,
    full_name: str,
) -> str:
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "fullName": full_name},
    )
    assert reg.status_code == 201, reg.text
    token = reg.json()["token"]
    verify_registered_email(client, database_url, email)
    return token


def register_and_login_http(
    api_url: str,
    database_url: str,
    *,
    email: str,
    password: str,
    full_name: str,
    timeout: float = 30,
) -> str:
    reg = requests.post(
        f"{api_url.rstrip('/')}/api/auth/register",
        json={"email": email, "password": password, "fullName": full_name},
        timeout=timeout,
    )
    assert reg.status_code == 201, reg.text
    token = reg.json()["token"]
    verify_registered_email_http(api_url, database_url, email, timeout=timeout)
    return token
