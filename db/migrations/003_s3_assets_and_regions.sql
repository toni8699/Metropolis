CREATE TABLE IF NOT EXISTS region
(
  region_id BIGSERIAL PRIMARY KEY,
  code VARCHAR(64) NOT NULL UNIQUE,
  display_name VARCHAR(128) NOT NULL,
  country_code CHAR(2) NOT NULL DEFAULT 'CA',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS file_asset
(
  file_id BIGSERIAL PRIMARY KEY,
  owner_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
  listing_id BIGINT REFERENCES vehicle_listing(listing_id) ON DELETE CASCADE,
  bucket VARCHAR(128) NOT NULL,
  object_key TEXT NOT NULL UNIQUE,
  file_url TEXT NOT NULL,
  content_type VARCHAR(255),
  size_bytes BIGINT CHECK (size_bytes IS NULL OR size_bytes >= 0),
  scope VARCHAR(32) NOT NULL CHECK (scope IN ('FLEET', 'OWNER_LISTING', 'USER_DOC')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_file_asset_listing ON file_asset(listing_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_file_asset_owner ON file_asset(owner_user_id, created_at DESC);
