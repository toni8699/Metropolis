-- Rich listing details for Turo/Airbnb-like metadata.

ALTER TABLE vehicle_listing
  ADD COLUMN IF NOT EXISTS guidelines TEXT,
  ADD COLUMN IF NOT EXISTS transmission VARCHAR(30),
  ADD COLUMN IF NOT EXISTS fuel_type VARCHAR(30),
  ADD COLUMN IF NOT EXISTS seats INT,
  ADD COLUMN IF NOT EXISTS doors INT,
  ADD COLUMN IF NOT EXISTS features JSONB,
  ADD COLUMN IF NOT EXISTS images JSONB,
  ADD COLUMN IF NOT EXISTS address VARCHAR(255),
  ADD COLUMN IF NOT EXISTS latitude DECIMAL(9,6),
  ADD COLUMN IF NOT EXISTS longitude DECIMAL(9,6);

ALTER TABLE vehicle_listing
  DROP CONSTRAINT IF EXISTS vehicle_listing_seats_check;
ALTER TABLE vehicle_listing
  ADD CONSTRAINT vehicle_listing_seats_check CHECK (seats IS NULL OR seats > 0);

ALTER TABLE vehicle_listing
  DROP CONSTRAINT IF EXISTS vehicle_listing_doors_check;
ALTER TABLE vehicle_listing
  ADD CONSTRAINT vehicle_listing_doors_check CHECK (doors IS NULL OR doors > 0);

UPDATE vehicle_listing
SET guidelines = rules
WHERE guidelines IS NULL AND rules IS NOT NULL;

UPDATE vehicle_listing
SET images = photos_json
WHERE images IS NULL AND photos_json IS NOT NULL;

UPDATE vehicle_listing
SET address = pickup_address
WHERE address IS NULL AND pickup_address IS NOT NULL;

UPDATE vehicle_listing l
SET
  latitude = loc.lat,
  longitude = loc.lng
FROM listing_location loc
WHERE l.listing_id = loc.listing_id
  AND (l.latitude IS NULL OR l.longitude IS NULL);
