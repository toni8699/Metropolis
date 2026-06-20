"""Fixup: OTHER body type + body_type_other if 000005 ran before squash merge.

Revision ID: 000006_body_type_other_fixup
Revises: 000005_drop_odometer_columns
Create Date: 2026-06-19
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000006_body_type_other_fixup"
down_revision: str | None = "000005_drop_odometer_columns"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO ref_body_type (code, display_name, sort_order)
        VALUES ('OTHER', 'Other', 80)
        ON CONFLICT (code) DO NOTHING;

        ALTER TABLE vehicle_asset
          ADD COLUMN IF NOT EXISTS body_type_other VARCHAR(80);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE vehicle_asset DROP COLUMN IF EXISTS body_type_other;
        DELETE FROM ref_body_type WHERE code = 'OTHER';
        """
    )
