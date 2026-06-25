"""Mail service unit tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from vroom.services import mail_service


def test_send_html_noop_without_resend_config():
    with patch.object(mail_service.settings, "resend_api_key", ""):
        assert mail_service._send_html("a@b.com", "Subj", "<p>x</p>") is False


def test_booking_email_context_missing_returns_none():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = None
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.__enter__.return_value = mock_conn

    with patch("vroom.services.mail_service.get_connection", return_value=mock_conn):
        assert mail_service.booking_email_context(999) is None


def test_send_booking_confirmed_sends_renter_and_host():
    ctx = {
        "renterName": "Renter",
        "renterEmail": "renter@test.com",
        "hostName": "Host",
        "hostEmail": "host@test.com",
        "listingTitle": "Test Car",
        "tripWindow": "Jan 1 – Jan 2",
        "total": 200,
        "currency": "CAD",
        "bookingUrl": "http://localhost/app/bookings/1",
        "hostDashboardUrl": "http://localhost/host/dashboard",
    }
    with (
        patch("vroom.services.mail_service.booking_email_context", return_value=ctx),
        patch("vroom.services.mail_service._send_html", return_value=True) as send,
    ):
        mail_service.send_booking_confirmed(1)
    assert send.call_count == 2
