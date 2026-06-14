"""
Integration tests for date-aware listing search (GET /api/listings).

Requires a running backend and DATABASE_URL (same Neon DB as the API).

Run:
  docker compose up
  export $(grep -v '^#' .env | xargs)
  cd backend && uv sync --extra dev
  pytest tests/test_search_integration.py -v

Env (optional):
  INTEGRATION_API_URL  default http://localhost:5000
  INTEGRATION_LISTING_ID  force a listing id for booking overlap tests
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import psycopg2
import pytest
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_URL = os.environ.get("INTEGRATION_API_URL", "http://localhost:5000").rstrip("/")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
INTEGRATION_LISTING_ID = os.environ.get("INTEGRATION_LISTING_ID", "").strip()

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DATABASE_URL must be set (project .env)",
)

# Far-future window to avoid colliding with real bookings.
BOOKING_START = datetime(2099, 6, 1, 10, 0, tzinfo=timezone.utc)
BOOKING_END = BOOKING_START + timedelta(days=4)
OVERLAP_SEARCH_START = BOOKING_START + timedelta(days=1)
OVERLAP_SEARCH_END = BOOKING_START + timedelta(days=3)
NON_OVERLAP_SEARCH_START = datetime(2099, 8, 1, 10, 0, tzinfo=timezone.utc)
NON_OVERLAP_SEARCH_END = NON_OVERLAP_SEARCH_START + timedelta(days=3)


def _iso_z(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _api(
    method: str,
    path: str,
    *,
    token: str | None = None,
    params: dict | None = None,
    json: dict | None = None,
):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"{API_URL}{path}"
    if params:
        url = f"{url}?{urlencode(params)}"
    return requests.request(method, url, headers=headers, json=json, timeout=30)


def _error_message(resp: requests.Response) -> str:
    try:
        body = resp.json()
        return str(body.get("message") or body.get("description") or body)
    except Exception:
        return resp.text


def _listing_ids(resp: requests.Response) -> set[int]:
    listings = resp.json().get("listings") or []
    return {int(item["listingId"]) for item in listings}


def _register_user(prefix: str) -> str:
    email = f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"
    password = "SearchTest123!"
    resp = _api(
        "POST",
        "/api/auth/register",
        json={"email": email, "password": password, "fullName": prefix},
    )
    assert resp.status_code == 201, _error_message(resp)
    return resp.json()["token"]


def _create_instant_book_listing(host_token: str) -> int:
    resp = _api(
        "POST",
        "/api/listings",
        token=host_token,
        json={
            "title": f"Search Test {uuid.uuid4().hex[:8]}",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2021,
            "pricePerDay": 49.0,
            "lat": 45.5017,
            "lng": -73.5673,
            "cityZone": "montreal",
            "instantBook": True,
        },
    )
    assert resp.status_code == 201, _error_message(resp)
    listing_id = int(resp.json()["listing"]["listingId"])
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE vehicle_listing SET instant_book = TRUE WHERE listing_id = %s",
                (listing_id,),
            )
        conn.commit()
    return listing_id


def _prepare_listing_for_booking(host_token: str) -> tuple[int, bool]:
    """Return (listing_id, should_delete_listing_on_teardown)."""
    if INTEGRATION_LISTING_ID:
        listing_id = int(INTEGRATION_LISTING_ID)
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE vehicle_listing SET instant_book = TRUE WHERE listing_id = %s",
                    (listing_id,),
                )
            conn.commit()
        return listing_id, False
    return _create_instant_book_listing(host_token), True


def _delete_booking(booking_id: int) -> None:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM trip_event WHERE booking_id = %s", (booking_id,))
            cur.execute("DELETE FROM booking_instruction WHERE booking_id = %s", (booking_id,))
            cur.execute("DELETE FROM review WHERE booking_id = %s", (booking_id,))
            cur.execute("DELETE FROM booking WHERE booking_id = %s", (booking_id,))
        conn.commit()


def _delete_listing(listing_id: int) -> None:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM booking WHERE listing_id = %s",
                (listing_id,),
            )
            cur.execute("DELETE FROM listing_image WHERE listing_id = %s", (listing_id,))
            cur.execute("DELETE FROM vehicle_listing WHERE listing_id = %s", (listing_id,))
        conn.commit()


@pytest.fixture
def listing_with_confirmed_booking():
    host_token = _register_user("search-host")
    renter_token = _register_user("search-renter")
    listing_id, delete_listing = _prepare_listing_for_booking(host_token)
    resp = _api(
        "POST",
        "/api/bookings",
        token=renter_token,
        json={
            "listingId": listing_id,
            "startAt": _iso_z(BOOKING_START),
            "endAt": _iso_z(BOOKING_END),
        },
    )
    assert resp.status_code == 201, _error_message(resp)
    booking_id = int(resp.json()["booking"]["bookingId"])
    assert resp.json()["booking"]["status"] == "PENDING"
    pay_resp = _api("POST", f"/api/bookings/{booking_id}/payments", token=renter_token)
    assert pay_resp.status_code == 200, _error_message(pay_resp)
    yield listing_id, booking_id
    _delete_booking(booking_id)
    if delete_listing:
        _delete_listing(listing_id)


def test_search_no_dates_returns_listings():
    resp = _api("GET", "/api/listings")
    assert resp.status_code == 200, _error_message(resp)
    listings = resp.json().get("listings") or []
    assert listings, "Expected at least one active listing without date filters"


def test_search_hides_listing_during_confirmed_booking(listing_with_confirmed_booking):
    listing_id, _booking_id = listing_with_confirmed_booking
    resp = _api(
        "GET",
        "/api/listings",
        params={
            "start_at": _iso_z(OVERLAP_SEARCH_START),
            "end_at": _iso_z(OVERLAP_SEARCH_END),
        },
    )
    assert resp.status_code == 200, _error_message(resp)
    assert listing_id not in _listing_ids(resp)


def test_search_shows_listing_outside_booking_window(listing_with_confirmed_booking):
    listing_id, _booking_id = listing_with_confirmed_booking
    resp = _api(
        "GET",
        "/api/listings",
        params={
            "start_at": _iso_z(NON_OVERLAP_SEARCH_START),
            "end_at": _iso_z(NON_OVERLAP_SEARCH_END),
        },
    )
    assert resp.status_code == 200, _error_message(resp)
    assert listing_id in _listing_ids(resp)


def test_search_legacy_start_end_aliases_hide_overlapping(listing_with_confirmed_booking):
    listing_id, _booking_id = listing_with_confirmed_booking
    resp = _api(
        "GET",
        "/api/listings",
        params={
            "start": _iso_z(OVERLAP_SEARCH_START),
            "end": _iso_z(OVERLAP_SEARCH_END),
        },
    )
    assert resp.status_code == 200, _error_message(resp)
    assert listing_id not in _listing_ids(resp)


def test_search_validation_requires_both_dates():
    resp = _api(
        "GET",
        "/api/listings",
        params={"start_at": _iso_z(BOOKING_START)},
    )
    assert resp.status_code == 400, resp.text
    assert "start_at and end_at" in _error_message(resp)


def test_search_hides_listing_during_blocked_availability_window():
    host_token = _register_user("search-block-host")
    listing_id, delete_listing = _prepare_listing_for_booking(host_token)
    blocked_start = datetime(2099, 9, 10, 10, 0, tzinfo=timezone.utc)
    blocked_end = blocked_start + timedelta(days=5)
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO listing_availability (listing_id, start_at, end_at, status)
                VALUES (%s, %s, %s, 'BLOCKED')
                """,
                (listing_id, blocked_start, blocked_end),
            )
        conn.commit()
    try:
        resp = _api(
            "GET",
            "/api/listings",
            params={
                "start_at": _iso_z(blocked_start + timedelta(days=1)),
                "end_at": _iso_z(blocked_start + timedelta(days=3)),
            },
        )
        assert resp.status_code == 200, _error_message(resp)
        assert listing_id not in _listing_ids(resp)
    finally:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM listing_availability WHERE listing_id = %s",
                    (listing_id,),
                )
            conn.commit()
        if delete_listing:
            _delete_listing(listing_id)


def test_search_validation_end_must_be_after_start():
    resp = _api(
        "GET",
        "/api/listings",
        params={
            "start_at": _iso_z(BOOKING_END),
            "end_at": _iso_z(BOOKING_START),
        },
    )
    assert resp.status_code == 400, resp.text
    assert "end_at must be after start_at" in _error_message(resp)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
