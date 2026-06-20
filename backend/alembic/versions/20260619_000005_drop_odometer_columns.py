"""Drop odometer columns + OTHER body type + body_type_other text.

Revision ID: 000005_drop_odometer_columns
Revises: 000004_feature_catalog
Create Date: 2026-06-19
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000005_drop_odometer_columns"
down_revision: str | None = "000004_feature_catalog"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_vehicle_asset_sync_listing ON vehicle_asset;

        ALTER TABLE vehicle_asset DROP COLUMN IF EXISTS odometer_km;
        ALTER TABLE vehicle_listing DROP COLUMN IF EXISTS mileage;

        INSERT INTO ref_body_type (code, display_name, sort_order)
        VALUES ('OTHER', 'Other', 80)
        ON CONFLICT (code) DO NOTHING;

        ALTER TABLE vehicle_asset
          ADD COLUMN IF NOT EXISTS body_type_other VARCHAR(80);

        CREATE OR REPLACE FUNCTION sync_listing_cache_from_asset(p_vehicle_id BIGINT)
        RETURNS void
        LANGUAGE plpgsql
        AS $$
        BEGIN
          UPDATE vehicle_listing vl
          SET
            make = va.make,
            model = va.model,
            year = va.model_year,
            transmission = va.transmission,
            fuel_type = va.fuel_type,
            seats = va.seats,
            updated_at = NOW()
          FROM vehicle_asset va
          WHERE vl.vehicle_id = va.vehicle_id
            AND va.vehicle_id = p_vehicle_id;
        END;
        $$;

        CREATE OR REPLACE FUNCTION trg_sync_listing_cache_from_asset()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
          PERFORM sync_listing_cache_from_asset(NEW.vehicle_id);
          RETURN NEW;
        END;
        $$;

        CREATE TRIGGER trg_vehicle_asset_sync_listing
        AFTER INSERT OR UPDATE OF
          make, model, model_year, vin, fuel_type, transmission, seats, body_type_id
        ON vehicle_asset
        FOR EACH ROW
        EXECUTE FUNCTION trg_sync_listing_cache_from_asset();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_vehicle_asset_sync_listing ON vehicle_asset;

        ALTER TABLE vehicle_asset DROP COLUMN IF EXISTS body_type_other;
        DELETE FROM ref_body_type WHERE code = 'OTHER';

        ALTER TABLE vehicle_asset
          ADD COLUMN IF NOT EXISTS odometer_km INT
            CHECK (odometer_km IS NULL OR odometer_km >= 0);
        ALTER TABLE vehicle_listing
          ADD COLUMN IF NOT EXISTS mileage INT
            CHECK (mileage IS NULL OR mileage >= 0);

        CREATE OR REPLACE FUNCTION sync_listing_cache_from_asset(p_vehicle_id BIGINT)
        RETURNS void
        LANGUAGE plpgsql
        AS $$
        BEGIN
          UPDATE vehicle_listing vl
          SET
            make = va.make,
            model = va.model,
            year = va.model_year,
            mileage = va.odometer_km,
            transmission = va.transmission,
            fuel_type = va.fuel_type,
            seats = va.seats,
            updated_at = NOW()
          FROM vehicle_asset va
          WHERE vl.vehicle_id = va.vehicle_id
            AND va.vehicle_id = p_vehicle_id;
        END;
        $$;

        CREATE OR REPLACE FUNCTION trg_sync_listing_cache_from_asset()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
          PERFORM sync_listing_cache_from_asset(NEW.vehicle_id);
          RETURN NEW;
        END;
        $$;

        CREATE TRIGGER trg_vehicle_asset_sync_listing
        AFTER INSERT OR UPDATE OF
          make, model, model_year, vin, fuel_type, transmission, seats, odometer_km, body_type_id
        ON vehicle_asset
        FOR EACH ROW
        EXECUTE FUNCTION trg_sync_listing_cache_from_asset();
        """
    )
