"""Booking cancel eligibility unit tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from vroom.services.booking_support import host_can_cancel, renter_can_cancel

_NOW = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
_FUTURE = _NOW + timedelta(days=2)
_PAST = _NOW - timedelta(days=1)


def test_renter_can_cancel_confirmed_before_start():
    assert renter_can_cancel("CONFIRMED", _FUTURE, now=_NOW) is True


def test_renter_can_cancel_pending_unpaid():
    assert renter_can_cancel("PENDING", _FUTURE, now=_NOW) is True


def test_renter_cannot_cancel_after_start():
    assert renter_can_cancel("CONFIRMED", _PAST, now=_NOW) is False


def test_host_can_cancel_confirmed_before_start():
    assert host_can_cancel("CONFIRMED", _FUTURE, now=_NOW) is True


def test_renter_can_cancel_pending_after_start():
    assert renter_can_cancel("PENDING", _PAST, now=_NOW) is True


def test_host_can_cancel_unpaid_pending_after_start():
    assert host_can_cancel("PENDING", _PAST, now=_NOW) is True


def test_host_cannot_cancel_pending_approval():
    assert host_can_cancel("PENDING_APPROVAL", _FUTURE, now=_NOW) is False
