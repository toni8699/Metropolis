"""Decouple runtime fleet flows from legacy Vehicle table.

Revision ID: 000004_vehicle_deprecate
Revises: 000003_asset_links
Create Date: 2026-06-14
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000004_vehicle_deprecate"
down_revision: str | None = "000003_asset_links"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE vehicle_asset
          ADD COLUMN IF NOT EXISTS branch_id INT REFERENCES branch(branchid) ON DELETE SET NULL,
          ADD COLUMN IF NOT EXISTS odometer_km INT CHECK (odometer_km IS NULL OR odometer_km >= 0),
          ADD COLUMN IF NOT EXISTS fleet_status VARCHAR(30)
        """
    )
    op.execute(
        """
        UPDATE vehicle_asset
        SET fleet_status = COALESCE(
          fleet_status,
          CASE
            WHEN asset_status = 'ACTIVE'::vehicle_asset_status THEN 'Available'
            WHEN asset_status = 'MAINTENANCE'::vehicle_asset_status THEN 'Maintenance'
            WHEN asset_status = 'RETIRED'::vehicle_asset_status THEN 'Retired'
            ELSE 'Onboarding'
          END
        )
        WHERE owner_type = 'COMPANY'::vehicle_owner_type
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vehicle_asset_fleet_branch_status ON vehicle_asset(branch_id, fleet_status)"
    )

    # Remove hard dependency from listings to legacy vehicle table.
    op.execute(
        """
        ALTER TABLE vehicle_listing
        DROP CONSTRAINT IF EXISTS vehicle_listing_fleet_vehicle_vin_fkey
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vehicle_listing_fleet_vin ON vehicle_listing(fleet_vehicle_vin)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_vehicle_listing_fleet_vin")
    op.execute("DROP INDEX IF EXISTS idx_vehicle_asset_fleet_branch_status")
    # Re-introducing the old FK is intentionally skipped to avoid data loss on downgrade.
