"""Transactional email via Resend."""

from __future__ import annotations

import logging
from datetime import datetime

from psycopg2.extras import RealDictCursor

from vroom.core.config import settings
from vroom.core.db import get_connection
from vroom.services.booking_rows import build_host_earnings, build_price_breakdown

_logger = logging.getLogger("vroom.mail")


def _frontend_base() -> str:
    return settings.frontend_base_url.rstrip("/")


def _format_trip_window(start_at: datetime, end_at: datetime) -> str:
    start = start_at.strftime("%b %d, %Y %H:%M UTC")
    end = end_at.strftime("%b %d, %Y %H:%M UTC")
    return f"{start} – {end}"


def _send_html(to: str, subject: str, html: str) -> bool:
    """Send HTML email. Returns True if sent. No-op when Resend not configured."""
    api_key = settings.resend_api_key
    mail_from = settings.mail_from
    if not api_key or not mail_from:
        _logger.warning("Skipping email to %s (Resend not configured): %s", to, subject)
        return False
    try:
        import resend

        resend.api_key = api_key
        response = resend.Emails.send(
            {
                "from": mail_from,
                "to": [to],
                "subject": subject,
                "html": html,
            }
        )
        _logger.info("Email queued for %s (resend id=%s): %s", to, response, subject)
        return True
    except Exception:
        _logger.exception(
            "Failed to send email to %s (from=%s): %s",
            to,
            mail_from,
            subject,
        )
        return False


def booking_email_context(booking_id: int) -> dict | None:
    """Fetch renter/host/listing fields for transactional email templates."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                  b.booking_id,
                  b.status,
                  b.start_at,
                  b.end_at,
                  b.price_snapshot_json,
                  l.title AS listing_title,
                  l.source_type,
                  l.owner_user_id,
                  renter.email AS renter_email,
                  renter.full_name AS renter_name,
                  host.email AS host_email,
                  host.full_name AS host_name
                FROM booking b
                JOIN vehicle_listing l ON l.listing_id = b.listing_id
                JOIN app_user renter ON renter.user_id = b.renter_user_id
                LEFT JOIN app_user host ON host.user_id = l.owner_user_id
                WHERE b.booking_id = %s
                """,
                (booking_id,),
            )
            row = cur.fetchone()
    if not row:
        return None
    base = _frontend_base()
    pricing = build_price_breakdown(row)
    return {
        "bookingId": row["booking_id"],
        "status": row["status"],
        "listingTitle": row["listing_title"],
        "sourceType": row["source_type"],
        "ownerUserId": row["owner_user_id"],
        "renterEmail": row["renter_email"],
        "renterName": row.get("renter_name") or row["renter_email"],
        "hostEmail": row.get("host_email"),
        "hostName": row.get("host_name") or row.get("host_email") or "Host",
        "tripWindow": _format_trip_window(row["start_at"], row["end_at"]),
        "total": pricing.get("total"),
        "currency": pricing.get("currency") or "CAD",
        "bookingUrl": f"{base}/app/bookings/{booking_id}",
        "tripsUrl": f"{base}/app/trips",
        "hostDashboardUrl": f"{base}/host/dashboard",
    }


def send_verification_email(email: str, token: str) -> None:
    """Send HTML verification link. No-op when Resend is not configured."""
    verify_url = f"{_frontend_base()}/verify-email?token={token}"
    html = f"""\
<p>Welcome to VROOM.</p>
<p>Confirm your email to finish signing up:</p>
<p><a href="{verify_url}">Verify email</a></p>
<p>Or copy this link: {verify_url}</p>
"""
    _send_html(email, "Verify your VROOM email", html)


def send_booking_confirmed(booking_id: int) -> None:
    ctx = booking_email_context(booking_id)
    if not ctx:
        return
    renter_html = f"""\
<p>Hi {ctx["renterName"]},</p>
<p>Your booking for <strong>{ctx["listingTitle"]}</strong> is confirmed.</p>
<p>Trip: {ctx["tripWindow"]}</p>
<p>Total paid: {ctx["total"]} {ctx["currency"]}</p>
<p><a href="{ctx["bookingUrl"]}">View booking</a></p>
"""
    _send_html(ctx["renterEmail"], f"Booking confirmed — {ctx['listingTitle']}", renter_html)
    if ctx.get("hostEmail"):
        host_html = f"""\
<p>Hi {ctx["hostName"]},</p>
<p>You have a new confirmed booking for <strong>{ctx["listingTitle"]}</strong>.</p>
<p>Trip: {ctx["tripWindow"]}</p>
<p>Renter: {ctx["renterName"]}</p>
<p><a href="{ctx["hostDashboardUrl"]}">Open host dashboard</a></p>
"""
        _send_html(ctx["hostEmail"], f"New booking — {ctx['listingTitle']}", host_html)


def send_booking_pending_approval(booking_id: int) -> None:
    ctx = booking_email_context(booking_id)
    if not ctx:
        return
    renter_html = f"""\
<p>Hi {ctx["renterName"]},</p>
<p>Payment received for <strong>{ctx["listingTitle"]}</strong>. Waiting for host approval.</p>
<p>Trip: {ctx["tripWindow"]}</p>
<p>Total: {ctx["total"]} {ctx["currency"]}</p>
<p><a href="{ctx["tripsUrl"]}">View your trips</a></p>
"""
    _send_html(
        ctx["renterEmail"],
        f"Booking pending approval — {ctx['listingTitle']}",
        renter_html,
    )
    if ctx.get("hostEmail"):
        host_html = f"""\
<p>Hi {ctx["hostName"]},</p>
<p>A guest paid for <strong>{ctx["listingTitle"]}</strong> and needs your approval.</p>
<p>Trip: {ctx["tripWindow"]}</p>
<p>Renter: {ctx["renterName"]}</p>
<p><a href="{ctx["hostDashboardUrl"]}">Approve or reject in dashboard</a></p>
"""
        _send_html(
            ctx["hostEmail"],
            f"Action required — approve booking for {ctx['listingTitle']}",
            host_html,
        )


def send_booking_approved(booking_id: int) -> None:
    ctx = booking_email_context(booking_id)
    if not ctx:
        return
    html = f"""\
<p>Hi {ctx["renterName"]},</p>
<p>Good news — your booking for <strong>{ctx["listingTitle"]}</strong> was approved.</p>
<p>Trip: {ctx["tripWindow"]}</p>
<p><a href="{ctx["bookingUrl"]}">View booking</a></p>
"""
    _send_html(ctx["renterEmail"], f"Booking approved — {ctx['listingTitle']}", html)


def send_booking_rejected(booking_id: int) -> None:
    ctx = booking_email_context(booking_id)
    if not ctx:
        return
    html = f"""\
<p>Hi {ctx["renterName"]},</p>
<p>Your booking request for <strong>{ctx["listingTitle"]}</strong> was declined by the host.</p>
<p>Trip: {ctx["tripWindow"]}</p>
<p><a href="{ctx["tripsUrl"]}">View your trips</a></p>
"""
    _send_html(ctx["renterEmail"], f"Booking declined — {ctx['listingTitle']}", html)


def send_booking_cancelled(booking_id: int) -> None:
    ctx = booking_email_context(booking_id)
    if not ctx:
        return
    renter_html = f"""\
<p>Hi {ctx["renterName"]},</p>
<p>Your booking for <strong>{ctx["listingTitle"]}</strong> was cancelled.</p>
<p>Trip: {ctx["tripWindow"]}</p>
<p><a href="{ctx["tripsUrl"]}">View your trips</a></p>
"""
    _send_html(ctx["renterEmail"], f"Booking cancelled — {ctx['listingTitle']}", renter_html)
    if ctx.get("hostEmail"):
        host_html = f"""\
<p>Hi {ctx["hostName"]},</p>
<p>Booking for <strong>{ctx["listingTitle"]}</strong> was cancelled.</p>
<p>Trip: {ctx["tripWindow"]}</p>
<p><a href="{ctx["hostDashboardUrl"]}">Open host dashboard</a></p>
"""
        _send_html(ctx["hostEmail"], f"Booking cancelled — {ctx['listingTitle']}", host_html)


def send_trip_reminder(booking_id: int) -> bool:
    ctx = booking_email_context(booking_id)
    if not ctx:
        return False
    html = f"""\
<p>Hi {ctx["renterName"]},</p>
<p>Your trip for <strong>{ctx["listingTitle"]}</strong> starts in about 24 hours.</p>
<p>Trip: {ctx["tripWindow"]}</p>
<p><a href="{ctx["bookingUrl"]}">View pickup details</a></p>
"""
    return _send_html(ctx["renterEmail"], f"Trip starts soon — {ctx['listingTitle']}", html)


def send_trip_completed_review(booking_id: int) -> None:
    ctx = booking_email_context(booking_id)
    if not ctx:
        return
    html = f"""\
<p>Hi {ctx["renterName"]},</p>
<p>Your trip for <strong>{ctx["listingTitle"]}</strong> is complete.</p>
<p>Share feedback while it's fresh — reviews are open for 30 days.</p>
<p><a href="{ctx["tripsUrl"]}">Leave a review</a></p>
"""
    _send_html(ctx["renterEmail"], f"How was your trip? — {ctx['listingTitle']}", html)


def send_host_payout_sent(booking_id: int, *, amount: float, currency: str) -> None:
    ctx = booking_email_context(booking_id)
    if not ctx or not ctx.get("hostEmail"):
        return
    html = f"""\
<p>Hi {ctx["hostName"]},</p>
<p>We sent <strong>{amount:.2f} {currency.upper()}</strong> for your completed trip on
<strong>{ctx["listingTitle"]}</strong>.</p>
<p>Trip: {ctx["tripWindow"]}</p>
<p><a href="{ctx["hostDashboardUrl"]}">View payout details</a></p>
"""
    _send_html(
        ctx["hostEmail"],
        f"Payout sent — {ctx['listingTitle']}",
        html,
    )


def gross_payout_from_booking_row(row: dict) -> tuple[float, str]:
    pricing = build_price_breakdown(row)
    earnings = build_host_earnings(pricing)
    return float(earnings["grossPayout"]), str(earnings.get("currency") or "CAD")
