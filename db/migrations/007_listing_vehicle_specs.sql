-- Add explicit listing vehicle specs for admin creation flow.

ALTER TABLE vehicle_listing
  ADD COLUMN IF NOT EXISTS mileage INT,
  ADD COLUMN IF NOT EXISTS vehicle_class_id INT;

DO $$
BEGIN
  IF to_regclass('public.vehicleclass') IS NOT NULL THEN
    ALTER TABLE vehicle_listing
      DROP CONSTRAINT IF EXISTS vehicle_listing_vehicle_class_id_fkey;
    ALTER TABLE vehicle_listing
      ADD CONSTRAINT vehicle_listing_vehicle_class_id_fkey
      FOREIGN KEY (vehicle_class_id) REFERENCES vehicleclass(classid) ON DELETE SET NULL;
  END IF;
END
$$;

ALTER TABLE vehicle_listing
  DROP CONSTRAINT IF EXISTS vehicle_listing_mileage_check;

ALTER TABLE vehicle_listing
  ADD CONSTRAINT vehicle_listing_mileage_check
  CHECK (mileage IS NULL OR mileage >= 0);

DO $$
BEGIN
  IF to_regclass('public.vehicle') IS NOT NULL THEN
    UPDATE vehicle_listing l
    SET
      mileage = v.mileage,
      vehicle_class_id = v.classid
    FROM vehicle v
    WHERE l.fleet_vehicle_vin = v.vin
      AND (l.mileage IS NULL OR l.vehicle_class_id IS NULL);
  END IF;
END
$$;
