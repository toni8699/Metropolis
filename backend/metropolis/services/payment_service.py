from __future__ import annotations

import os

import stripe
from psycopg2.extras import Json, RealDictCursor

from metropolis.core.db import get_connection
from metropolis.services.booking_support import resolve_post_payment_status


def _stripe_enabled() -> bool:
    return bool(os.environ.get("STRIPE_SECRET_KEY", "").strip())


def _amount_cents_from_snapshot(snapshot: dict) -> int:
    total = float(snapshot.get("total") or 0)
    return max(50, int(round(total * 100)))


class PaymentService:
    def __init__(self) -> None:
        key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
        if key:
            stripe.api_key = key

    def create_payment_intent(self, booking_id: int, renter_user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                row = self._fetch_booking_for_payment(cur, booking_id)
                if not row:
                    return {"status": "not_found", "message": "Booking not found."}
                if row["renter_user_id"] != renter_user_id:
                    return {
                        "status": "forbidden",
                        "message": "Only the renter can pay for this booking.",
                    }
                if row["status"] != "PENDING":
                    return {
                        "status": "validation_error",
                        "message": "Booking is not awaiting payment.",
                    }

                snapshot = row["price_snapshot_json"] or {}
                amount_cents = _amount_cents_from_snapshot(snapshot)
                currency = (snapshot.get("currency") or "CAD").lower()

                cur.execute(
                    """
                    SELECT payment_id, status, stripe_payment_intent_id
                    FROM payment
                    WHERE booking_id = %s
                    """,
                    (booking_id,),
                )
                existing = cur.fetchone()
                if existing and existing["status"] == "succeeded":
                    return {
                        "status": "ok",
                        "bookingId": booking_id,
                        "clientSecret": None,
                        "mock": not _stripe_enabled(),
                        "alreadyPaid": True,
                    }

                if not _stripe_enabled():
                    conn.commit()
                    return self._complete_payment(booking_id, payment_intent_id=None, mock=True)

                intent_id = existing["stripe_payment_intent_id"] if existing else None
                client_secret = None
                if intent_id:
                    intent = stripe.PaymentIntent.retrieve(intent_id)
                    client_secret = intent.client_secret
                else:
                    intent = stripe.PaymentIntent.create(
                        amount=amount_cents,
                        currency=currency,
                        metadata={"booking_id": str(booking_id)},
                        automatic_payment_methods={"enabled": True},
                    )
                    intent_id = intent.id
                    client_secret = intent.client_secret
                    if existing:
                        cur.execute(
                            """
                            UPDATE payment
                            SET amount_cents = %s, currency = %s, stripe_payment_intent_id = %s,
                                updated_at = NOW()
                            WHERE booking_id = %s
                            """,
                            (amount_cents, currency, intent_id, booking_id),
                        )
                    else:
                        cur.execute(
                            """
                            INSERT INTO payment (
                              booking_id, amount_cents, currency, status, stripe_payment_intent_id
                            )
                            VALUES (%s, %s, %s, 'pending', %s)
                            """,
                            (booking_id, amount_cents, currency, intent_id),
                        )
                    conn.commit()

                return {
                    "status": "ok",
                    "bookingId": booking_id,
                    "clientSecret": client_secret,
                    "mock": False,
                    "alreadyPaid": False,
                }

    def handle_webhook(self, payload: bytes, signature: str | None) -> dict:
        secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()
        if not secret:
            return {"status": "validation_error", "message": "Stripe webhook not configured."}
        try:
            event = stripe.Webhook.construct_event(payload, signature, secret)
        except ValueError:
            return {"status": "validation_error", "message": "Invalid webhook payload."}
        except stripe.error.SignatureVerificationError:
            return {"status": "validation_error", "message": "Invalid webhook signature."}

        if event["type"] == "payment_intent.succeeded":
            intent = event["data"]["object"]
            booking_id = self._resolve_booking_id_from_intent(intent)
            if booking_id is None:
                return {"status": "validation_error", "message": "Missing booking reference."}
            return self._complete_payment(booking_id, payment_intent_id=intent["id"], mock=False)

        if event["type"] == "account.updated":
            from metropolis.services.payout_service import payout_service

            return payout_service.handle_account_updated(event["data"]["object"])

        return {"status": "ignored", "message": f"Unhandled event type {event['type']}."}

    def _resolve_booking_id_from_intent(self, intent: dict) -> int | None:
        metadata = intent.get("metadata") or {}
        raw = metadata.get("booking_id")
        if raw:
            return int(raw)
        intent_id = intent.get("id")
        if not intent_id:
            return None
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT booking_id FROM payment WHERE stripe_payment_intent_id = %s",
                    (intent_id,),
                )
                row = cur.fetchone()
                return int(row[0]) if row else None

    def _fetch_booking_for_payment(self, cur, booking_id: int):
        cur.execute(
            """
            SELECT b.booking_id, b.renter_user_id, b.status, b.price_snapshot_json,
                   l.source_type, l.instant_book
            FROM booking b
            JOIN vehicle_listing l ON l.listing_id = b.listing_id
            WHERE b.booking_id = %s
            FOR UPDATE
            """,
            (booking_id,),
        )
        return cur.fetchone()

    def _complete_payment(
        self,
        booking_id: int,
        *,
        payment_intent_id: str | None,
        mock: bool,
    ) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                row = self._fetch_booking_for_payment(cur, booking_id)
                if not row:
                    return {"status": "not_found", "message": "Booking not found."}
                if row["status"] != "PENDING":
                    return {
                        "status": "ok",
                        "bookingId": booking_id,
                        "clientSecret": None,
                        "mock": mock,
                        "alreadyPaid": True,
                    }

                snapshot = row["price_snapshot_json"] or {}
                amount_cents = _amount_cents_from_snapshot(snapshot)
                currency = (snapshot.get("currency") or "CAD").lower()
                next_status = resolve_post_payment_status(
                    row["source_type"],
                    bool(row.get("instant_book", True)),
                )

                cur.execute(
                    "SELECT payment_id, status FROM payment WHERE booking_id = %s",
                    (booking_id,),
                )
                payment_row = cur.fetchone()
                if payment_row and payment_row["status"] == "succeeded":
                    conn.commit()
                    return {
                        "status": "ok",
                        "bookingId": booking_id,
                        "clientSecret": None,
                        "mock": mock,
                        "alreadyPaid": True,
                    }

                if payment_row:
                    cur.execute(
                        """
                        UPDATE payment
                        SET status = 'succeeded',
                            stripe_payment_intent_id = COALESCE(%s, stripe_payment_intent_id),
                            updated_at = NOW()
                        WHERE booking_id = %s
                        """,
                        (payment_intent_id, booking_id),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO payment (
                          booking_id, amount_cents, currency, status, stripe_payment_intent_id
                        )
                        VALUES (%s, %s, %s, 'succeeded', %s)
                        """,
                        (booking_id, amount_cents, currency, payment_intent_id),
                    )

                cur.execute(
                    """
                    UPDATE booking
                    SET status = %s::booking_status, updated_at = NOW()
                    WHERE booking_id = %s
                    """,
                    (next_status, booking_id),
                )
                cur.execute(
                    """
                    INSERT INTO trip_event (booking_id, event_type, actor_user_id, metadata_json)
                    VALUES (%s, 'PAYMENT_SUCCEEDED', NULL, %s::jsonb)
                    """,
                    (
                        booking_id,
                        Json(
                            {
                                "mock": mock,
                                "toStatus": next_status,
                                "stripePaymentIntentId": payment_intent_id,
                            }
                        ),
                    ),
                )
                conn.commit()

        from metropolis.services.booking_notifications import notify_payment_completed

        notify_payment_completed(booking_id, next_status)

        return {
            "status": "ok",
            "bookingId": booking_id,
            "clientSecret": None,
            "mock": mock,
            "alreadyPaid": False,
        }

    def confirm_payment(self, booking_id: int, renter_user_id: int) -> dict:
        """Apply payment after client-side Stripe confirm (webhook fallback)."""
        if not _stripe_enabled():
            return {"status": "validation_error", "message": "Stripe not configured."}
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                row = self._fetch_booking_for_payment(cur, booking_id)
                if not row:
                    return {"status": "not_found", "message": "Booking not found."}
                if row["renter_user_id"] != renter_user_id:
                    return {
                        "status": "forbidden",
                        "message": "Only the renter can confirm payment.",
                    }
                if row["status"] != "PENDING":
                    return {
                        "status": "ok",
                        "bookingId": booking_id,
                        "alreadyPaid": True,
                    }
                cur.execute(
                    """
                    SELECT stripe_payment_intent_id, status
                    FROM payment
                    WHERE booking_id = %s
                    """,
                    (booking_id,),
                )
                payment_row = cur.fetchone()
                if not payment_row or not payment_row.get("stripe_payment_intent_id"):
                    return {
                        "status": "validation_error",
                        "message": "No payment found for this booking.",
                    }
                intent = stripe.PaymentIntent.retrieve(payment_row["stripe_payment_intent_id"])
                if intent.status != "succeeded":
                    return {
                        "status": "validation_error",
                        "message": "Payment has not completed yet.",
                    }
        return self._complete_payment(
            booking_id,
            payment_intent_id=intent.id,
            mock=False,
        )


payment_service = PaymentService()
