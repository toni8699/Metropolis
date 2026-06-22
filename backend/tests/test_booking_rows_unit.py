"""Booking row mapping unit tests."""

from __future__ import annotations

from datetime import datetime, timezone

from metropolis.services.booking_rows import to_booking_row


def test_to_booking_row_reads_listing_title_from_booking_select_sql():
    row = {
        "booking_id": 1,
        "listing_id": 10,
        "listing_title": "Host Civic",
        "source_type": "OWNER",
        "owner_user_id": 5,
        "renter_user_id": 9,
        "renter_email": "renter@test.com",
        "city_zone": "montreal",
        "start_at": datetime(2026, 6, 1, tzinfo=timezone.utc),
        "end_at": datetime(2026, 6, 3, tzinfo=timezone.utc),
        "status": "CONFIRMED",
        "price_snapshot_json": {},
        "created_at": datetime(2026, 5, 20, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 5, 20, tzinfo=timezone.utc),
    }
    payload = to_booking_row(row)
    assert payload["listingTitle"] == "Host Civic"
