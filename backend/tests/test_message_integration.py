"""Integration tests for booking messages (REST path).

Requires: running API + DATABASE_URL.
Socket.IO path is exercised by the smoke E2E tests.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests

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
        "/api/listings",
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
    pay = _api("POST", f"/api/bookings/{booking_id}/payments", token=renter_token)
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


def _post_message(token: str, booking_id: int, text: str):
    return _api(
        "POST",
        f"/api/bookings/{booking_id}/messages",
        token=token,
        json={"messageText": text},
    )


def _get_threads(token: str):
    return _api("GET", "/api/messages/threads", token=token)


def _thread_for_booking(body: dict, booking_id: int) -> dict | None:
    for thread in body.get("threads", []):
        if int(thread["bookingId"]) == booking_id:
            return thread
    return None


def test_unread_count_before_and_after_mark_read():
    host_token, _ = _register("msg-unread-host")
    renter_token, _ = _register("msg-unread-renter")
    listing_id = _create_listing(host_token)
    booking_id = _create_paid_booking(renter_token, listing_id)

    assert _post_message(renter_token, booking_id, "First unread").status_code in (200, 201)
    assert _post_message(renter_token, booking_id, "Second unread").status_code in (200, 201)

    threads_before = _get_threads(host_token)
    assert threads_before.status_code == 200, threads_before.text
    thread_before = _thread_for_booking(threads_before.json(), booking_id)
    assert thread_before is not None
    assert thread_before["unreadCount"] == 2

    load = _api("GET", f"/api/bookings/{booking_id}/messages", token=host_token)
    assert load.status_code == 200, load.text

    threads_after = _get_threads(host_token)
    assert threads_after.status_code == 200, threads_after.text
    thread_after = _thread_for_booking(threads_after.json(), booking_id)
    assert thread_after is not None
    assert thread_after["unreadCount"] == 0


def test_own_messages_are_not_counted_as_unread():
    host_token, _ = _register("msg-own-host")
    renter_token, _ = _register("msg-own-renter")
    listing_id = _create_listing(host_token)
    booking_id = _create_paid_booking(renter_token, listing_id)

    assert _post_message(renter_token, booking_id, "From renter").status_code in (200, 201)
    load = _api("GET", f"/api/bookings/{booking_id}/messages", token=renter_token)
    assert load.status_code == 200, load.text

    threads = _get_threads(renter_token)
    assert threads.status_code == 200, threads.text
    thread = _thread_for_booking(threads.json(), booking_id)
    assert thread is not None
    assert thread["unreadCount"] == 0


def test_new_message_increments_unread_after_read():
    host_token, _ = _register("msg-new-host")
    renter_token, _ = _register("msg-new-renter")
    listing_id = _create_listing(host_token)
    booking_id = _create_paid_booking(renter_token, listing_id)

    assert _post_message(renter_token, booking_id, "Initial").status_code in (200, 201)
    load = _api("GET", f"/api/bookings/{booking_id}/messages", token=host_token)
    assert load.status_code == 200, load.text

    assert _post_message(renter_token, booking_id, "Follow-up").status_code in (200, 201)

    threads = _get_threads(host_token)
    assert threads.status_code == 200, threads.text
    thread = _thread_for_booking(threads.json(), booking_id)
    assert thread is not None
    assert thread["unreadCount"] == 1
