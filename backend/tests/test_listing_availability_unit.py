"""Listing availability status validation."""

from __future__ import annotations

from metropolis.services.listing_service import ListingService


def test_add_availability_rejects_invalid_status():
    service = ListingService()
    result = service.add_availability(
        {"userId": 1, "role": "HOST"},
        999999,
        {"startAt": "2026-07-01T10:00:00Z", "endAt": "2026-07-05T10:00:00Z", "status": "NOPE"},
    )
    assert result["status"] == "bad_request"
