"""Allow ARCHIVED listing status (soft-delete) and protect booking history.

Revision ID: 000011_listing_archive_status
Revises: 000010_trip_inspection
Create Date: 2026-06-25
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000011_listing_archive_status"
down_revision: str | None = "000010_trip_inspection"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE vehicle_listing
          DROP CONSTRAINT IF EXISTS vehicle_listing_status_active_consistency;
        ALTER TABLE vehicle_listing
          ADD CONSTRAINT vehicle_listing_status_active_consistency CHECK (
            (status = 'ACTIVE' AND active = TRUE)
            OR (status = 'INACTIVE' AND active = FALSE)
            OR (status = 'ARCHIVED' AND active = FALSE)
          );

        ALTER TABLE booking
          DROP CONSTRAINT IF EXISTS booking_listing_id_fkey;
        ALTER TABLE booking
          ADD CONSTRAINT booking_listing_id_fkey
          FOREIGN KEY (listing_id) REFERENCES vehicle_listing(listing_id)
          ON DELETE RESTRICT;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE booking
          DROP CONSTRAINT IF EXISTS booking_listing_id_fkey;
        ALTER TABLE booking
          ADD CONSTRAINT booking_listing_id_fkey
          FOREIGN KEY (listing_id) REFERENCES vehicle_listing(listing_id)
          ON DELETE CASCADE;

        ALTER TABLE vehicle_listing
          DROP CONSTRAINT IF EXISTS vehicle_listing_status_active_consistency;
        ALTER TABLE vehicle_listing
          ADD CONSTRAINT vehicle_listing_status_active_consistency CHECK (
            (status = 'ACTIVE' AND active = TRUE)
            OR (status = 'INACTIVE' AND active = FALSE)
          );
        """
    )
