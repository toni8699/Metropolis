"""Remove legacy org/RBAC tables and redundant listing brand field.

Revision ID: 000005_legacy_cleanup
Revises: 000004_vehicle_deprecate
Create Date: 2026-06-14
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000005_legacy_cleanup"
down_revision: str | None = "000004_vehicle_deprecate"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Normalize listing make/brand redundancy before dropping brand column.
    op.execute(
        """
        UPDATE vehicle_listing
        SET make = COALESCE(make, brand)
        WHERE make IS NULL
        """
    )
    op.execute("ALTER TABLE vehicle_listing DROP COLUMN IF EXISTS brand")

    # Drop obsolete ownership/RBAC model from old experiments.
    op.execute("ALTER TABLE vehicle_listing DROP COLUMN IF EXISTS owner_organization_id")
    op.execute("DROP TABLE IF EXISTS organization_members")
    op.execute("DROP TABLE IF EXISTS organizations")
    op.execute("DROP TABLE IF EXISTS user_roles")
    op.execute("DROP TABLE IF EXISTS roles")

    # Drop legacy operational tables no longer used by runtime services.
    op.execute(
        """
        ALTER TABLE vehicle_listing
        DROP CONSTRAINT IF EXISTS vehicle_listing_vehicle_class_id_fkey
        """
    )
    op.execute(
        """
        ALTER TABLE vehicle_listing
        DROP CONSTRAINT IF EXISTS vehicle_listing_legacy_vehicle_class_id_fkey
        """
    )
    op.execute("ALTER TABLE vehicle_listing DROP COLUMN IF EXISTS vehicle_class_id")
    op.execute("ALTER TABLE vehicle_listing DROP COLUMN IF EXISTS legacy_vehicle_class_id")

    op.execute(
        """
        ALTER TABLE vehicle_asset
        DROP CONSTRAINT IF EXISTS vehicle_asset_vehicle_class_id_fkey
        """
    )
    op.execute(
        """
        ALTER TABLE vehicle_asset
        DROP CONSTRAINT IF EXISTS vehicle_asset_legacy_vehicle_class_id_fkey
        """
    )
    op.execute("ALTER TABLE vehicle_asset DROP COLUMN IF EXISTS vehicle_class_id")
    op.execute("ALTER TABLE vehicle_asset DROP COLUMN IF EXISTS legacy_vehicle_class_id")

    op.execute("ALTER TABLE branch DROP CONSTRAINT IF EXISTS fk_branch_manager")
    op.execute("ALTER TABLE branch DROP COLUMN IF EXISTS managerid")
    op.execute("DROP TABLE IF EXISTS branchmanager")
    op.execute("DROP TABLE IF EXISTS employee")
    op.execute("DROP TABLE IF EXISTS relocation")
    op.execute("DROP TABLE IF EXISTS vehicle")
    op.execute("DROP TABLE IF EXISTS vehicleclass")


def downgrade() -> None:
    # Intentional no-op: migration is a one-way cleanup.
    pass
