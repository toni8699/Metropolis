"""Shared fixtures for backend tests (integration env + HTTP helper)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")


def integration_env() -> tuple[str, str]:
    api_url = os.environ.get("INTEGRATION_API_URL", "http://localhost:5000").rstrip("/")
    database_url = os.environ.get("DATABASE_URL", "").strip()
    return api_url, database_url


@pytest.fixture(scope="session")
def api_url() -> str:
    return integration_env()[0]


@pytest.fixture(scope="session")
def database_url() -> str:
    db = integration_env()[1]
    if not db:
        pytest.skip("DATABASE_URL must be set (project .env)")
    return db


def api_request(
    api_url: str,
    method: str,
    path: str,
    *,
    token: str | None = None,
    json: dict | None = None,
    timeout: float = 30,
) -> requests.Response:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(
        method, f"{api_url}{path}", headers=headers, json=json, timeout=timeout
    )
