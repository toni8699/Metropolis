"""
Integration tests for the reviews API.

Requires a running backend and DATABASE_URL (same Neon DB as the API).

Run:
  docker compose up
  export $(grep -v '^#' .env | xargs)
  cd backend && uv sync --extra dev
  pytest tests/test_reviews_integration.py -v

Env (optional):
  INTEGRATION_API_URL  default http://localhost:5000
  INTEGRATION_EMAIL / INTEGRATION_PASSWORD  login; registers if login fails
  INTEGRATION_LISTING_ID  force a listing id
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

import psycopg2
import pytest
import requests
from conftest import api_request, integration_env

API_URL, DATABASE_URL = integration_env()
INTEGRATION_EMAIL = os.environ.get("INTEGRATION_EMAIL", "").strip()
INTEGRATION_PASSWORD = os.environ.get("INTEGRATION_PASSWORD", "").strip()
INTEGRATION_LISTING_ID = os.environ.get("INTEGRATION_LISTING_ID", "").strip()

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DATABASE_URL must be set (project .env)",
)


def _error_message(resp: requests.Response) -> str:
    try:
        body = resp.json()
        return str(body.get("message") or body.get("description") or body)
    except Exception:
        return resp.text


def _login_or_register() -> str:
    if INTEGRATION_EMAIL and INTEGRATION_PASSWORD:
        resp = api_request(
            API_URL,
            "POST",
            "/api/auth/login",
            json={"email": INTEGRATION_EMAIL, "password": INTEGRATION_PASSWORD},
        )
        if resp.status_code == 200 and resp.json().get("token"):
            return resp.json()["token"]

    email = f"review-int-{uuid.uuid4().hex[:10]}@example.com"
    password = "ReviewTest123!"
    from auth_test_helpers import register_and_login_http

    return register_and_login_http(
        API_URL,
        DATABASE_URL,
        email=email,
        password=password,
        full_name="Review Integration",
    )


def _pick_listing_id() -> int:
    if INTEGRATION_LISTING_ID:
        return int(INTEGRATION_LISTING_ID)
    resp = api_request(API_URL, "GET", "/api/listings")
    assert resp.status_code == 200, _error_message(resp)
    listings = resp.json().get("listings") or []
    assert listings, "No listings in database — need at least one active listing"
    return int(listings[0]["listingId"])


def _get_listing_stats(listing_id: int) -> tuple[int | None, int]:
    resp = api_request(API_URL, "GET", f"/api/listings/{listing_id}")
    assert resp.status_code == 200, _error_message(resp)
    listing = resp.json()["listing"]
    avg = listing.get("averageRating")
    count = int(listing.get("reviewCount") or 0)
    return (float(avg) if avg is not None else None, count)


def _expected_average(old_avg: float | None, old_count: int, new_rating: int) -> float:
    if old_count == 0:
        return float(new_rating)
    total = (old_avg or 0.0) * old_count + new_rating
    return float(
        Decimal(str(total / (old_count + 1))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )


def _set_booking_completed(booking_id: int) -> None:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE booking SET status = 'COMPLETED', updated_at = NOW() WHERE booking_id = %s",
                (booking_id,),
            )
            assert cur.rowcount == 1, f"booking {booking_id} not updated"
        conn.commit()


def _set_booking_window(booking_id: int, *, start_at: datetime, end_at: datetime) -> None:
    """Update trip window; satisfies DB check end_at > start_at."""
    assert end_at > start_at, "test setup: end_at must be after start_at"
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE booking
                SET start_at = %s, end_at = %s, updated_at = NOW()
                WHERE booking_id = %s
                """,
                (start_at, end_at, booking_id),
            )
            assert cur.rowcount == 1, f"booking {booking_id} not updated"
        conn.commit()


def test_reviews_integration_flow():
    token = _login_or_register()
    listing_id = _pick_listing_id()

    start = datetime(2099, 6, 1, 10, 0, tzinfo=timezone.utc)
    end = start + timedelta(days=3)
    booking_resp = api_request(
        API_URL,
        "POST",
        "/api/bookings",
        token=token,
        json={
            "listingId": listing_id,
            "startAt": start.isoformat().replace("+00:00", "Z"),
            "endAt": end.isoformat().replace("+00:00", "Z"),
        },
    )
    assert booking_resp.status_code == 201, _error_message(booking_resp)
    booking_id = int(booking_resp.json()["booking"]["bookingId"])

    review_payload = {
        "targetType": "LISTING",
        "rating": 5,
        "cleanliness": 5,
        "accuracy": 4,
        "communication": 5,
        "comment": "integration test review",
    }

    early_resp = api_request(
        API_URL,
        "POST",
        f"/api/bookings/{booking_id}/reviews",
        token=token,
        json=review_payload,
    )
    assert early_resp.status_code == 400, early_resp.text
    assert "COMPLETED" in _error_message(early_resp)

    baseline_avg, baseline_count = _get_listing_stats(listing_id)

    _set_booking_completed(booking_id)

    now = datetime.now(timezone.utc)
    _set_booking_window(
        booking_id,
        start_at=now - timedelta(days=34),
        end_at=now - timedelta(days=31),
    )

    expired_resp = api_request(
        API_URL,
        "POST",
        f"/api/bookings/{booking_id}/reviews",
        token=token,
        json=review_payload,
    )
    assert expired_resp.status_code == 400, expired_resp.text
    assert "30-day review window" in _error_message(expired_resp)

    now = datetime.now(timezone.utc)
    _set_booking_window(
        booking_id,
        start_at=now - timedelta(days=3),
        end_at=now,
    )

    new_rating = 4
    review_payload["rating"] = new_rating
    ok_resp = api_request(
        API_URL,
        "POST",
        f"/api/bookings/{booking_id}/reviews",
        token=token,
        json=review_payload,
    )
    assert ok_resp.status_code == 201, _error_message(ok_resp)
    body = ok_resp.json()
    assert body.get("status") == "success"
    assert body["review"]["targetType"] == "LISTING"
    assert body["review"]["rating"] == new_rating
    assert body["review"]["cleanliness"] == review_payload["cleanliness"]
    assert body["review"]["accuracy"] == review_payload["accuracy"]
    assert body["review"]["communication"] == review_payload["communication"]

    dup_resp = api_request(
        API_URL,
        "POST",
        f"/api/bookings/{booking_id}/reviews",
        token=token,
        json=review_payload,
    )
    assert dup_resp.status_code == 400, dup_resp.text
    assert "already submitted" in _error_message(dup_resp).lower()

    after_avg, after_count = _get_listing_stats(listing_id)
    assert after_count == baseline_count + 1
    assert after_avg == pytest.approx(_expected_average(baseline_avg, baseline_count, new_rating))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
