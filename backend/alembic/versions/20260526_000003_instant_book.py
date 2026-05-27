"""Listing instant_book + PENDING_APPROVAL booking status.

Revision ID: 000003_instant_book
Revises: 000002_review_sub_ratings
Create Date: 2026-05-26
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000003_instant_book"
down_revision: str | None = "000002_review_sub_ratings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE vehicle_listing
          ADD COLUMN IF NOT EXISTS instant_book BOOLEAN NOT NULL DEFAULT TRUE;
        """
    )
    op.execute(
        """
        ALTER TYPE booking_status ADD VALUE IF NOT EXISTS 'PENDING_APPROVAL';
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE vehicle_listing
          DROP COLUMN IF EXISTS instant_book;
        """
    )
