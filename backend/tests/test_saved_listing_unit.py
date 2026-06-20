from __future__ import annotations

from metropolis.services.saved_listing_service import SavedListingService


def test_saved_listing_toggle_payload_shape() -> None:
    service = SavedListingService()
    assert hasattr(service, "list_saved")
    assert hasattr(service, "save_listing")
    assert hasattr(service, "unsave_listing")

    ok = {
        "status": "success",
        "listingId": 42,
        "saved": True,
        "savedListingIds": [42, 7],
    }
    assert ok["savedListingIds"] == [42, 7]
    assert ok["saved"] is True
