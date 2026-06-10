"""payment table for Stripe checkout.

Revision ID: 000005_payment
Revises: 000004_booking_message
Create Date: 2026-06-09
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000005_payment"
down_revision: str | None = "000004_booking_message"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS payment (
          payment_id BIGSERIAL PRIMARY KEY,
          booking_id BIGINT NOT NULL
            REFERENCES booking(booking_id) ON DELETE CASCADE,
          amount_cents INTEGER NOT NULL,
          currency VARCHAR(3) NOT NULL DEFAULT 'cad',
          status VARCHAR(20) NOT NULL DEFAULT 'pending',
          stripe_payment_intent_id VARCHAR(100),
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_payment_booking_id ON payment(booking_id)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_payment_stripe_intent ON payment(stripe_payment_intent_id)
        WHERE stripe_payment_intent_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS payment")
