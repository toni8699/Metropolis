"""Host payout ledger for Stripe Connect transfers.

Revision ID: 000009_host_payout
Revises: 000008_saved_listings
Create Date: 2026-06-21
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000009_host_payout"
down_revision: str | None = "000008_saved_listings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS host_payout (
          payout_id BIGSERIAL PRIMARY KEY,
          booking_id BIGINT NOT NULL UNIQUE REFERENCES booking(booking_id) ON DELETE CASCADE,
          owner_user_id BIGINT NOT NULL REFERENCES app_user(user_id),
          amount_cents INT NOT NULL CHECK (amount_cents > 0),
          currency VARCHAR(3) NOT NULL DEFAULT 'cad',
          stripe_transfer_id VARCHAR(100),
          status VARCHAR(20) NOT NULL DEFAULT 'pending',
          failure_reason TEXT,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_host_payout_owner_status
          ON host_payout(owner_user_id, status);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS host_payout;")
