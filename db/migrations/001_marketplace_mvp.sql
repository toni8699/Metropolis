DO $$
BEGIN
  CREATE TYPE user_role AS ENUM ('RENTER', 'OWNER', 'ADMIN');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE listing_source_type AS ENUM ('OWNER', 'FLEET');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE booking_status AS ENUM ('PENDING', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE availability_status AS ENUM ('AVAILABLE', 'BLOCKED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS app_user
(
  user_id BIGSERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role user_role NOT NULL DEFAULT 'RENTER',
  full_name VARCHAR(150),
  phone VARCHAR(32),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS owner_profile
(
  user_id BIGINT PRIMARY KEY REFERENCES app_user(user_id) ON DELETE CASCADE,
  verification_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
  payout_ref TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vehicle_listing
(
  listing_id BIGSERIAL PRIMARY KEY,
  owner_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
  fleet_vehicle_vin CHAR(17) REFERENCES Vehicle(vin) ON DELETE SET NULL,
  source_type listing_source_type NOT NULL,
  title VARCHAR(120) NOT NULL,
  brand VARCHAR(80),
  make VARCHAR(80),
  model VARCHAR(80),
  year INT,
  description TEXT,
  rules TEXT,
  pickup_notes_template TEXT,
  price_per_day DECIMAL(10,2) NOT NULL CHECK (price_per_day >= 0),
  photos_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (
    (source_type = 'OWNER' AND owner_user_id IS NOT NULL AND fleet_vehicle_vin IS NULL) OR
    (source_type = 'FLEET' AND fleet_vehicle_vin IS NOT NULL)
  )
);

CREATE TABLE IF NOT EXISTS listing_location
(
  listing_id BIGINT PRIMARY KEY REFERENCES vehicle_listing(listing_id) ON DELETE CASCADE,
  lat DECIMAL(9,6) NOT NULL,
  lng DECIMAL(9,6) NOT NULL,
  geohash VARCHAR(20),
  city_zone VARCHAR(64) NOT NULL,
  last_parked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (lat BETWEEN -90 AND 90),
  CHECK (lng BETWEEN -180 AND 180)
);

CREATE INDEX IF NOT EXISTS idx_listing_location_city_zone ON listing_location(city_zone);
CREATE INDEX IF NOT EXISTS idx_listing_location_geohash ON listing_location(geohash);

CREATE TABLE IF NOT EXISTS listing_availability
(
  availability_id BIGSERIAL PRIMARY KEY,
  listing_id BIGINT NOT NULL REFERENCES vehicle_listing(listing_id) ON DELETE CASCADE,
  start_at TIMESTAMPTZ NOT NULL,
  end_at TIMESTAMPTZ NOT NULL,
  status availability_status NOT NULL DEFAULT 'AVAILABLE',
  CHECK (end_at > start_at)
);

CREATE INDEX IF NOT EXISTS idx_listing_availability_listing_window ON listing_availability(listing_id, start_at, end_at);

CREATE TABLE IF NOT EXISTS booking
(
  booking_id BIGSERIAL PRIMARY KEY,
  listing_id BIGINT NOT NULL REFERENCES vehicle_listing(listing_id) ON DELETE CASCADE,
  renter_user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  start_at TIMESTAMPTZ NOT NULL,
  end_at TIMESTAMPTZ NOT NULL,
  status booking_status NOT NULL DEFAULT 'PENDING',
  price_snapshot_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (end_at > start_at)
);

CREATE INDEX IF NOT EXISTS idx_booking_listing_window ON booking(listing_id, start_at, end_at);
CREATE INDEX IF NOT EXISTS idx_booking_renter ON booking(renter_user_id);

CREATE TABLE IF NOT EXISTS booking_instruction
(
  instruction_id BIGSERIAL PRIMARY KEY,
  booking_id BIGINT NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
  owner_user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  message TEXT NOT NULL,
  sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  read_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS trip_event
(
  event_id BIGSERIAL PRIMARY KEY,
  booking_id BIGINT NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
  event_type VARCHAR(50) NOT NULL,
  actor_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
  event_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_trip_event_booking ON trip_event(booking_id, event_at);
