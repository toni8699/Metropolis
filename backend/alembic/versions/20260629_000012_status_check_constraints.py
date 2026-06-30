"""Constrain free-text status columns to their known value sets.

Revision ID: 000012_status_check_constraints
Revises: 000011_listing_archive_status
Create Date: 2026-06-29
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000012_status_check_constraints"
down_revision: str | None = "000011_listing_archive_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE payment
          DROP CONSTRAINT IF EXISTS payment_status_check;
        ALTER TABLE payment
          ADD CONSTRAINT payment_status_check CHECK (
            status IN ('pending', 'succeeded', 'failed', 'refunded', 'canceled')
          );

        ALTER TABLE host_payout
          DROP CONSTRAINT IF EXISTS host_payout_status_check;
        ALTER TABLE host_payout
          ADD CONSTRAINT host_payout_status_check CHECK (
            status IN ('pending', 'pending_onboarding', 'succeeded', 'failed', 'skipped')
          );

        ALTER TABLE owner_profile
          DROP CONSTRAINT IF EXISTS owner_profile_verification_status_check;
        ALTER TABLE owner_profile
          ADD CONSTRAINT owner_profile_verification_status_check CHECK (
            verification_status IN ('PENDING', 'VERIFIED', 'REJECTED')
          );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE owner_profile
          DROP CONSTRAINT IF EXISTS owner_profile_verification_status_check;
        ALTER TABLE host_payout
          DROP CONSTRAINT IF EXISTS host_payout_status_check;
        ALTER TABLE payment
          DROP CONSTRAINT IF EXISTS payment_status_check;
        """
    )
