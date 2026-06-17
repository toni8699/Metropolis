"""Shared fixtures for backend tests (integration env + HTTP helper)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env", override=False)

_test_db = os.environ.get("TEST_DATABASE_URL", "").strip()
if _test_db:
    os.environ["DATABASE_URL"] = _test_db

os.environ.setdefault("DEBUG", "1")
os.environ["RATELIMIT_ENABLED"] = "0"

_INTEGRATION_TEST_FILES = frozenset(
    {
        "test_booking_approval_integration.py",
        "test_fastapi_auth.py",
        "test_fleet_sync_integration.py",
        "test_message_integration.py",
        "test_reviews_integration.py",
        "test_search_integration.py",
    }
)


def _integration_db_skip_reason() -> str | None:
    url = os.environ.get("DATABASE_URL", "").strip().lower()
    if not url:
        return None
    if "localhost" in url or "127.0.0.1" in url or "@postgres_test:" in url:
        return None
    return (
        "Integration tests skip remote DATABASE_URL (Neon). "
        "Use: docker compose -f docker-compose.yml -f docker-compose.test.yml "
        "--profile test run --rm test"
    )


def pytest_collection_modifyitems(config, items):
    reason = _integration_db_skip_reason()
    if not reason:
        return
    skip = pytest.mark.skip(reason=reason)
    for item in items:
        if item.path.name in _INTEGRATION_TEST_FILES:
            item.add_marker(skip)


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
    return requests.request(method, f"{api_url}{path}", headers=headers, json=json, timeout=timeout)
