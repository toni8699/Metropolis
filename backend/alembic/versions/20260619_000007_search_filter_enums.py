"""Search filter enums (incl. Diesel), transmission_type, filter indexes.

Revision ID: 000007_search_filter_enums
Revises: 000006_body_type_other_fixup
Create Date: 2026-06-19
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000007_search_filter_enums"
down_revision: str | None = "000006_body_type_other_fixup"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BACKFILL_TRANSMISSION = """
UPDATE vehicle_asset
SET transmission = CASE
  WHEN transmission IS NULL OR btrim(transmission) = '' THEN NULL
  WHEN lower(transmission) LIKE '%manual%' THEN 'MANUAL'
  WHEN lower(transmission) LIKE '%auto%' OR lower(transmission) LIKE '%cvt%' THEN 'AUTOMATIC'
  ELSE NULL
END;

UPDATE vehicle_listing
SET transmission = CASE
  WHEN transmission IS NULL OR btrim(transmission) = '' THEN NULL
  WHEN lower(transmission) LIKE '%manual%' THEN 'MANUAL'
  WHEN lower(transmission) LIKE '%auto%' OR lower(transmission) LIKE '%cvt%' THEN 'AUTOMATIC'
  ELSE NULL
END;
"""

_BACKFILL_FUEL = """
UPDATE vehicle_asset
SET fuel_type = CASE
  WHEN fuel_type IS NULL OR btrim(fuel_type) = '' THEN NULL
  WHEN lower(fuel_type) LIKE '%electric%' OR lower(fuel_type) = 'ev' THEN 'Electric'
  WHEN lower(fuel_type) LIKE '%hybrid%' THEN 'Hybrid'
  WHEN lower(fuel_type) LIKE '%diesel%' THEN 'Diesel'
  WHEN lower(fuel_type) LIKE '%gas%' OR lower(fuel_type) LIKE '%petrol%' THEN 'Gasoline'
  ELSE NULL
END;

UPDATE vehicle_listing
SET fuel_type = CASE
  WHEN fuel_type IS NULL OR btrim(fuel_type) = '' THEN NULL
  WHEN lower(fuel_type) LIKE '%electric%' OR lower(fuel_type) = 'ev' THEN 'Electric'
  WHEN lower(fuel_type) LIKE '%hybrid%' THEN 'Hybrid'
  WHEN lower(fuel_type) LIKE '%diesel%' THEN 'Diesel'
  WHEN lower(fuel_type) LIKE '%gas%' OR lower(fuel_type) LIKE '%petrol%' THEN 'Gasoline'
  ELSE NULL
END;
"""


def upgrade() -> None:
    op.execute(_BACKFILL_TRANSMISSION)
    op.execute(_BACKFILL_FUEL)
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_vehicle_asset_sync_listing ON vehicle_asset;

        CREATE TYPE transmission_type AS ENUM ('AUTOMATIC', 'MANUAL');
        CREATE TYPE fuel_type_enum AS ENUM ('Gasoline', 'Electric', 'Hybrid', 'Diesel');

        ALTER TABLE vehicle_asset
          ALTER COLUMN transmission TYPE transmission_type
          USING transmission::transmission_type,
          ALTER COLUMN fuel_type TYPE fuel_type_enum
          USING fuel_type::fuel_type_enum;

        ALTER TABLE vehicle_listing
          ALTER COLUMN transmission TYPE transmission_type
          USING transmission::transmission_type,
          ALTER COLUMN fuel_type TYPE fuel_type_enum
          USING fuel_type::fuel_type_enum;

        CREATE TRIGGER trg_vehicle_asset_sync_listing
        AFTER INSERT OR UPDATE OF
          make, model, model_year, vin, fuel_type, transmission, seats, body_type_id
        ON vehicle_asset
        FOR EACH ROW
        EXECUTE FUNCTION trg_sync_listing_cache_from_asset();

        CREATE INDEX idx_vehicle_listing_price_active
          ON vehicle_listing(price_per_day)
          WHERE COALESCE(status, 'ACTIVE') = 'ACTIVE';

        CREATE INDEX idx_vehicle_asset_body_type ON vehicle_asset(body_type_id);
        CREATE INDEX idx_vehicle_asset_transmission ON vehicle_asset(transmission);
        CREATE INDEX idx_vehicle_asset_fuel_type ON vehicle_asset(fuel_type);
        CREATE INDEX idx_vehicle_asset_seats ON vehicle_asset(seats);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS idx_vehicle_asset_seats;
        DROP INDEX IF EXISTS idx_vehicle_asset_fuel_type;
        DROP INDEX IF EXISTS idx_vehicle_asset_transmission;
        DROP INDEX IF EXISTS idx_vehicle_asset_body_type;
        DROP INDEX IF EXISTS idx_vehicle_listing_price_active;

        DROP TRIGGER IF EXISTS trg_vehicle_asset_sync_listing ON vehicle_asset;

        ALTER TABLE vehicle_listing
          ALTER COLUMN transmission TYPE VARCHAR(30)
          USING transmission::text,
          ALTER COLUMN fuel_type TYPE VARCHAR(30)
          USING fuel_type::text;

        ALTER TABLE vehicle_asset
          ALTER COLUMN transmission TYPE VARCHAR(30)
          USING transmission::text,
          ALTER COLUMN fuel_type TYPE VARCHAR(30)
          USING fuel_type::text;

        DROP TYPE IF EXISTS fuel_type_enum;
        DROP TYPE IF EXISTS transmission_type;

        CREATE TRIGGER trg_vehicle_asset_sync_listing
        AFTER INSERT OR UPDATE OF
          make, model, model_year, vin, fuel_type, transmission, seats, body_type_id
        ON vehicle_asset
        FOR EACH ROW
        EXECUTE FUNCTION trg_sync_listing_cache_from_asset();
        """
    )
