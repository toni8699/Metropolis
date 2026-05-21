-- Migration 009: Schema standardization and domain unification
-- Resolves dual location, redundant media JSON, legacy Customer bridge, booking link column.
-- Types match existing schema: BIGINT ids (not UUID).

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Unify legacy Customer with modern app_user
-- ---------------------------------------------------------------------------
ALTER TABLE customer
  ADD COLUMN IF NOT EXISTS user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL;

COMMENT ON COLUMN customer.user_id IS
  'Links marketplace app_user accounts to legacy Customer records for fleet operations.';

CREATE UNIQUE INDEX IF NOT EXISTS idx_customer_user_id
  ON customer(user_id)
  WHERE user_id IS NOT NULL;

-- Backfill links where emails already match
UPDATE customer c
SET user_id = u.user_id
FROM app_user u
WHERE c.user_id IS NULL
  AND lower(trim(c.email)) = lower(trim(u.email));

-- ---------------------------------------------------------------------------
-- 2. Consolidate listing location (listing_location = GIS truth)
-- ---------------------------------------------------------------------------
ALTER TABLE listing_location
  ADD COLUMN IF NOT EXISTS raw_address VARCHAR(512);

COMMENT ON COLUMN listing_location.raw_address IS
  'Human-readable pickup or billing address; coordinates stay in lat/lng.';

UPDATE listing_location ll
SET raw_address = COALESCE(
  NULLIF(trim(ll.raw_address), ''),
  NULLIF(trim(vl.address), ''),
  NULLIF(trim(vl.pickup_address), '')
)
FROM vehicle_listing vl
WHERE ll.listing_id = vl.listing_id
  AND (
    (vl.address IS NOT NULL AND trim(vl.address) <> '')
    OR (vl.pickup_address IS NOT NULL AND trim(vl.pickup_address) <> '')
  );

ALTER TABLE vehicle_listing
  DROP COLUMN IF EXISTS address,
  DROP COLUMN IF EXISTS latitude,
  DROP COLUMN IF EXISTS longitude;

-- ---------------------------------------------------------------------------
-- 3. Resolve media redundancies (file_asset + listing_image)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS listing_image (
  listing_id BIGINT NOT NULL REFERENCES vehicle_listing(listing_id) ON DELETE CASCADE,
  file_id BIGINT NOT NULL REFERENCES file_asset(file_id) ON DELETE CASCADE,
  display_order INT NOT NULL DEFAULT 0,
  PRIMARY KEY (listing_id, file_id)
);

CREATE INDEX IF NOT EXISTS idx_listing_image_listing_order
  ON listing_image(listing_id, display_order);

-- Existing S3 rows already tied to a listing
INSERT INTO listing_image (listing_id, file_id, display_order)
SELECT
  fa.listing_id,
  fa.file_id,
  (ROW_NUMBER() OVER (PARTITION BY fa.listing_id ORDER BY fa.created_at) - 1)::INT
FROM file_asset fa
WHERE fa.listing_id IS NOT NULL
ON CONFLICT (listing_id, file_id) DO NOTHING;

-- Inline JSON URLs that already have a matching file_asset row
INSERT INTO listing_image (listing_id, file_id, display_order)
SELECT
  vl.listing_id,
  fa.file_id,
  (ROW_NUMBER() OVER (
    PARTITION BY vl.listing_id
    ORDER BY fa.created_at
  ) - 1)::INT
FROM vehicle_listing vl
CROSS JOIN LATERAL (
  SELECT DISTINCT trim(url_text) AS url
  FROM jsonb_array_elements_text(
    COALESCE(vl.photos_json, '[]'::jsonb) || COALESCE(vl.images, '[]'::jsonb)
  ) AS url_text
  WHERE trim(url_text) <> ''
) AS urls
JOIN file_asset fa
  ON fa.listing_id = vl.listing_id
 AND fa.file_url = urls.url
ON CONFLICT (listing_id, file_id) DO NOTHING;

-- JSON URLs with no file_asset row: create legacy file_asset stubs, then link
WITH orphan_urls AS (
  SELECT DISTINCT
    vl.listing_id,
    urls.url
  FROM vehicle_listing vl
  CROSS JOIN LATERAL (
    SELECT DISTINCT trim(url_text) AS url
    FROM jsonb_array_elements_text(
      COALESCE(vl.photos_json, '[]'::jsonb) || COALESCE(vl.images, '[]'::jsonb)
    ) AS url_text
    WHERE trim(url_text) <> ''
  ) AS urls
  WHERE NOT EXISTS (
    SELECT 1
    FROM file_asset fa
    WHERE fa.listing_id = vl.listing_id
      AND fa.file_url = urls.url
  )
),
inserted_assets AS (
  INSERT INTO file_asset (
    listing_id,
    bucket,
    object_key,
    file_url,
    scope
  )
  SELECT
    ou.listing_id,
    'legacy-migration',
    'legacy-migration/' || ou.listing_id::TEXT || '/' || md5(ou.url),
    ou.url,
    'OWNER_LISTING'
  FROM orphan_urls ou
  ON CONFLICT (object_key) DO UPDATE
  SET listing_id = COALESCE(file_asset.listing_id, EXCLUDED.listing_id),
      file_url = EXCLUDED.file_url
  RETURNING listing_id, file_id, file_url
)
INSERT INTO listing_image (listing_id, file_id, display_order)
SELECT
  ia.listing_id,
  ia.file_id,
  0
FROM inserted_assets ia
ON CONFLICT (listing_id, file_id) DO NOTHING;

ALTER TABLE vehicle_listing
  DROP COLUMN IF EXISTS photos_json,
  DROP COLUMN IF EXISTS images;

-- ---------------------------------------------------------------------------
-- 4. Consolidate rules into guidelines
-- ---------------------------------------------------------------------------
UPDATE vehicle_listing
SET guidelines = COALESCE(NULLIF(trim(guidelines), ''), NULLIF(trim(rules), ''))
WHERE rules IS NOT NULL
  AND trim(rules) <> ''
  AND (guidelines IS NULL OR trim(guidelines) = '');

ALTER TABLE vehicle_listing
  DROP COLUMN IF EXISTS rules;

-- ---------------------------------------------------------------------------
-- 5. Marketplace booking <-> legacy reservation link
-- ---------------------------------------------------------------------------
ALTER TABLE booking
  ADD COLUMN IF NOT EXISTS legacy_reservation_id INT REFERENCES reservation(resid) ON DELETE SET NULL;

COMMENT ON COLUMN booking.legacy_reservation_id IS
  'Links marketplace bookings to legacy Reservation rows to prevent double booking.';

CREATE UNIQUE INDEX IF NOT EXISTS idx_booking_legacy_reservation_id
  ON booking(legacy_reservation_id)
  WHERE legacy_reservation_id IS NOT NULL;

COMMIT;
