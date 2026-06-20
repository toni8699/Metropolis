"""Vehicle realignment: ref_body_type, vin metadata, asset SoT, listing cache sync.

Revision ID: 000003_vehicle_realignment
Revises: 000002_email_verification
Create Date: 2026-06-19
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000003_vehicle_realignment"
down_revision: str | None = "000002_email_verification"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE ref_body_type (
          body_type_id SERIAL PRIMARY KEY,
          code VARCHAR(40) NOT NULL UNIQUE,
          display_name VARCHAR(80) NOT NULL,
          sort_order INT NOT NULL DEFAULT 0
        );

        INSERT INTO ref_body_type (code, display_name, sort_order) VALUES
          ('SEDAN', 'Sedan', 10),
          ('SUV', 'SUV', 20),
          ('TRUCK', 'Truck', 30),
          ('EV', 'Electric', 40),
          ('MINIVAN', 'Minivan', 50),
          ('COUPE', 'Coupe', 60),
          ('WAGON', 'Wagon', 70);

        CREATE TABLE ref_nhtsa_body_class_map (
          map_id SERIAL PRIMARY KEY,
          nhtsa_body_class VARCHAR(120) NOT NULL UNIQUE,
          body_type_id INT NOT NULL REFERENCES ref_body_type(body_type_id)
        );

        INSERT INTO ref_nhtsa_body_class_map (nhtsa_body_class, body_type_id)
        SELECT v.nhtsa_body_class, bt.body_type_id
        FROM (VALUES
          ('SEDAN', 'SEDAN'),
          ('SEDAN/SA', 'SEDAN'),
          ('SPORT UTILITY VEHICLE (SUV)/MULTI-PURPOSE VEHICLE (MPV)', 'SUV'),
          ('SPORT UTILITY VEHICLE', 'SUV'),
          ('MULTI-PURPOSE VEHICLE (MPV)', 'MINIVAN'),
          ('MPV', 'MINIVAN'),
          ('PICKUP', 'TRUCK'),
          ('TRUCK', 'TRUCK'),
          ('COUPE', 'COUPE'),
          ('WAGON', 'WAGON'),
          ('HATCHBACK', 'SEDAN'),
          ('CONVERTIBLE', 'COUPE'),
          ('CROSSOVER UTILITY VEHICLE (CUV)', 'SUV')
        ) AS v(nhtsa_body_class, code)
        JOIN ref_body_type bt ON bt.code = v.code;

        ALTER TABLE vehicle_asset
          ADD COLUMN IF NOT EXISTS body_type_id INT REFERENCES ref_body_type(body_type_id),
          ADD COLUMN IF NOT EXISTS fuel_type VARCHAR(30),
          ADD COLUMN IF NOT EXISTS transmission VARCHAR(30),
          ADD COLUMN IF NOT EXISTS seats INT CHECK (seats IS NULL OR seats > 0);

        ALTER TABLE vehicle_listing
          ADD COLUMN IF NOT EXISTS listing_title VARCHAR(120);

        UPDATE vehicle_listing
        SET listing_title = title
        WHERE listing_title IS NULL;

        UPDATE vehicle_asset va
        SET
          make = COALESCE(va.make, vl.make),
          model = COALESCE(va.model, vl.model),
          model_year = COALESCE(va.model_year, vl.year),
          odometer_km = COALESCE(va.odometer_km, vl.mileage),
          transmission = COALESCE(va.transmission, vl.transmission),
          fuel_type = COALESCE(va.fuel_type, vl.fuel_type),
          seats = COALESCE(va.seats, vl.seats)
        FROM vehicle_listing vl
        WHERE vl.vehicle_id = va.vehicle_id;

        UPDATE vehicle_asset va
        SET body_type_id = bt.body_type_id
        FROM vehicle_listing vl
        JOIN ref_body_type bt ON bt.display_name = TRIM(
          SUBSTRING(vl.description FROM 'Vehicle type: (.+)$')
        )
        WHERE vl.vehicle_id = va.vehicle_id
          AND vl.description ~ '^Vehicle type: '
          AND va.body_type_id IS NULL;

        UPDATE vehicle_listing
        SET description = NULLIF(
          TRIM(REGEXP_REPLACE(description, '^Vehicle type: [^\\n]+\\s*', '')),
          ''
        )
        WHERE description ~ '^Vehicle type: ';

        CREATE TABLE vehicle_vin_metadata (
          metadata_id BIGSERIAL PRIMARY KEY,
          vehicle_id BIGINT NOT NULL UNIQUE REFERENCES vehicle_asset(vehicle_id) ON DELETE CASCADE,
          vin VARCHAR(17) NOT NULL,
          decoded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          nhtsa_response JSONB NOT NULL,
          decode_source VARCHAR(32) NOT NULL DEFAULT 'NHTSA_VPIC',
          CONSTRAINT vehicle_vin_metadata_vin_len_check CHECK (
            char_length(vin) BETWEEN 11 AND 17
          )
        );

        CREATE INDEX idx_vehicle_vin_metadata_vin ON vehicle_vin_metadata(vin);

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

        DROP TRIGGER IF EXISTS trg_vehicle_asset_sync_listing ON vehicle_asset;
        CREATE TRIGGER trg_vehicle_asset_sync_listing
        AFTER INSERT OR UPDATE OF
          make, model, model_year, vin, fuel_type, transmission, seats, odometer_km, body_type_id
        ON vehicle_asset
        FOR EACH ROW
        EXECUTE FUNCTION trg_sync_listing_cache_from_asset();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_vehicle_asset_sync_listing ON vehicle_asset;
        DROP FUNCTION IF EXISTS trg_sync_listing_cache_from_asset();
        DROP FUNCTION IF EXISTS sync_listing_cache_from_asset(BIGINT);
        DROP TABLE IF EXISTS vehicle_vin_metadata;
        ALTER TABLE vehicle_listing DROP COLUMN IF EXISTS listing_title;
        ALTER TABLE vehicle_asset
          DROP COLUMN IF EXISTS seats,
          DROP COLUMN IF EXISTS transmission,
          DROP COLUMN IF EXISTS fuel_type,
          DROP COLUMN IF EXISTS body_type_id;
        DROP TABLE IF EXISTS ref_nhtsa_body_class_map;
        DROP TABLE IF EXISTS ref_body_type;
        """
    )
