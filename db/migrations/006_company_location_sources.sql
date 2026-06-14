-- Canonical company parking and branch-linked listing location sources.

ALTER TABLE branch
  ADD COLUMN IF NOT EXISTS lat DECIMAL(9,6),
  ADD COLUMN IF NOT EXISTS lng DECIMAL(9,6);

CREATE TABLE IF NOT EXISTS company_parking_spot (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  area_id INT NOT NULL REFERENCES area(areaid) ON DELETE RESTRICT,
  branch_id INT REFERENCES branch(branchid) ON DELETE SET NULL,
  address VARCHAR(255) NOT NULL,
  lat DECIMAL(9,6) NOT NULL CHECK (lat BETWEEN -90 AND 90),
  lng DECIMAL(9,6) NOT NULL CHECK (lng BETWEEN -180 AND 180),
  city_zone VARCHAR(64) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_company_parking_spot_area ON company_parking_spot(area_id);
CREATE INDEX IF NOT EXISTS idx_company_parking_spot_branch ON company_parking_spot(branch_id);
CREATE INDEX IF NOT EXISTS idx_company_parking_spot_city_zone ON company_parking_spot(city_zone);

ALTER TABLE vehicle_listing
  ADD COLUMN IF NOT EXISTS location_source_type VARCHAR(20),
  ADD COLUMN IF NOT EXISTS branch_id INT REFERENCES branch(branchid) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS parking_spot_id BIGINT REFERENCES company_parking_spot(id) ON DELETE SET NULL;

ALTER TABLE vehicle_listing
  DROP CONSTRAINT IF EXISTS vehicle_listing_location_source_type_check;

ALTER TABLE vehicle_listing
  ADD CONSTRAINT vehicle_listing_location_source_type_check
  CHECK (
    location_source_type IS NULL
    OR location_source_type IN ('BRANCH', 'PARKING_SPOT')
  );

ALTER TABLE vehicle_listing
  DROP CONSTRAINT IF EXISTS vehicle_listing_single_location_source_check;

ALTER TABLE vehicle_listing
  ADD CONSTRAINT vehicle_listing_single_location_source_check
  CHECK (
    NOT (branch_id IS NOT NULL AND parking_spot_id IS NOT NULL)
  );

DO $$
BEGIN
  IF to_regclass('public.vehicle') IS NOT NULL THEN
    UPDATE vehicle_listing l
    SET
      branch_id = v.branchid,
      location_source_type = COALESCE(l.location_source_type, 'BRANCH')
    FROM vehicle v
    WHERE l.fleet_vehicle_vin = v.vin
      AND l.branch_id IS NULL;
  END IF;
END
$$;
