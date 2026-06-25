"""Stripe Connect host payouts (transfer on trip COMPLETED)."""

from __future__ import annotations

import logging
import os
from typing import Any

import stripe
from psycopg2.extras import RealDictCursor

from vroom.core.config import settings
from vroom.core.db import get_connection
from vroom.services import mail_service, stripe_connect_v2
from vroom.services.booking_rows import build_host_earnings, build_price_breakdown
from vroom.services.stripe_connect_v2 import StripeConnectV2Error

_logger = logging.getLogger("vroom.payout")


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


def _connect_setup_message(exc: Exception) -> str:
    msg = getattr(exc, "message", None) or str(exc).strip()
    if "signed up for Connect" in msg:
        return (
            "Stripe Connect is not enabled for this platform. "
            "Enable Connect in the Stripe Dashboard (Express), then try again."
        )
    return msg or "Stripe payout setup failed."


def _public_business_url() -> str | None:
    """HTTPS marketing URL for Connect prefill (Stripe rejects localhost)."""
    explicit = settings.stripe_connect_business_url.strip()
    if explicit:
        return explicit.rstrip("/")
    base = settings.frontend_base_url.strip().rstrip("/")
    if base.startswith("https://") and "localhost" not in base and "127.0.0.1" not in base:
        return base
    return None


def _platform_business_profile() -> dict:
    brand = settings.stripe_connect_business_name.strip() or "Vroom"
    profile: dict = {
        "name": brand,
        "product_description": (
            f"Independent vehicle host on {brand}. Peer-to-peer car rentals in Canada."
        ),
        "mcc": "7512",
    }
    url = _public_business_url()
    if url:
        profile["url"] = url
    support = (settings.stripe_connect_support_email or settings.mail_from or "").strip()
    if support:
        profile["support_email"] = support
    return profile


def _individual_prefill(email: str, full_name: str | None, phone: str | None = None) -> dict:
    individual = {"email": email}
    if full_name:
        parts = full_name.strip().split(None, 1)
        if parts:
            individual["first_name"] = parts[0][:100]
            if len(parts) > 1:
                individual["last_name"] = parts[1][:100]
    if phone and phone.strip():
        individual["phone"] = phone.strip()[:20]
    return individual


def _v2_individual_identity(email: str, full_name: str | None, phone: str | None) -> dict:
    individual = {"email": email}
    prefill = _individual_prefill(email, full_name, phone)
    if prefill.get("first_name"):
        individual["given_name"] = prefill["first_name"]
    if prefill.get("last_name"):
        individual["surname"] = prefill["last_name"]
    if prefill.get("phone"):
        individual["phone"] = prefill["phone"]
    return individual


def _v2_defaults_profile() -> dict:
    biz = _platform_business_profile()
    profile: dict = {"product_description": biz["product_description"]}
    url = biz.get("url")
    if url:
        profile["business_url"] = url
    return profile


def _build_v2_create_payload(
    user_id: int, email: str, full_name: str | None, phone: str | None
) -> dict[str, Any]:
    brand = settings.stripe_connect_business_name.strip() or "Vroom"
    return {
        "contact_email": email,
        "display_name": brand,
        "dashboard": "express",
        "identity": {
            "country": "CA",
            "entity_type": "individual",
            "individual": _v2_individual_identity(email, full_name, phone),
        },
        "defaults": {
            "responsibilities": {
                "fees_collector": "application",
                "losses_collector": "application",
            },
            "profile": _v2_defaults_profile(),
        },
        "configuration": {
            "recipient": {
                "capabilities": {
                    "stripe_balance": {"stripe_transfers": {"requested": True}},
                },
            },
        },
        "include": ["configuration.recipient", "identity", "requirements"],
        "metadata": {"user_id": str(user_id)},
    }


def _account_requirements(account: dict) -> dict:
    return account.get("requirements") or {}


def _v2_transfers_status(account: dict) -> str | None:
    config = account.get("configuration") or {}
    recipient = config.get("recipient") or {}
    caps = recipient.get("capabilities") or {}
    stripe_balance = caps.get("stripe_balance") or {}
    transfers = stripe_balance.get("stripe_transfers") or {}
    status = transfers.get("status")
    return status if isinstance(status, str) else None


def _v2_transfer_capability_active(account: dict) -> bool:
    return _v2_transfers_status(account) == "active"


def _requirement_deadline_status(block: dict | None) -> str | None:
    if not isinstance(block, dict):
        return None
    status = block.get("status")
    return status if isinstance(status, str) else None


def _requirements_has_open_entries(account: dict) -> bool:
    requirements = _account_requirements(account)
    entries = requirements.get("entries")
    if entries is None:
        return bool(requirements.get("currently_due") or requirements.get("past_due"))
    open_statuses = {"currently_due", "past_due"}
    for entry in entries:
        for key in ("minimum_deadline", "deadline"):
            status = _requirement_deadline_status(entry.get(key))
            if status in open_statuses:
                return True
    summary = requirements.get("summary") or {}
    status = _requirement_deadline_status(summary.get("minimum_deadline"))
    return status in open_statuses


def _requirements_pending_verification(account: dict) -> bool:
    requirements = _account_requirements(account)
    entries = requirements.get("entries")
    if entries is None:
        return bool(requirements.get("pending_verification"))
    for entry in entries:
        for key in ("minimum_deadline", "deadline"):
            if _requirement_deadline_status(entry.get(key)) == "pending_verification":
                return True
    summary = requirements.get("summary") or {}
    return _requirement_deadline_status(summary.get("minimum_deadline")) == "pending_verification"


def _requirements_submitted_awaiting_activation(account: dict) -> bool:
    """Host finished embedded onboarding; Stripe still activating transfers."""
    if _v2_transfer_capability_active(account):
        return False
    requirements = _account_requirements(account)
    entries = requirements.get("entries")
    if entries is None:
        return False
    return not entries and not _requirements_has_open_entries(account)


def _connect_ready_from_account(account: dict) -> bool:
    return _v2_transfer_capability_active(account)


def _account_onboarding_required(account: dict) -> bool:
    if _connect_ready_from_account(account):
        return False
    if _requirements_pending_verification(account):
        return False
    if _requirements_submitted_awaiting_activation(account):
        return False
    if _requirements_has_open_entries(account):
        return True
    requirements = _account_requirements(account)
    if requirements.get("pending_verification"):
        return False
    if requirements.get("entries") is not None:
        return False
    return True


def _account_pending_verification(account: dict) -> bool:
    if _connect_ready_from_account(account):
        return False
    if _requirements_pending_verification(account):
        return True
    return _requirements_submitted_awaiting_activation(account)


def _resolve_charge_id(payment_intent_id: str | None) -> str | None:
    """Charge ID for transfer source_transaction (works before platform Available settles)."""
    if not payment_intent_id:
        return None
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        charge_id = intent.get("latest_charge")
        return charge_id if isinstance(charge_id, str) and charge_id else None
    except stripe.StripeError:
        _logger.exception("Could not resolve charge for PaymentIntent %s", payment_intent_id)
        return None


def _connect_flags_from_account(account: dict) -> dict:
    requirements = _account_requirements(account)
    ready = _connect_ready_from_account(account)
    details_submitted = (
        ready
        or _account_pending_verification(account)
        or (
            not _requirements_has_open_entries(account)
            and (
                requirements.get("entries") is not None
                or (not requirements.get("currently_due") and not requirements.get("past_due"))
            )
        )
    )
    return {
        "detailsSubmitted": bool(details_submitted),
        "chargesEnabled": ready,
        "payoutsEnabled": ready,
        "ready": ready,
        "onboardingRequired": _account_onboarding_required(account),
        "pendingVerification": _account_pending_verification(account),
    }


def _retrieve_connect_account(account_id: str) -> dict:
    return stripe_connect_v2.retrieve_account(account_id)


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
                    "onboardingRequired": False,
                    "pendingVerification": False,
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
            "onboardingRequired": False,
            "pendingVerification": False,
        }
        if account_id and _connect_enabled():
            try:
                account = _retrieve_connect_account(account_id)
                connect.update(_connect_flags_from_account(account))
            except Exception:
                _logger.exception("Failed to retrieve Connect account %s", account_id)
        recent = self._list_recent_payouts(user_id)
        if connect.get("ready") and any(
            p["status"] in ("pending_onboarding", "failed") for p in recent
        ):
            self._retry_pending_payouts_for_owner(user_id)
            recent = self._list_recent_payouts(user_id)
        return {"status": "success", "connect": connect, "recentPayouts": recent}

    def create_account_session(
        self, user_id: int, email: str | None, *, component: str = "onboarding"
    ) -> dict:
        """Client secret for Connect embedded onboarding or account management."""
        if not _connect_enabled():
            return {
                "status": "validation_error",
                "message": "Stripe Connect is not configured.",
            }
        if not (email or "").strip():
            return {
                "status": "validation_error",
                "message": "Account email is required for payout setup.",
            }
        account_id, err = self.ensure_connect_account(user_id, email.strip())
        if not account_id:
            return {
                "status": "validation_error",
                "message": err or "Could not create Connect account.",
            }
        use_management = component == "management"
        try:
            account = _retrieve_connect_account(account_id)
            ready = _connect_ready_from_account(account)
            if use_management:
                if not ready:
                    return {
                        "status": "validation_error",
                        "message": "Complete payout setup before managing settings.",
                    }
                session_components = {
                    "account_management": {
                        "enabled": True,
                        "features": {"external_account_collection": True},
                    },
                }
            elif ready:
                session_components = {
                    "account_management": {
                        "enabled": True,
                        "features": {"external_account_collection": True},
                    },
                }
            else:
                session_components = {
                    "account_onboarding": {
                        "enabled": True,
                        "features": {"external_account_collection": True},
                    },
                }
            session = stripe.AccountSession.create(
                account=account_id,
                components=session_components,
            )
        except (stripe.StripeError, StripeConnectV2Error) as exc:
            _logger.exception("AccountSession failed for user %s", user_id)
            return {"status": "validation_error", "message": _connect_setup_message(exc)}
        return {
            "status": "success",
            "clientSecret": session.client_secret,
            "accountId": account_id,
            "component": "management" if use_management or ready else "onboarding",
        }

    def create_express_dashboard_link(self, user_id: int) -> dict:
        """One-time Stripe Express dashboard login URL (ready accounts only)."""
        if not _connect_enabled():
            return {
                "status": "validation_error",
                "message": "Stripe Connect is not configured.",
            }
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                profile = self._fetch_owner_profile(cur, user_id)
        account_id = profile.get("payout_ref") if profile else None
        if not account_id:
            return {"status": "validation_error", "message": "No payout account linked."}
        if not self._account_ready(account_id):
            return {
                "status": "validation_error",
                "message": "Complete payout setup before opening Stripe dashboard.",
            }
        try:
            login = stripe.Account.create_login_link(account_id)
        except stripe.StripeError as exc:
            _logger.exception("Express login link failed for user %s", user_id)
            return {"status": "validation_error", "message": _connect_setup_message(exc)}
        return {
            "status": "success",
            "dashboardUrl": login.url,
            "accountId": account_id,
        }

    def reset_connect_account(self, user_id: int) -> dict:
        """Unlink Stripe Connect account so host can onboard fresh (debug only)."""
        if not settings.debug:
            return {
                "status": "forbidden",
                "message": "Payout reset is only available in debug mode.",
            }
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE owner_profile SET payout_ref = NULL WHERE user_id = %s",
                    (user_id,),
                )
                conn.commit()
        return {
            "status": "success",
            "message": "Payout account unlinked. Click Set up payouts to start again.",
        }

    def ensure_connect_account(self, user_id: int, email: str) -> tuple[str | None, str | None]:
        if not _connect_enabled():
            return None, "Stripe Connect is not configured."
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                profile = self._fetch_owner_profile(cur, user_id)
                if profile and profile.get("payout_ref"):
                    return profile["payout_ref"], None
                user_row = self._fetch_app_user(cur, user_id)
                full_name = user_row.get("full_name") if user_row else None
                phone = user_row.get("phone") if user_row else None
                try:
                    account = stripe_connect_v2.create_account(
                        _build_v2_create_payload(user_id, email, full_name, phone)
                    )
                except StripeConnectV2Error as exc:
                    _logger.exception("v2 account create failed for user %s", user_id)
                    return None, _connect_setup_message(exc)
                account_id = account.get("id")
                if not account_id:
                    return None, "Stripe did not return a Connect account id."
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
                return account_id, None

    def _fetch_app_user(self, cur, user_id: int) -> dict | None:
        cur.execute(
            "SELECT email, full_name, phone FROM app_user WHERE user_id = %s",
            (user_id,),
        )
        return cur.fetchone()

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
                    transfer_params: dict = {
                        "amount": amount_cents,
                        "currency": currency,
                        "destination": account_id,
                        "transfer_group": str(booking_id),
                        "metadata": {"booking_id": str(booking_id)},
                    }
                    charge_id = _resolve_charge_id(row.get("stripe_payment_intent_id"))
                    if charge_id:
                        transfer_params["source_transaction"] = charge_id
                    transfer = stripe.Transfer.create(**transfer_params)
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

    def handle_account_updated(self, account_id: str) -> dict:
        if not account_id:
            return {"status": "ignored"}
        try:
            account = _retrieve_connect_account(account_id)
        except Exception:
            _logger.exception("Could not load Connect account %s for webhook", account_id)
            return {"status": "ignored"}
        if not _connect_ready_from_account(account):
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
            retried += self._retry_pending_payouts_for_owner(owner["user_id"])
        return {"status": "success", "retried": retried}

    def _retry_pending_payouts_for_owner(self, owner_user_id: int) -> int:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT booking_id FROM host_payout
                    WHERE owner_user_id = %s AND status IN ('pending_onboarding', 'failed')
                    ORDER BY created_at ASC
                    LIMIT 50
                    """,
                    (owner_user_id,),
                )
                pending = [r["booking_id"] for r in cur.fetchall()]
        retried = 0
        for booking_id in pending:
            result = self.transfer_for_booking(booking_id)
            if result.get("payoutStatus") == "succeeded":
                retried += 1
        return retried

    def _account_ready(self, account_id: str) -> bool:
        try:
            account = _retrieve_connect_account(account_id)
            return _connect_ready_from_account(account)
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
              p.status AS payment_status,
              p.stripe_payment_intent_id
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
