"""Payout service unit tests (mock Stripe + DB)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from metropolis.services.payout_service import PayoutService


def _mock_conn(fetchone=None, fetchall=None):
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchone.side_effect = fetchone or [None]
    cur.fetchall.return_value = fetchall or []
    conn.cursor.return_value.__enter__.return_value = cur
    conn.__enter__.return_value = conn
    return conn, cur


SNAPSHOT = {"subtotal": 100, "cleaningFee": 50, "dayCount": 1, "pricePerDay": 100}


def test_transfer_skipped_for_fleet_listing():
    svc = PayoutService()
    row = {
        "booking_id": 1,
        "status": "COMPLETED",
        "source_type": "FLEET",
        "price_snapshot_json": SNAPSHOT,
        "start_at": MagicMock(),
        "end_at": MagicMock(),
        "owner_user_id": 2,
        "payment_status": "succeeded",
    }
    conn, _cur = _mock_conn(fetchone=[row, None])
    with patch("metropolis.services.payout_service.get_connection", return_value=conn):
        result = svc.transfer_for_booking(1)
    assert result["status"] == "skipped"


def test_gross_payout_amount_from_snapshot():
    from metropolis.services.booking_rows import build_host_earnings, build_price_breakdown

    row = {
        "price_snapshot_json": {
            "pricePerDay": 100,
            "dayCount": 2,
            "subtotal": 200,
            "cleaningFee": 50,
            "serviceFee": 20,
            "total": 270,
            "currency": "CAD",
        },
        "start_at": MagicMock(),
        "end_at": MagicMock(),
    }
    pricing = build_price_breakdown(row)
    earnings = build_host_earnings(pricing)
    assert earnings["grossPayout"] == 250.0


def test_transfer_idempotent_when_already_succeeded():
    svc = PayoutService()
    payout_row = {"payout_id": 1, "status": "succeeded", "stripe_transfer_id": "tr_123"}
    booking_row = {
        "booking_id": 5,
        "status": "COMPLETED",
        "source_type": "OWNER",
        "price_snapshot_json": SNAPSHOT,
        "start_at": MagicMock(),
        "end_at": MagicMock(),
        "owner_user_id": 2,
        "payment_status": "succeeded",
    }
    conn, _cur = _mock_conn(fetchone=[booking_row, payout_row])
    with patch("metropolis.services.payout_service.get_connection", return_value=conn):
        result = svc.transfer_for_booking(5)
    assert result["status"] == "success"
    assert result["payoutStatus"] == "succeeded"


def test_connect_disabled_marks_skipped():
    svc = PayoutService()
    booking_row = {
        "booking_id": 3,
        "status": "COMPLETED",
        "source_type": "OWNER",
        "price_snapshot_json": SNAPSHOT,
        "start_at": MagicMock(),
        "end_at": MagicMock(),
        "owner_user_id": 2,
        "payment_status": "succeeded",
    }
    conn, _cur = _mock_conn(fetchone=[booking_row, None])
    with (
        patch("metropolis.services.payout_service.get_connection", return_value=conn),
        patch("metropolis.services.payout_service._connect_enabled", return_value=False),
    ):
        result = svc.transfer_for_booking(3)
    assert result["payoutStatus"] == "skipped"
