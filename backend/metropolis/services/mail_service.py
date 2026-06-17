"""Transactional email via Resend."""

from __future__ import annotations

import logging

from metropolis.core.config import settings

_logger = logging.getLogger("metropolis.mail")


def send_verification_email(email: str, token: str) -> None:
    """Send HTML verification link. No-op when Resend is not configured."""
    api_key = settings.resend_api_key
    mail_from = settings.mail_from
    base_url = settings.frontend_base_url.rstrip("/")
    if not api_key or not mail_from:
        # ponytail: dev/test skip when keys missing; prod should set RESEND_API_KEY + MAIL_FROM
        _logger.warning("Skipping verification email to %s (Resend not configured)", email)
        return

    verify_url = f"{base_url}/verify-email?token={token}"
    html = f"""\
<p>Welcome to VROOM.</p>
<p>Confirm your email to finish signing up:</p>
<p><a href="{verify_url}">Verify email</a></p>
<p>Or copy this link: {verify_url}</p>
"""

    try:
        import resend

        resend.api_key = api_key
        response = resend.Emails.send(
            {
                "from": mail_from,
                "to": [email],
                "subject": "Verify your VROOM email",
                "html": html,
            }
        )
        _logger.info("Verification email queued for %s (resend id=%s)", email, response)
    except Exception:
        _logger.exception(
            "Failed to send verification email to %s (from=%s). "
            "Check RESEND_API_KEY, MAIL_FROM domain verification, and Resend logs.",
            email,
            mail_from,
        )
