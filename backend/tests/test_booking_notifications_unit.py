"""Booking notification hook tests."""

from __future__ import annotations

from unittest.mock import patch

from vroom.services.booking_notifications import (
    notify_payment_completed,
    notify_trip_completed,
)


def test_notify_payment_completed_confirmed():
    with patch("vroom.services.mail_service.send_booking_confirmed") as send:
        notify_payment_completed(10, "CONFIRMED")
    send.assert_called_once_with(10)


def test_notify_payment_completed_pending_approval():
    with patch("vroom.services.mail_service.send_booking_pending_approval") as send:
        notify_payment_completed(11, "PENDING_APPROVAL")
    send.assert_called_once_with(11)


def test_notify_trip_completed_calls_email_and_payout():
    with (
        patch("vroom.services.mail_service.send_trip_completed_review") as review,
        patch(
            "vroom.services.payout_service.payout_service.transfer_for_booking",
        ) as payout,
    ):
        notify_trip_completed(12)
    review.assert_called_once_with(12)
    payout.assert_called_once_with(12)
