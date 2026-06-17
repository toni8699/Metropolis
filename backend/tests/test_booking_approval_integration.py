"""
Integration tests for instant book vs host approval booking workflow.

Requires running API + DATABASE_URL (same as other integration tests).

Run:
  docker compose up -d backend
  cd backend && pytest tests/test_booking_approval_integration.py -v
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import psycopg2
import pytest
import requests

API_URL = os.environ.get("INTEGRATION_API_URL", "http://localhost:5000").rstrip("/")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DATABASE_URL must be set (project .env)",
)

BOOKING_START = datetime(2099, 7, 10, 10, 0, tzinfo=timezone.utc)
BOOKING_END = BOOKING_START + timedelta(days=3)


def _iso_z(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _api(method: str, path: str, *, token: str | None = None, json: dict | None = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, f"{API_URL}{path}", headers=headers, json=json, timeout=30)


def _patch_booking_status(booking_id: int, token: str, status: str):
    return _api(
        "PATCH",
        f"/api/bookings/{booking_id}",
        token=token,
        json={"status": status},
    )


def _error_message(resp: requests.Response) -> str:
    try:
        body = resp.json()
        return str(body.get("message") or body.get("description") or body)
    except Exception:
        return resp.text


def _register_user(prefix: str) -> tuple[str, int]:
    email = f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"
    password = "ApprovalTest123!"
    resp = _api(
        "POST",
        "/api/auth/register",
        json={"email": email, "password": password, "fullName": prefix},
    )
    assert resp.status_code == 201, _error_message(resp)
    token = resp.json()["token"]
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM app_user WHERE email = %s", (email,))
            user_id = int(cur.fetchone()[0])
    return token, user_id


def _create_owner_listing(host_token: str, *, instant_book: bool = True) -> int:
    title = f"Approval Test {uuid.uuid4().hex[:8]}"
    resp = _api(
        "POST",
        "/api/listings",
        token=host_token,
        json={
            "title": title,
            "make": "Honda",
            "model": "Civic",
            "year": 2022,
            "pricePerDay": 55.0,
            "lat": 45.5017,
            "lng": -73.5673,
            "cityZone": "montreal",
            "instantBook": instant_book,
        },
    )
    assert resp.status_code == 201, _error_message(resp)
    listing_id = int(resp.json()["listing"]["listingId"])
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE vehicle_listing SET instant_book = %s WHERE listing_id = %s",
                (instant_book, listing_id),
            )
        conn.commit()
    return listing_id


def _create_booking(renter_token: str, listing_id: int) -> dict:
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
    booking = resp.json()["booking"]
    assert booking["status"] == "PENDING"
    return booking


def _pay_for_booking(renter_token: str, booking_id: int) -> dict:
    resp = _api("POST", f"/api/bookings/{booking_id}/payments", token=renter_token)
    assert resp.status_code == 200, _error_message(resp)
    return resp.json()


def _create_paid_booking(renter_token: str, listing_id: int) -> dict:
    booking = _create_booking(renter_token, listing_id)
    _pay_for_booking(renter_token, int(booking["bookingId"]))
    detail = _api("GET", f"/api/bookings/{booking['bookingId']}", token=renter_token)
    assert detail.status_code == 200, _error_message(detail)
    return detail.json()["booking"]


def _ensure_fleet_listing(host_user_id: int) -> int:
    fleet_vin = f"CI{uuid.uuid4().hex[:13].upper()}"
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO area (areaid, areaname)
                VALUES (99001, 'CI Fleet Area')
                ON CONFLICT (areaid) DO NOTHING
                """
            )
            cur.execute(
                """
                INSERT INTO branch (branchid, areaid, city)
                VALUES (99001, 99001, 'Montreal')
                ON CONFLICT (branchid) DO NOTHING
                """
            )
            cur.execute(
                """
                INSERT INTO vehicle_asset (
                  vin,
                  vehicle_category,
                  owner_type,
                  owner_party_name,
                  asset_status,
                  make,
                  model,
                  branch_id,
                  fleet_status
                )
                VALUES (
                  %s,
                  'STANDARD'::vehicle_category,
                  'COMPANY'::vehicle_owner_type,
                  'Company Fleet',
                  'ACTIVE'::vehicle_asset_status,
                  'Fleet',
                  'Sedan',
                  99001,
                  'Available'
                )
                ON CONFLICT (vin) DO UPDATE
                SET
                  branch_id = EXCLUDED.branch_id,
                  fleet_status = EXCLUDED.fleet_status,
                  asset_status = EXCLUDED.asset_status
                """,
                (fleet_vin,),
            )
            cur.execute("SELECT vehicle_id FROM vehicle_asset WHERE vin = %s", (fleet_vin,))
            vehicle_id = int(cur.fetchone()[0])
            cur.execute(
                """
                INSERT INTO vehicle_listing (
                  owner_user_id, vehicle_id, source_type, fleet_vehicle_vin, title,
                  price_per_day, active, is_company_owned, instant_book
                )
                VALUES (%s, %s, 'FLEET', %s, %s, 60.00, TRUE, TRUE, TRUE)
                RETURNING listing_id
                """,
                (host_user_id, vehicle_id, fleet_vin, f"CI Fleet {uuid.uuid4().hex[:6]}"),
            )
            listing_id = int(cur.fetchone()[0])
            cur.execute(
                """
                INSERT INTO listing_location (listing_id, lat, lng, city_zone)
                VALUES (%s, 45.5020, -73.5680, 'montreal')
                ON CONFLICT (listing_id) DO NOTHING
                """,
                (listing_id,),
            )
        conn.commit()
    return listing_id


def _insert_confirmed_booking(
    listing_id: int,
    renter_user_id: int,
    *,
    start_at: datetime,
    end_at: datetime,
) -> int:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO booking (
                  listing_id, renter_user_id, start_at, end_at, status, price_snapshot_json
                )
                VALUES (%s, %s, %s, %s, 'CONFIRMED', '{"pricePerDay": 55}'::jsonb)
                RETURNING booking_id
                """,
                (listing_id, renter_user_id, start_at, end_at),
            )
            booking_id = int(cur.fetchone()[0])
        conn.commit()
    return booking_id


def test_fleet_listing_auto_confirms():
    host_token, host_user_id = _register_user("fleet-host")
    renter_token, _renter_id = _register_user("fleet-renter")
    listing_id = _ensure_fleet_listing(host_user_id)

    booking = _create_paid_booking(renter_token, listing_id)
    assert booking["status"] == "CONFIRMED"
    assert booking["sourceType"] == "FLEET"


def test_owner_instant_book_auto_confirms():
    host_token, _host_id = _register_user("instant-host")
    renter_token, _renter_id = _register_user("instant-renter")
    listing_id = _create_owner_listing(host_token, instant_book=True)

    booking = _create_paid_booking(renter_token, listing_id)
    assert booking["status"] == "CONFIRMED"
    assert booking["sourceType"] == "OWNER"


def test_owner_request_to_book_starts_pending_approval():
    host_token, _host_id = _register_user("pending-host")
    renter_token, _renter_id = _register_user("pending-renter")
    listing_id = _create_owner_listing(host_token, instant_book=False)

    booking = _create_paid_booking(renter_token, listing_id)
    assert booking["status"] == "PENDING_APPROVAL"
    assert booking["sourceType"] == "OWNER"


def test_host_approves_pending_booking():
    host_token, _host_user_id = _register_user("approve-host")
    renter_token, _renter_id = _register_user("approve-renter")
    listing_id = _create_owner_listing(host_token, instant_book=False)
    booking = _create_paid_booking(renter_token, listing_id)
    booking_id = int(booking["bookingId"])
    assert booking["status"] == "PENDING_APPROVAL"

    approve_resp = _patch_booking_status(booking_id, host_token, "CONFIRMED")
    assert approve_resp.status_code == 200, _error_message(approve_resp)
    assert approve_resp.json()["booking"]["status"] == "CONFIRMED"

    other_token, _ = _register_user("approve-intruder")
    forbidden = _patch_booking_status(booking_id, other_token, "CONFIRMED")
    assert forbidden.status_code == 403


def test_approve_fails_when_confirmed_conflict_exists():
    host_token, _host_user_id = _register_user("conflict-host")
    renter_a_token, renter_a_id = _register_user("conflict-renter-a")
    renter_b_token, renter_b_id = _register_user("conflict-renter-b")
    listing_id = _create_owner_listing(host_token, instant_book=False)

    pending = _create_paid_booking(renter_a_token, listing_id)
    booking_id = int(pending["bookingId"])

    _insert_confirmed_booking(
        listing_id,
        renter_b_id,
        start_at=BOOKING_START + timedelta(days=1),
        end_at=BOOKING_END - timedelta(days=1),
    )

    approve_resp = _patch_booking_status(booking_id, host_token, "CONFIRMED")
    assert approve_resp.status_code == 400, approve_resp.text
    assert "overlap" in _error_message(approve_resp).lower()

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status FROM booking WHERE booking_id = %s", (booking_id,))
            assert cur.fetchone()[0] == "PENDING_APPROVAL"


def test_renter_cancel_before_start():
    host_token, _ = _register_user("cancel-host")
    renter_token, _ = _register_user("cancel-renter")
    listing_id = _create_owner_listing(host_token, instant_book=True)
    booking = _create_paid_booking(renter_token, listing_id)
    booking_id = int(booking["bookingId"])
    assert booking["status"] == "CONFIRMED"

    cancel_resp = _patch_booking_status(booking_id, renter_token, "CANCELLED")
    assert cancel_resp.status_code == 200, _error_message(cancel_resp)
    assert cancel_resp.json()["booking"]["status"] == "CANCELLED"

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT event_type FROM trip_event
                WHERE booking_id = %s
                ORDER BY event_id DESC
                LIMIT 1
                """,
                (booking_id,),
            )
            assert cur.fetchone()[0] == "BOOKING_CANCELLED"


def test_duplicate_booking_same_dates_rejected():
    host_token, _ = _register_user("dup-host")
    renter_a_token, _ = _register_user("dup-renter-a")
    renter_b_token, _ = _register_user("dup-renter-b")
    listing_id = _create_owner_listing(host_token, instant_book=True)

    first = _create_paid_booking(renter_a_token, listing_id)
    assert first["status"] == "CONFIRMED"

    second = _api(
        "POST",
        "/api/bookings",
        token=renter_b_token,
        json={
            "listingId": listing_id,
            "startAt": _iso_z(BOOKING_START),
            "endAt": _iso_z(BOOKING_END),
        },
    )
    assert second.status_code == 400, second.text
    assert "unavailable" in _error_message(second).lower()


def test_host_rejects_pending_booking():
    host_token, _host_id = _register_user("reject-host")
    renter_token, _renter_id = _register_user("reject-renter")
    listing_id = _create_owner_listing(host_token, instant_book=False)
    booking = _create_paid_booking(renter_token, listing_id)
    booking_id = int(booking["bookingId"])

    reject_resp = _patch_booking_status(booking_id, host_token, "CANCELLED")
    assert reject_resp.status_code == 200, _error_message(reject_resp)
    assert reject_resp.json()["booking"]["status"] == "CANCELLED"
