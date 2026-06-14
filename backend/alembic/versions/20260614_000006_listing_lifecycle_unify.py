"""Unify listing lifecycle semantics around status.

Revision ID: 000006_listing_lifecycle_unify
Revises: 000005_legacy_cleanup
Create Date: 2026-06-14
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000006_listing_lifecycle_unify"
down_revision: str | None = "000005_legacy_cleanup"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE vehicle_listing
        ADD COLUMN IF NOT EXISTS status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE'
        """
    )
    op.execute(
        """
        UPDATE vehicle_listing
        SET status = CASE WHEN active THEN 'ACTIVE' ELSE 'INACTIVE' END
        WHERE status IS NULL OR status NOT IN ('ACTIVE', 'INACTIVE')
        """
    )
    op.execute(
        """
        ALTER TABLE vehicle_listing
        DROP CONSTRAINT IF EXISTS vehicle_listing_status_active_consistency
        """
    )
    op.execute(
        """
        ALTER TABLE vehicle_listing
        ADD CONSTRAINT vehicle_listing_status_active_consistency
        CHECK (
          (status = 'ACTIVE' AND active = TRUE)
          OR (status = 'INACTIVE' AND active = FALSE)
        )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE vehicle_listing
        DROP CONSTRAINT IF EXISTS vehicle_listing_status_active_consistency
        """
    )
