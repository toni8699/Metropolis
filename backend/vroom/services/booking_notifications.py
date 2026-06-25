"""Post-commit booking side effects (email + payout). Never raise to callers."""

from __future__ import annotations

import logging

_logger = logging.getLogger("vroom.booking_notifications")


def notify_payment_completed(booking_id: int, next_status: str) -> None:
    from vroom.services import mail_service

    try:
        if next_status == "CONFIRMED":
            mail_service.send_booking_confirmed(booking_id)
        elif next_status == "PENDING_APPROVAL":
            mail_service.send_booking_pending_approval(booking_id)
    except Exception:
        _logger.exception("payment notification failed for booking %s", booking_id)


def notify_booking_approved(booking_id: int) -> None:
    from vroom.services import mail_service

    try:
        mail_service.send_booking_approved(booking_id)
    except Exception:
        _logger.exception("approval notification failed for booking %s", booking_id)


def notify_booking_rejected(booking_id: int) -> None:
    from vroom.services import mail_service

    try:
        mail_service.send_booking_rejected(booking_id)
    except Exception:
        _logger.exception("rejection notification failed for booking %s", booking_id)


def notify_booking_cancelled(booking_id: int) -> None:
    from vroom.services import mail_service

    try:
        mail_service.send_booking_cancelled(booking_id)
    except Exception:
        _logger.exception("cancellation notification failed for booking %s", booking_id)


def notify_trip_completed(booking_id: int) -> None:
    from vroom.services import mail_service, payout_service

    try:
        mail_service.send_trip_completed_review(booking_id)
    except Exception:
        _logger.exception("trip completed email failed for booking %s", booking_id)
    try:
        payout_service.transfer_for_booking(booking_id)
    except Exception:
        _logger.exception("payout transfer failed for booking %s", booking_id)
