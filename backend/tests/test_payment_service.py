"""Payment service unit tests (dev mock path + status resolution)."""

from __future__ import annotations

from metropolis.services.booking_support import resolve_post_payment_status


def test_post_payment_status_fleet_and_instant_confirm():
    assert resolve_post_payment_status("FLEET", True) == "CONFIRMED"
    assert resolve_post_payment_status("OWNER", True) == "CONFIRMED"


def test_post_payment_status_non_instant_owner_pending_approval():
    assert resolve_post_payment_status("OWNER", False) == "PENDING_APPROVAL"
