"""Integration tests for booking messages (REST path).

Requires: running API + DATABASE_URL.
Socket.IO path is exercised by the smoke E2E tests.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
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

MSG_START = datetime(2099, 9, 1, 10, 0, tzinfo=timezone.utc)
MSG_END = MSG_START + timedelta(days=2)


def _iso_z(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _api(method: str, path: str, *, json: dict | None = None, token: str | None = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, f"{API_URL}{path}", headers=headers, json=json, timeout=15)


def _register(prefix: str) -> tuple[str, int]:
    email = f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"
    resp = _api(
        "POST",
        "/api/auth/register",
        json={"email": email, "password": "MsgTest123!", "fullName": prefix},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    return body["token"], int(body["user"]["userId"])


def _create_listing(host_token: str) -> int:
    resp = _api(
        "POST",
        "/api/owner/listings",
        token=host_token,
        json={
            "title": f"Msg test car {uuid.uuid4().hex[:6]}",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2021,
            "pricePerDay": 45.0,
            "lat": 45.5017,
            "lng": -73.5673,
            "cityZone": "montreal",
            "instantBook": True,
        },
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["listing"]["listingId"])


def _create_paid_booking(renter_token: str, listing_id: int) -> int:
    resp = _api(
        "POST",
        "/api/bookings",
        token=renter_token,
        json={"listingId": listing_id, "startAt": _iso_z(MSG_START), "endAt": _iso_z(MSG_END)},
    )
    assert resp.status_code == 201, resp.text
    booking_id = int(resp.json()["booking"]["bookingId"])
    pay = _api("POST", f"/api/bookings/{booking_id}/payment-intent", token=renter_token)
    assert pay.ok, pay.text
    return booking_id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_renter_can_post_and_retrieve_message():
    host_token, _ = _register("msg-host")
    renter_token, _ = _register("msg-renter")
    listing_id = _create_listing(host_token)
    booking_id = _create_paid_booking(renter_token, listing_id)

    post = _api(
        "POST",
        f"/api/bookings/{booking_id}/messages",
        token=renter_token,
        json={"messageText": "Hello from renter!"},
    )
    assert post.status_code in (200, 201), post.text

    get = _api("GET", f"/api/bookings/{booking_id}/messages", token=renter_token)
    assert get.status_code == 200, get.text
    messages = get.json().get("messages", [])
    texts = [m["messageText"] for m in messages]
    assert "Hello from renter!" in texts


def test_host_can_post_message_to_own_booking():
    host_token, _ = _register("msg-host2")
    renter_token, _ = _register("msg-renter2")
    listing_id = _create_listing(host_token)
    booking_id = _create_paid_booking(renter_token, listing_id)

    post = _api(
        "POST",
        f"/api/bookings/{booking_id}/messages",
        token=host_token,
        json={"messageText": "Hello from host!"},
    )
    assert post.status_code in (200, 201), post.text


def test_stranger_cannot_read_messages():
    host_token, _ = _register("msg-host3")
    renter_token, _ = _register("msg-renter3")
    stranger_token, _ = _register("msg-stranger3")
    listing_id = _create_listing(host_token)
    booking_id = _create_paid_booking(renter_token, listing_id)

    resp = _api("GET", f"/api/bookings/{booking_id}/messages", token=stranger_token)
    assert resp.status_code in (403, 401), resp.text


def test_unauthenticated_cannot_read_messages():
    host_token, _ = _register("msg-host4")
    renter_token, _ = _register("msg-renter4")
    listing_id = _create_listing(host_token)
    booking_id = _create_paid_booking(renter_token, listing_id)

    resp = _api("GET", f"/api/bookings/{booking_id}/messages")
    assert resp.status_code == 401, resp.text
