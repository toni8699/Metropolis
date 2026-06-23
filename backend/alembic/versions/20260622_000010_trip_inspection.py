"""Trip inspection photos + booking.completed_at.

Revision ID: 000010_trip_inspection
Revises: 000009_host_payout
Create Date: 2026-06-22
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000010_trip_inspection"
down_revision: str | None = "000009_host_payout"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
          CREATE TYPE trip_inspection_phase AS ENUM ('CHECK_IN', 'CHECK_OUT');
        EXCEPTION
          WHEN duplicate_object THEN NULL;
        END $$;

        ALTER TABLE booking ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

        CREATE INDEX IF NOT EXISTS idx_booking_completed_at
          ON booking(completed_at) WHERE status = 'COMPLETED';

        ALTER TABLE file_asset ADD COLUMN IF NOT EXISTS booking_id BIGINT
          REFERENCES booking(booking_id) ON DELETE SET NULL;

        ALTER TABLE file_asset DROP CONSTRAINT IF EXISTS file_asset_scope_check;
        ALTER TABLE file_asset ADD CONSTRAINT file_asset_scope_check
          CHECK (scope IN (
            'FLEET', 'OWNER_LISTING', 'USER_DOC', 'USER_AVATAR', 'TRIP_INSPECTION'
          ));

        CREATE TABLE IF NOT EXISTS booking_inspection_photo (
          photo_id            BIGSERIAL PRIMARY KEY,
          booking_id          BIGINT NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
          file_id             BIGINT NOT NULL REFERENCES file_asset(file_id) ON DELETE CASCADE,
          phase               trip_inspection_phase NOT NULL,
          angle_key           VARCHAR(64) NOT NULL,
          is_extra            BOOLEAN NOT NULL DEFAULT FALSE,
          uploaded_by_user_id BIGINT NOT NULL REFERENCES app_user(user_id),
          created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_booking_inspection_standard_slot
          ON booking_inspection_photo (booking_id, phase, angle_key)
          WHERE is_extra = FALSE;

        CREATE INDEX IF NOT EXISTS idx_booking_inspection_booking_phase
          ON booking_inspection_photo (booking_id, phase, created_at);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS booking_inspection_photo;
        ALTER TABLE file_asset DROP COLUMN IF EXISTS booking_id;
        ALTER TABLE booking DROP COLUMN IF EXISTS completed_at;
        DROP TYPE IF EXISTS trip_inspection_phase;
        """
    )
