"""Backfill canonical vehicle_asset links from existing listings.

Revision ID: 000003_asset_links
Revises: 000002_vehicle_asset_foundation
Create Date: 2026-06-14
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000003_asset_links"
down_revision: str | None = "000002_vehicle_asset_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Fleet listings: create/find canonical asset by VIN, then attach listing.
    op.execute(
        """
        INSERT INTO vehicle_asset (
          vin, vehicle_category, owner_type, owner_party_name, asset_status, make, model, model_year
        )
        SELECT DISTINCT
          l.fleet_vehicle_vin,
          'STANDARD'::vehicle_category,
          'COMPANY'::vehicle_owner_type,
          'Company Fleet',
          CASE WHEN l.active THEN 'ACTIVE'::vehicle_asset_status
               ELSE 'ONBOARDING'::vehicle_asset_status END,
          COALESCE(v.make, l.make, l.brand),
          COALESCE(v.model, l.model),
          l.year
        FROM vehicle_listing l
        LEFT JOIN vehicle v ON v.vin = l.fleet_vehicle_vin
        WHERE l.source_type = 'FLEET'
          AND l.fleet_vehicle_vin IS NOT NULL
        ON CONFLICT (vin) DO UPDATE
          SET updated_at = NOW()
        """
    )
    op.execute(
        """
        UPDATE vehicle_listing l
        SET vehicle_id = va.vehicle_id
        FROM vehicle_asset va
        WHERE l.source_type = 'FLEET'
          AND l.fleet_vehicle_vin IS NOT NULL
          AND va.vin = l.fleet_vehicle_vin
          AND l.vehicle_id IS NULL
        """
    )

    # Host/company-owner listings: create one canonical asset per listing when missing.
    op.execute(
        """
        DO $$
        DECLARE
          r RECORD;
          created_vehicle_id BIGINT;
          normalized_owner vehicle_owner_type;
        BEGIN
          FOR r IN
            SELECT listing_id, owner_user_id, is_company_owned, active, make, brand, model, year
            FROM vehicle_listing
            WHERE source_type = 'OWNER'
              AND vehicle_id IS NULL
            ORDER BY listing_id
          LOOP
            normalized_owner := CASE
              WHEN COALESCE(r.is_company_owned, FALSE) THEN 'COMPANY'::vehicle_owner_type
              ELSE 'INDEPENDENT_HOST'::vehicle_owner_type
            END;

            INSERT INTO vehicle_asset (
              vehicle_category,
              owner_type,
              owner_party_user_id,
              owner_party_name,
              asset_status,
              make,
              model,
              model_year
            )
            VALUES (
              'STANDARD'::vehicle_category,
              normalized_owner,
              r.owner_user_id,
              CASE WHEN normalized_owner = 'COMPANY'::vehicle_owner_type THEN 'Company Managed' ELSE NULL END,
              CASE WHEN r.active THEN 'ACTIVE'::vehicle_asset_status
                   ELSE 'ONBOARDING'::vehicle_asset_status END,
              COALESCE(r.make, r.brand),
              r.model,
              r.year
            )
            RETURNING vehicle_id INTO created_vehicle_id;

            UPDATE vehicle_listing
            SET vehicle_id = created_vehicle_id
            WHERE listing_id = r.listing_id;
          END LOOP;
        END $$;
        """
    )

    # Align initial listing visibility to current active flag.
    op.execute(
        """
        UPDATE vehicle_listing
        SET visibility_status = CASE
          WHEN active THEN 'PUBLISHED'::listing_visibility_status
          ELSE 'HIDDEN'::listing_visibility_status
        END
        """
    )


def downgrade() -> None:
    # Keep canonical links on downgrade to avoid destructive data loss.
    pass
