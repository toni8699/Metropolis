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
from urllib.parse import urlencode

import psycopg2
import pytest
import requests

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
    from auth_test_helpers import register_and_login_http

    email = f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"
    password = "SearchTest123!"
    return register_and_login_http(
        API_URL,
        DATABASE_URL,
        email=email,
        password=password,
        full_name=prefix,
    )


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
            cur.execute("DELETE FROM review WHERE booking_id = %s", (booking_id,))
            cur.execute("DELETE FROM booking WHERE booking_id = %s", (booking_id,))
        conn.commit()


def _delete_listing(listing_id: int) -> None:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT vehicle_id FROM vehicle_listing WHERE listing_id = %s",
                (listing_id,),
            )
            row = cur.fetchone()
            vehicle_id = row[0] if row else None
            cur.execute(
                "DELETE FROM booking WHERE listing_id = %s",
                (listing_id,),
            )
            cur.execute("DELETE FROM listing_image WHERE listing_id = %s", (listing_id,))
            cur.execute("DELETE FROM listing_location WHERE listing_id = %s", (listing_id,))
            cur.execute("DELETE FROM listing_availability WHERE listing_id = %s", (listing_id,))
            cur.execute("DELETE FROM vehicle_listing WHERE listing_id = %s", (listing_id,))
            if vehicle_id:
                cur.execute(
                    "DELETE FROM vehicle_vin_metadata WHERE vehicle_id = %s",
                    (vehicle_id,),
                )
                cur.execute("DELETE FROM vehicle_asset WHERE vehicle_id = %s", (vehicle_id,))
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
    pay_body = pay_resp.json()
    assert (
        pay_body.get("mock") is True
    ), "integration tests expect mock payment (unset STRIPE_SECRET_KEY in CI)"
    detail_resp = _api("GET", f"/api/bookings/{booking_id}", token=renter_token)
    assert detail_resp.status_code == 200, _error_message(detail_resp)
    booking_status = detail_resp.json()["booking"]["status"]
    assert (
        booking_status == "CONFIRMED"
    ), f"expected instant-book payment to confirm booking, got {booking_status}"
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


def _update_listing_asset_specs(
    listing_id: int,
    *,
    transmission: str | None = None,
    fuel_type: str | None = None,
    seats: int | None = None,
    body_type_id: int | None = None,
    price_per_day: float | None = None,
) -> None:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT vehicle_id FROM vehicle_listing WHERE listing_id = %s",
                (listing_id,),
            )
            row = cur.fetchone()
            assert row and row[0], f"listing {listing_id} missing vehicle_id"
            vehicle_id = row[0]
            if transmission is not None:
                cur.execute(
                    """
                    UPDATE vehicle_asset
                    SET transmission = %s::transmission_type
                    WHERE vehicle_id = %s
                    """,
                    (transmission, vehicle_id),
                )
            if fuel_type is not None:
                cur.execute(
                    "UPDATE vehicle_asset SET fuel_type = %s::fuel_type_enum WHERE vehicle_id = %s",
                    (fuel_type, vehicle_id),
                )
            if seats is not None:
                cur.execute(
                    "UPDATE vehicle_asset SET seats = %s WHERE vehicle_id = %s",
                    (seats, vehicle_id),
                )
            if body_type_id is not None:
                cur.execute(
                    "UPDATE vehicle_asset SET body_type_id = %s WHERE vehicle_id = %s",
                    (body_type_id, vehicle_id),
                )
            if price_per_day is not None:
                cur.execute(
                    "UPDATE vehicle_listing SET price_per_day = %s WHERE listing_id = %s",
                    (price_per_day, listing_id),
                )
        conn.commit()


def _set_listing_features(listing_id: int, feature_ids: list[int]) -> None:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM listing_feature WHERE listing_id = %s", (listing_id,))
            for feature_id in feature_ids:
                cur.execute(
                    """
                    INSERT INTO listing_feature (listing_id, feature_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (listing_id, feature_id),
                )
        conn.commit()


def _first_two_feature_ids() -> tuple[int, int]:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT feature_id
                FROM ref_feature
                WHERE is_active = TRUE
                ORDER BY feature_id
                LIMIT 2
                """
            )
            rows = cur.fetchall()
    assert len(rows) == 2, "Need at least two active features for intersection tests"
    return int(rows[0][0]), int(rows[1][0])


def test_search_filters_price_range():
    host_token = _register_user("search-price-host")
    listing_id, delete_listing = _prepare_listing_for_booking(host_token)
    _update_listing_asset_specs(listing_id, price_per_day=75.0)
    try:
        include = _api("GET", "/api/listings", params={"minPrice": 70, "maxPrice": 80})
        exclude = _api("GET", "/api/listings", params={"minPrice": 80, "maxPrice": 90})
        assert include.status_code == 200, _error_message(include)
        assert exclude.status_code == 200, _error_message(exclude)
        assert listing_id in _listing_ids(include)
        assert listing_id not in _listing_ids(exclude)
    finally:
        if delete_listing:
            _delete_listing(listing_id)


def test_search_filters_transmission_and_fuel():
    host_token = _register_user("search-spec-host")
    listing_id, delete_listing = _prepare_listing_for_booking(host_token)
    _update_listing_asset_specs(
        listing_id,
        transmission="MANUAL",
        fuel_type="Hybrid",
        seats=5,
    )
    try:
        match = _api(
            "GET",
            "/api/listings",
            params={"transmission": "MANUAL", "fuelTypes": "Hybrid"},
        )
        miss = _api(
            "GET",
            "/api/listings",
            params={"transmission": "AUTOMATIC", "fuelTypes": "Hybrid"},
        )
        assert match.status_code == 200, _error_message(match)
        assert miss.status_code == 200, _error_message(miss)
        assert listing_id in _listing_ids(match)
        assert listing_id not in _listing_ids(miss)
    finally:
        if delete_listing:
            _delete_listing(listing_id)


def test_search_filters_seats_seven_plus():
    host_token = _register_user("search-seats-host")
    listing_id, delete_listing = _prepare_listing_for_booking(host_token)
    _update_listing_asset_specs(listing_id, seats=8)
    try:
        match = _api("GET", "/api/listings", params={"seatsGte": 7})
        miss = _api("GET", "/api/listings", params={"seats": "2,4,5"})
        assert match.status_code == 200, _error_message(match)
        assert miss.status_code == 200, _error_message(miss)
        assert listing_id in _listing_ids(match)
        assert listing_id not in _listing_ids(miss)
    finally:
        if delete_listing:
            _delete_listing(listing_id)


def test_search_filters_feature_intersection():
    host_token = _register_user("search-feature-host")
    listing_with_both, delete_both = _prepare_listing_for_booking(host_token)
    listing_with_one, delete_one = _prepare_listing_for_booking(host_token)
    feature_a, feature_b = _first_two_feature_ids()
    _set_listing_features(listing_with_both, [feature_a, feature_b])
    _set_listing_features(listing_with_one, [feature_a])
    try:
        both = _api("GET", "/api/listings", params={"featureIds": f"{feature_a},{feature_b}"})
        one = _api("GET", "/api/listings", params={"featureIds": str(feature_a)})
        assert both.status_code == 200, _error_message(both)
        assert one.status_code == 200, _error_message(one)
        both_ids = _listing_ids(both)
        one_ids = _listing_ids(one)
        assert listing_with_both in both_ids
        assert listing_with_one not in both_ids
        assert listing_with_both in one_ids
        assert listing_with_one in one_ids
    finally:
        if delete_both:
            _delete_listing(listing_with_both)
        if delete_one:
            _delete_listing(listing_with_one)


def test_search_count_matches_total_count_and_pagination():
    host_token = _register_user("search-count-host")
    listing_id, delete_listing = _prepare_listing_for_booking(host_token)
    _update_listing_asset_specs(listing_id, price_per_day=88.0)
    try:
        count_resp = _api("GET", "/api/listings/count", params={"minPrice": 80, "maxPrice": 95})
        list_resp = _api(
            "GET",
            "/api/listings",
            params={"minPrice": 80, "maxPrice": 95, "limit": 1, "offset": 0},
        )
        assert count_resp.status_code == 200, _error_message(count_resp)
        assert list_resp.status_code == 200, _error_message(list_resp)
        count_body = count_resp.json()
        list_body = list_resp.json()
        assert count_body["totalCount"] == list_body["totalCount"]
        assert list_body["limit"] == 1
        assert list_body["offset"] == 0
        assert len(list_body.get("listings") or []) <= 1
        assert listing_id in _listing_ids(list_resp)
    finally:
        if delete_listing:
            _delete_listing(listing_id)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
