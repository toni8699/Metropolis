"""Stripe Connect host payouts (transfer on trip COMPLETED)."""

from __future__ import annotations

import logging
import os

import stripe
from psycopg2.extras import RealDictCursor

from metropolis.core.config import settings
from metropolis.core.db import get_connection
from metropolis.services import mail_service
from metropolis.services.booking_rows import build_host_earnings, build_price_breakdown

_logger = logging.getLogger("metropolis.payout")


def _stripe_enabled() -> bool:
    key = settings.stripe_secret_key.strip() or os.environ.get("STRIPE_SECRET_KEY", "").strip()
    return bool(key)


def _connect_enabled() -> bool:
    if not _stripe_enabled():
        return False
    raw = os.environ.get("STRIPE_CONNECT_ENABLED", "").strip().lower()
    if raw in {"0", "false", "no"}:
        return False
    return True


def _configure_stripe() -> None:
    key = settings.stripe_secret_key.strip() or os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if key:
        stripe.api_key = key


class PayoutService:
    def __init__(self) -> None:
        _configure_stripe()

    def get_connect_status(self, user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                profile = self._fetch_owner_profile(cur, user_id)
        if not profile:
            return {
                "status": "success",
                "connect": {
                    "accountId": None,
                    "detailsSubmitted": False,
                    "chargesEnabled": False,
                    "payoutsEnabled": False,
                    "ready": False,
                },
                "recentPayouts": [],
            }
        account_id = profile.get("payout_ref")
        connect = {
            "accountId": account_id,
            "detailsSubmitted": False,
            "chargesEnabled": False,
            "payoutsEnabled": False,
            "ready": False,
        }
        if account_id and _connect_enabled():
            try:
                account = stripe.Account.retrieve(account_id)
                connect["detailsSubmitted"] = bool(account.get("details_submitted"))
                connect["chargesEnabled"] = bool(account.get("charges_enabled"))
                connect["payoutsEnabled"] = bool(account.get("payouts_enabled"))
                connect["ready"] = (
                    connect["detailsSubmitted"]
                    and connect["chargesEnabled"]
                    and connect["payoutsEnabled"]
                )
            except Exception:
                _logger.exception("Failed to retrieve Connect account %s", account_id)
        recent = self._list_recent_payouts(user_id)
        return {"status": "success", "connect": connect, "recentPayouts": recent}

    def create_onboarding_link(self, user_id: int, email: str) -> dict:
        if not _connect_enabled():
            return {
                "status": "validation_error",
                "message": "Stripe Connect is not configured.",
            }
        account_id = self.ensure_connect_account(user_id, email)
        if not account_id:
            return {"status": "error", "message": "Could not create Connect account."}
        base = settings.frontend_base_url.rstrip("/")
        try:
            link = stripe.AccountLink.create(
                account=account_id,
                refresh_url=f"{base}/host/dashboard?payout=refresh",
                return_url=f"{base}/host/dashboard?payout=complete",
                type="account_onboarding",
            )
        except Exception as exc:
            _logger.exception("AccountLink.create failed for user %s", user_id)
            return {"status": "error", "message": str(exc)}
        return {
            "status": "success",
            "onboardingUrl": link.url,
            "accountId": account_id,
        }

    def ensure_connect_account(self, user_id: int, email: str) -> str | None:
        if not _connect_enabled():
            return None
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                profile = self._fetch_owner_profile(cur, user_id)
                if profile and profile.get("payout_ref"):
                    return profile["payout_ref"]
                try:
                    account = stripe.Account.create(
                        type="express",
                        country="CA",
                        email=email,
                        capabilities={"transfers": {"requested": True}},
                        metadata={"user_id": str(user_id)},
                    )
                except Exception:
                    _logger.exception("Account.create failed for user %s", user_id)
                    return None
                account_id = account.id
                cur.execute(
                    """
                    INSERT INTO owner_profile (user_id, verification_status, payout_ref)
                    VALUES (%s, 'PENDING', %s)
                    ON CONFLICT (user_id) DO UPDATE
                    SET payout_ref = EXCLUDED.payout_ref
                    """,
                    (user_id, account_id),
                )
                conn.commit()
                return account_id

    def transfer_for_booking(self, booking_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                row = self._fetch_payout_context(cur, booking_id)
                if not row:
                    return {"status": "not_found", "message": "Booking not found."}
                if row["status"] != "COMPLETED":
                    return {
                        "status": "validation_error",
                        "message": "Payout only runs for completed bookings.",
                    }
                if row["source_type"] != "OWNER":
                    return {"status": "skipped", "message": "Fleet bookings skip Connect payout."}
                cur.execute(
                    """
                    SELECT payout_id, status, stripe_transfer_id
                    FROM host_payout WHERE booking_id = %s
                    """,
                    (booking_id,),
                )
                existing = cur.fetchone()
                if existing and existing["status"] == "succeeded":
                    return {
                        "status": "success",
                        "payoutStatus": "succeeded",
                        "transferId": existing.get("stripe_transfer_id"),
                    }
                pricing = build_price_breakdown(row)
                earnings = build_host_earnings(pricing)
                amount_cents = max(1, int(round(float(earnings["grossPayout"]) * 100)))
                currency = (earnings.get("currency") or "CAD").lower()
                owner_user_id = row["owner_user_id"]
                if not _connect_enabled():
                    self._upsert_payout(
                        cur,
                        booking_id=booking_id,
                        owner_user_id=owner_user_id,
                        amount_cents=amount_cents,
                        currency=currency,
                        status="skipped",
                        transfer_id=None,
                        failure_reason="Stripe Connect disabled",
                    )
                    conn.commit()
                    return {"status": "skipped", "payoutStatus": "skipped"}
                payment_status = (row.get("payment_status") or "").lower()
                if payment_status != "succeeded":
                    return {
                        "status": "validation_error",
                        "message": "Booking payment not succeeded.",
                    }
                profile = self._fetch_owner_profile(cur, owner_user_id)
                account_id = profile.get("payout_ref") if profile else None
                ready = account_id and self._account_ready(account_id)
                if not ready:
                    self._upsert_payout(
                        cur,
                        booking_id=booking_id,
                        owner_user_id=owner_user_id,
                        amount_cents=amount_cents,
                        currency=currency,
                        status="pending_onboarding",
                        transfer_id=None,
                        failure_reason="Host Connect onboarding incomplete",
                    )
                    conn.commit()
                    return {"status": "pending_onboarding", "payoutStatus": "pending_onboarding"}
                try:
                    transfer = stripe.Transfer.create(
                        amount=amount_cents,
                        currency=currency,
                        destination=account_id,
                        transfer_group=str(booking_id),
                        metadata={"booking_id": str(booking_id)},
                    )
                    transfer_id = transfer.id
                except Exception as exc:
                    _logger.exception("Transfer failed for booking %s", booking_id)
                    self._upsert_payout(
                        cur,
                        booking_id=booking_id,
                        owner_user_id=owner_user_id,
                        amount_cents=amount_cents,
                        currency=currency,
                        status="failed",
                        transfer_id=None,
                        failure_reason=str(exc),
                    )
                    conn.commit()
                    return {"status": "error", "message": str(exc), "payoutStatus": "failed"}
                self._upsert_payout(
                    cur,
                    booking_id=booking_id,
                    owner_user_id=owner_user_id,
                    amount_cents=amount_cents,
                    currency=currency,
                    status="succeeded",
                    transfer_id=transfer_id,
                    failure_reason=None,
                )
                conn.commit()
        try:
            mail_service.send_host_payout_sent(
                booking_id,
                amount=float(earnings["grossPayout"]),
                currency=currency,
            )
        except Exception:
            _logger.exception("payout email failed for booking %s", booking_id)
        return {
            "status": "success",
            "payoutStatus": "succeeded",
            "transferId": transfer_id,
        }

    def handle_account_updated(self, account: dict) -> dict:
        account_id = account.get("id")
        if not account_id:
            return {"status": "ignored"}
        if not (
            account.get("charges_enabled")
            and account.get("payouts_enabled")
            and account.get("details_submitted")
        ):
            return {"status": "ignored", "message": "Account not fully enabled."}
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT user_id FROM owner_profile WHERE payout_ref = %s",
                    (account_id,),
                )
                owners = cur.fetchall()
        retried = 0
        for owner in owners:
            with get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT booking_id FROM host_payout
                        WHERE owner_user_id = %s AND status = 'pending_onboarding'
                        ORDER BY created_at ASC
                        LIMIT 50
                        """,
                        (owner["user_id"],),
                    )
                    pending = [r["booking_id"] for r in cur.fetchall()]
            for booking_id in pending:
                result = self.transfer_for_booking(booking_id)
                if result.get("payoutStatus") == "succeeded":
                    retried += 1
        return {"status": "success", "retried": retried}

    def _account_ready(self, account_id: str) -> bool:
        try:
            account = stripe.Account.retrieve(account_id)
            return bool(
                account.get("details_submitted")
                and account.get("charges_enabled")
                and account.get("payouts_enabled")
            )
        except Exception:
            return False

    def _fetch_owner_profile(self, cur, user_id: int) -> dict | None:
        cur.execute(
            """
            SELECT user_id, payout_ref, verification_status
            FROM owner_profile
            WHERE user_id = %s
            """,
            (user_id,),
        )
        return cur.fetchone()

    def _fetch_payout_context(self, cur, booking_id: int) -> dict | None:
        cur.execute(
            """
            SELECT
              b.booking_id,
              b.status,
              b.price_snapshot_json,
              b.start_at,
              b.end_at,
              l.source_type,
              l.owner_user_id,
              l.title AS listing_title,
              p.status AS payment_status
            FROM booking b
            JOIN vehicle_listing l ON l.listing_id = b.listing_id
            LEFT JOIN payment p ON p.booking_id = b.booking_id
            WHERE b.booking_id = %s
            FOR UPDATE OF b
            """,
            (booking_id,),
        )
        return cur.fetchone()

    def _upsert_payout(
        self,
        cur,
        *,
        booking_id: int,
        owner_user_id: int,
        amount_cents: int,
        currency: str,
        status: str,
        transfer_id: str | None,
        failure_reason: str | None,
    ) -> None:
        cur.execute(
            """
            INSERT INTO host_payout (
              booking_id, owner_user_id, amount_cents, currency,
              stripe_transfer_id, status, failure_reason
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (booking_id) DO UPDATE SET
              amount_cents = EXCLUDED.amount_cents,
              currency = EXCLUDED.currency,
              stripe_transfer_id = COALESCE(
                EXCLUDED.stripe_transfer_id, host_payout.stripe_transfer_id
              ),
              status = EXCLUDED.status,
              failure_reason = EXCLUDED.failure_reason,
              updated_at = NOW()
            """,
            (
                booking_id,
                owner_user_id,
                amount_cents,
                currency,
                transfer_id,
                status,
                failure_reason,
            ),
        )

    def _list_recent_payouts(self, owner_user_id: int, limit: int = 10) -> list[dict]:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT hp.payout_id, hp.booking_id, hp.amount_cents, hp.currency,
                           hp.status, hp.stripe_transfer_id, hp.created_at,
                           l.title AS listing_title
                    FROM host_payout hp
                    JOIN booking b ON b.booking_id = hp.booking_id
                    JOIN vehicle_listing l ON l.listing_id = b.listing_id
                    WHERE hp.owner_user_id = %s
                    ORDER BY hp.created_at DESC
                    LIMIT %s
                    """,
                    (owner_user_id, limit),
                )
                rows = cur.fetchall()
        return [
            {
                "payoutId": row["payout_id"],
                "bookingId": row["booking_id"],
                "listingTitle": row["listing_title"],
                "amountCents": row["amount_cents"],
                "currency": row["currency"],
                "status": row["status"],
                "stripeTransferId": row.get("stripe_transfer_id"),
                "createdAt": row["created_at"].isoformat(),
            }
            for row in rows
        ]


payout_service = PayoutService()
