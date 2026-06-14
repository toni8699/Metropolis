"""Rename listing_location.raw_address to pickup_address.

Revision ID: 000002_listing_location_pickup_address
Revises: 000001_new_base
Create Date: 2026-06-14
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000002_listing_location_pickup_address"
down_revision: str | None = "000001_new_base"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'listing_location'
              AND column_name = 'raw_address'
          ) THEN
            ALTER TABLE listing_location
              RENAME COLUMN raw_address TO pickup_address;
          END IF;
        END $$
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'listing_location'
              AND column_name = 'pickup_address'
          ) THEN
            ALTER TABLE listing_location
              RENAME COLUMN pickup_address TO raw_address;
          END IF;
        END $$
        """
    )
