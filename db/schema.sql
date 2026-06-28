-- Metropolis rental schema (PostgreSQL / Neon)
-- Canonical snapshot of the full live schema.
-- Fresh database: `alembic upgrade head` (runs this file once when empty).
-- After any Alembic revision, update this file to match the final state.

-- ---------------------------------------------------------------------------
-- Legacy corporate geography
-- ---------------------------------------------------------------------------

CREATE TABLE area
(
  areaid INT NOT NULL PRIMARY KEY,
  areaname VARCHAR(100) NOT NULL
);

CREATE TABLE branch
(
  branchid INT NOT NULL PRIMARY KEY,
  address VARCHAR(200),
  phone_number VARCHAR(20),
  city VARCHAR(100),
  areaid INT NOT NULL,
  lat DECIMAL(9,6),
  lng DECIMAL(9,6),
  FOREIGN KEY (areaid) REFERENCES area(areaid)
);

-- ---------------------------------------------------------------------------
-- Enums
-- ---------------------------------------------------------------------------

CREATE TYPE user_role AS ENUM ('RENTER', 'OWNER', 'ADMIN');
CREATE TYPE listing_source_type AS ENUM ('OWNER', 'FLEET');
CREATE TYPE booking_status AS ENUM (
  'PENDING',
  'PENDING_APPROVAL',
  'CONFIRMED',
  'IN_PROGRESS',
  'COMPLETED',
  'CANCELLED'
);
CREATE TYPE availability_status AS ENUM ('AVAILABLE', 'BLOCKED');
CREATE TYPE review_target_type AS ENUM ('LISTING', 'RENTER');
CREATE TYPE vehicle_category AS ENUM ('STANDARD', 'LUXURY', 'TRUCK', 'EV');
CREATE TYPE vehicle_owner_type AS ENUM ('INDEPENDENT_HOST', 'FLEET_OWNER', 'COMPANY');
CREATE TYPE vehicle_asset_status AS ENUM ('ONBOARDING', 'ACTIVE', 'MAINTENANCE', 'RETIRED');
CREATE TYPE management_assignment_status AS ENUM ('PENDING', 'ACTIVE', 'TERMINATED');
CREATE TYPE transmission_type AS ENUM ('AUTOMATIC', 'MANUAL');
CREATE TYPE fuel_type_enum AS ENUM ('Gasoline', 'Electric', 'Hybrid', 'Diesel');
CREATE TYPE compliance_event_type AS ENUM (
  'PHYSICAL_INSPECTION',
  'DOCUMENT_VERIFICATION',
  'SAFETY_RUN',
  'WEIGHT_TOW_VERIFICATION'
);
CREATE TYPE compliance_result AS ENUM ('PASSED', 'FAILED');
CREATE TYPE insurance_coverage_type AS ENUM ('HOST_PERSONAL', 'PLATFORM_FLEET', 'TRIP_COMMERCIAL');
CREATE TYPE parking_provider_type AS ENUM ('PLATFORM_OWNED', 'PARTNER', 'HOST_PROVIDED');
CREATE TYPE booking_access_type AS ENUM ('DAILY_RENTAL', 'MEMBERSHIP');

-- ---------------------------------------------------------------------------
-- Identity
-- ---------------------------------------------------------------------------

CREATE TABLE app_user
(
  user_id BIGSERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role user_role NOT NULL DEFAULT 'RENTER',
  full_name VARCHAR(150),
  phone VARCHAR(32),
  profile_photo_url TEXT,
  lives VARCHAR(100),
  about TEXT,
  languages VARCHAR(150),
  work VARCHAR(100),
  is_approved_to_drive BOOLEAN NOT NULL DEFAULT FALSE,
  is_admin BOOLEAN NOT NULL DEFAULT FALSE,
  is_verified BOOLEAN NOT NULL DEFAULT FALSE,
  verification_token TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE owner_profile
(
  user_id BIGINT PRIMARY KEY REFERENCES app_user(user_id) ON DELETE CASCADE,
  verification_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
  payout_ref TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- Media + regions
-- ---------------------------------------------------------------------------

CREATE TABLE region
(
  region_id BIGSERIAL PRIMARY KEY,
  code VARCHAR(64) NOT NULL UNIQUE,
  display_name VARCHAR(128) NOT NULL,
  country_code CHAR(2) NOT NULL DEFAULT 'CA',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE file_asset
(
  file_id BIGSERIAL PRIMARY KEY,
  owner_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
  listing_id BIGINT,
  booking_id BIGINT,
  bucket VARCHAR(128) NOT NULL,
  object_key TEXT NOT NULL UNIQUE,
  file_url TEXT NOT NULL,
  content_type VARCHAR(255),
  size_bytes BIGINT CHECK (size_bytes IS NULL OR size_bytes >= 0),
  scope VARCHAR(32) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT file_asset_scope_check
    CHECK (scope IN ('FLEET', 'OWNER_LISTING', 'USER_DOC', 'USER_AVATAR', 'TRIP_INSPECTION'))
);

CREATE INDEX idx_file_asset_listing ON file_asset(listing_id, created_at DESC);
CREATE INDEX idx_file_asset_owner ON file_asset(owner_user_id, created_at DESC);
CREATE INDEX idx_file_asset_booking ON file_asset(booking_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- Vehicle reference data
-- ---------------------------------------------------------------------------

CREATE TABLE ref_body_type
(
  body_type_id SERIAL PRIMARY KEY,
  code VARCHAR(40) NOT NULL UNIQUE,
  display_name VARCHAR(80) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0
);

CREATE TABLE ref_nhtsa_body_class_map
(
  map_id SERIAL PRIMARY KEY,
  nhtsa_body_class VARCHAR(120) NOT NULL UNIQUE,
  body_type_id INT NOT NULL REFERENCES ref_body_type(body_type_id)
);

CREATE TABLE ref_feature
(
  feature_id SERIAL PRIMARY KEY,
  code VARCHAR(64) NOT NULL UNIQUE,
  name VARCHAR(120) NOT NULL UNIQUE,
  icon_key VARCHAR(64) NOT NULL DEFAULT 'Check',
  category VARCHAR(32) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------------
-- Vehicle assets
-- ---------------------------------------------------------------------------

CREATE TABLE vehicle_asset
(
  vehicle_id BIGSERIAL PRIMARY KEY,
  vin VARCHAR(17) UNIQUE,
  vehicle_category vehicle_category NOT NULL DEFAULT 'STANDARD',
  body_type_id INT REFERENCES ref_body_type(body_type_id),
  body_type_other VARCHAR(80),
  estimated_value DECIMAL(12,2) CHECK (estimated_value IS NULL OR estimated_value >= 0),
  owner_type vehicle_owner_type NOT NULL,
  owner_party_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
  owner_party_name VARCHAR(160),
  asset_status vehicle_asset_status NOT NULL DEFAULT 'ONBOARDING',
  make VARCHAR(80),
  model VARCHAR(80),
  model_year INT,
  fuel_type fuel_type_enum,
  transmission transmission_type,
  seats INT CHECK (seats IS NULL OR seats > 0),
  branch_id INT REFERENCES branch(branchid) ON DELETE SET NULL,
  fleet_status VARCHAR(30),
  is_vin_verified BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT vehicle_asset_owner_identity_check CHECK (
    owner_party_user_id IS NOT NULL OR owner_party_name IS NOT NULL
  ),
  CONSTRAINT vehicle_asset_vin_len_check CHECK (
    vin IS NULL OR char_length(vin) BETWEEN 11 AND 17
  )
);

CREATE INDEX idx_vehicle_asset_owner ON vehicle_asset(owner_type, owner_party_user_id);
CREATE INDEX idx_vehicle_asset_status ON vehicle_asset(asset_status);
CREATE INDEX idx_vehicle_asset_fleet_branch_status ON vehicle_asset(branch_id, fleet_status);
CREATE INDEX idx_vehicle_asset_body_type ON vehicle_asset(body_type_id);
CREATE INDEX idx_vehicle_asset_transmission ON vehicle_asset(transmission);
CREATE INDEX idx_vehicle_asset_fuel_type ON vehicle_asset(fuel_type);
CREATE INDEX idx_vehicle_asset_seats ON vehicle_asset(seats);

CREATE TABLE vehicle_vin_metadata
(
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
AFTER INSERT OR UPDATE OF make, model, model_year, vin, fuel_type, transmission, seats, body_type_id
ON vehicle_asset
FOR EACH ROW
EXECUTE FUNCTION trg_sync_listing_cache_from_asset();

-- ---------------------------------------------------------------------------
-- Company parking + marketplace listings
-- ---------------------------------------------------------------------------

CREATE TABLE company_parking_spot
(
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

CREATE INDEX idx_company_parking_spot_area ON company_parking_spot(area_id);
CREATE INDEX idx_company_parking_spot_branch ON company_parking_spot(branch_id);
CREATE INDEX idx_company_parking_spot_city_zone ON company_parking_spot(city_zone);

CREATE TABLE vehicle_listing
(
  listing_id BIGSERIAL PRIMARY KEY,
  owner_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
  created_by_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
  vehicle_id BIGINT REFERENCES vehicle_asset(vehicle_id) ON DELETE SET NULL,
  fleet_vehicle_vin CHAR(17),
  source_type listing_source_type NOT NULL,
  title VARCHAR(120) NOT NULL,
  listing_title VARCHAR(120),
  make VARCHAR(80),
  model VARCHAR(80),
  year INT,
  description TEXT,
  guidelines TEXT,
  transmission transmission_type,
  fuel_type fuel_type_enum,
  seats INT CHECK (seats IS NULL OR seats > 0),
  doors INT CHECK (doors IS NULL OR doors > 0),
  features JSONB,
  pickup_notes_template TEXT,
  price_per_day DECIMAL(10,2) NOT NULL CHECK (price_per_day >= 0),
  active BOOLEAN NOT NULL DEFAULT TRUE,
  status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
  instant_book BOOLEAN NOT NULL DEFAULT TRUE,
  is_company_owned BOOLEAN NOT NULL DEFAULT FALSE,
  location_source_type VARCHAR(20),
  branch_id INT REFERENCES branch(branchid) ON DELETE SET NULL,
  parking_spot_id BIGINT REFERENCES company_parking_spot(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT vehicle_listing_status_active_consistency CHECK (
    (status = 'ACTIVE' AND active = TRUE)
    OR (status = 'INACTIVE' AND active = FALSE)
    OR (status = 'ARCHIVED' AND active = FALSE)
  ),
  CONSTRAINT vehicle_listing_source_check CHECK (
    (source_type = 'OWNER' AND owner_user_id IS NOT NULL AND fleet_vehicle_vin IS NULL) OR
    (source_type = 'FLEET' AND fleet_vehicle_vin IS NOT NULL)
  ),
  CONSTRAINT vehicle_listing_location_source_type_check CHECK (
    location_source_type IS NULL
    OR location_source_type IN ('BRANCH', 'PARKING_SPOT')
  ),
  CONSTRAINT vehicle_listing_single_location_source_check CHECK (
    NOT (branch_id IS NOT NULL AND parking_spot_id IS NOT NULL)
  )
);

CREATE INDEX idx_vehicle_listing_vehicle_id ON vehicle_listing(vehicle_id);
CREATE INDEX idx_vehicle_listing_fleet_vin ON vehicle_listing(fleet_vehicle_vin);
CREATE INDEX idx_vehicle_listing_owner_source ON vehicle_listing(owner_user_id, source_type);
CREATE INDEX idx_vehicle_listing_price_active
  ON vehicle_listing(price_per_day)
  WHERE COALESCE(status, 'ACTIVE') = 'ACTIVE';

ALTER TABLE file_asset
  ADD CONSTRAINT file_asset_listing_id_fkey
  FOREIGN KEY (listing_id) REFERENCES vehicle_listing(listing_id) ON DELETE CASCADE;

CREATE TABLE listing_location
(
  listing_id BIGINT PRIMARY KEY REFERENCES vehicle_listing(listing_id) ON DELETE CASCADE,
  lat DECIMAL(9,6) NOT NULL,
  lng DECIMAL(9,6) NOT NULL,
  geohash VARCHAR(20),
  city_zone VARCHAR(64) NOT NULL,
  pickup_address VARCHAR(512),
  last_parked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (lat BETWEEN -90 AND 90),
  CHECK (lng BETWEEN -180 AND 180)
);

CREATE INDEX idx_listing_location_city_zone ON listing_location(city_zone);
CREATE INDEX idx_listing_location_geohash ON listing_location(geohash);

CREATE TABLE listing_availability
(
  availability_id BIGSERIAL PRIMARY KEY,
  listing_id BIGINT NOT NULL REFERENCES vehicle_listing(listing_id) ON DELETE CASCADE,
  start_at TIMESTAMPTZ NOT NULL,
  end_at TIMESTAMPTZ NOT NULL,
  status availability_status NOT NULL DEFAULT 'AVAILABLE',
  CHECK (end_at > start_at)
);

CREATE INDEX idx_listing_availability_listing_window
  ON listing_availability(listing_id, start_at, end_at);

CREATE TABLE listing_image
(
  listing_id BIGINT NOT NULL REFERENCES vehicle_listing(listing_id) ON DELETE CASCADE,
  file_id BIGINT NOT NULL REFERENCES file_asset(file_id) ON DELETE CASCADE,
  display_order INT NOT NULL DEFAULT 0,
  PRIMARY KEY (listing_id, file_id)
);

CREATE INDEX idx_listing_image_listing_order ON listing_image(listing_id, display_order);

CREATE TABLE listing_feature
(
  listing_id BIGINT NOT NULL REFERENCES vehicle_listing(listing_id) ON DELETE CASCADE,
  feature_id INT NOT NULL REFERENCES ref_feature(feature_id) ON DELETE CASCADE,
  PRIMARY KEY (listing_id, feature_id)
);

CREATE INDEX idx_listing_feature_feature ON listing_feature(feature_id);

-- ---------------------------------------------------------------------------
-- Bookings + payments + trip lifecycle
-- ---------------------------------------------------------------------------

CREATE TABLE booking
(
  booking_id BIGSERIAL PRIMARY KEY,
  listing_id BIGINT NOT NULL REFERENCES vehicle_listing(listing_id) ON DELETE RESTRICT,
  renter_user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  start_at TIMESTAMPTZ NOT NULL,
  end_at TIMESTAMPTZ NOT NULL,
  status booking_status NOT NULL DEFAULT 'PENDING',
  access_type booking_access_type NOT NULL DEFAULT 'DAILY_RENTAL',
  price_snapshot_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  CHECK (end_at > start_at)
);

CREATE INDEX idx_booking_listing_window ON booking(listing_id, start_at, end_at);
CREATE INDEX idx_booking_completed_at ON booking(completed_at) WHERE status = 'COMPLETED';
CREATE INDEX idx_booking_renter ON booking(renter_user_id);
CREATE INDEX idx_booking_status ON booking(status);

CREATE TABLE payment
(
  payment_id BIGSERIAL PRIMARY KEY,
  booking_id BIGINT NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
  amount_cents INTEGER NOT NULL,
  currency VARCHAR(3) NOT NULL DEFAULT 'cad',
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  stripe_payment_intent_id VARCHAR(100),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_payment_booking_id ON payment(booking_id);
CREATE INDEX idx_payment_stripe_intent ON payment(stripe_payment_intent_id)
  WHERE stripe_payment_intent_id IS NOT NULL;

CREATE TABLE trip_event
(
  event_id BIGSERIAL PRIMARY KEY,
  booking_id BIGINT NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
  event_type VARCHAR(50) NOT NULL,
  actor_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
  event_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_trip_event_booking ON trip_event(booking_id, event_at);

CREATE TYPE trip_inspection_phase AS ENUM ('CHECK_IN', 'CHECK_OUT');

CREATE TABLE booking_inspection_photo
(
  photo_id            BIGSERIAL PRIMARY KEY,
  booking_id          BIGINT NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
  file_id             BIGINT NOT NULL REFERENCES file_asset(file_id) ON DELETE CASCADE,
  phase               trip_inspection_phase NOT NULL,
  angle_key           VARCHAR(64) NOT NULL,
  is_extra            BOOLEAN NOT NULL DEFAULT FALSE,
  uploaded_by_user_id BIGINT NOT NULL REFERENCES app_user(user_id),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_booking_inspection_standard_slot
  ON booking_inspection_photo (booking_id, phase, angle_key)
  WHERE is_extra = FALSE;

CREATE INDEX idx_booking_inspection_booking_phase
  ON booking_inspection_photo (booking_id, phase, created_at);

CREATE TABLE booking_message
(
  message_id BIGSERIAL PRIMARY KEY,
  booking_id BIGINT NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
  sender_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  message_text TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_booking_message_booking_created
  ON booking_message(booking_id, created_at);

CREATE TABLE booking_chat_state
(
  booking_id BIGINT NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
  user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  last_read_message_id BIGINT REFERENCES booking_message(message_id) ON DELETE SET NULL,
  last_read_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (booking_id, user_id)
);

CREATE INDEX idx_booking_chat_state_user_booking
  ON booking_chat_state(user_id, booking_id);

-- ---------------------------------------------------------------------------
-- Reviews
-- ---------------------------------------------------------------------------

CREATE TABLE review
(
  review_id BIGSERIAL PRIMARY KEY,
  booking_id BIGINT NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
  author_user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  target_type review_target_type NOT NULL,
  target_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
  target_listing_id BIGINT REFERENCES vehicle_listing(listing_id) ON DELETE CASCADE,
  rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  cleanliness INT CHECK (cleanliness IS NULL OR cleanliness BETWEEN 1 AND 5),
  accuracy INT CHECK (accuracy IS NULL OR accuracy BETWEEN 1 AND 5),
  communication INT CHECK (communication IS NULL OR communication BETWEEN 1 AND 5),
  comment TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT review_booking_author_target_unique
    UNIQUE (booking_id, author_user_id, target_type),
  CONSTRAINT review_listing_target_requires_listing CHECK (
    target_type <> 'LISTING' OR target_listing_id IS NOT NULL
  ),
  CONSTRAINT review_renter_target_requires_user CHECK (
    target_type <> 'RENTER' OR target_user_id IS NOT NULL
  )
);

CREATE INDEX idx_review_listing_target
  ON review(target_listing_id, target_type, created_at DESC);
CREATE INDEX idx_review_booking ON review(booking_id);
CREATE INDEX idx_review_target_user ON review(target_user_id, target_type);

-- ---------------------------------------------------------------------------
-- Fleet operations (future phases — schema only today)
-- ---------------------------------------------------------------------------

CREATE TABLE management_program
(
  program_id BIGSERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  commission_rate DECIMAL(5,4) NOT NULL CHECK (commission_rate >= 0 AND commission_rate <= 1),
  included_services JSONB NOT NULL DEFAULT '[]'::jsonb,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE vehicle_management_assignment
(
  assignment_id BIGSERIAL PRIMARY KEY,
  vehicle_id BIGINT NOT NULL REFERENCES vehicle_asset(vehicle_id) ON DELETE CASCADE,
  manager_party_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
  manager_party_name VARCHAR(160),
  program_id BIGINT NOT NULL REFERENCES management_program(program_id) ON DELETE RESTRICT,
  start_date DATE NOT NULL,
  end_date DATE,
  status management_assignment_status NOT NULL DEFAULT 'PENDING',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT vehicle_mgmt_assignment_dates_check CHECK (
    end_date IS NULL OR end_date >= start_date
  ),
  CONSTRAINT vehicle_mgmt_assignment_manager_check CHECK (
    manager_party_user_id IS NOT NULL OR manager_party_name IS NOT NULL
  )
);

CREATE INDEX idx_vehicle_mgmt_assignment_vehicle
  ON vehicle_management_assignment(vehicle_id, status);

CREATE TABLE vehicle_compliance_event
(
  compliance_event_id BIGSERIAL PRIMARY KEY,
  vehicle_id BIGINT NOT NULL REFERENCES vehicle_asset(vehicle_id) ON DELETE CASCADE,
  event_type compliance_event_type NOT NULL,
  result compliance_result NOT NULL,
  effective_until TIMESTAMPTZ,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  recorded_by_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL
);

CREATE INDEX idx_vehicle_compliance_vehicle_type
  ON vehicle_compliance_event(vehicle_id, event_type, recorded_at DESC);

CREATE TABLE vehicle_insurance_policy
(
  policy_id BIGSERIAL PRIMARY KEY,
  vehicle_id BIGINT NOT NULL REFERENCES vehicle_asset(vehicle_id) ON DELETE CASCADE,
  provider_name VARCHAR(120) NOT NULL,
  policy_number VARCHAR(120) NOT NULL,
  coverage_type insurance_coverage_type NOT NULL,
  effective_from TIMESTAMPTZ NOT NULL,
  effective_to TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT vehicle_insurance_dates_check CHECK (effective_to > effective_from),
  CONSTRAINT vehicle_insurance_unique_policy UNIQUE (provider_name, policy_number)
);

CREATE INDEX idx_vehicle_insurance_vehicle_dates
  ON vehicle_insurance_policy(vehicle_id, effective_from, effective_to);

CREATE TABLE parking_hub
(
  hub_id BIGSERIAL PRIMARY KEY,
  name VARCHAR(160) NOT NULL,
  latitude DECIMAL(9,6) NOT NULL CHECK (latitude BETWEEN -90 AND 90),
  longitude DECIMAL(9,6) NOT NULL CHECK (longitude BETWEEN -180 AND 180),
  provider_type parking_provider_type NOT NULL,
  area_id INT REFERENCES area(areaid) ON DELETE SET NULL,
  branch_id INT REFERENCES branch(branchid) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_parking_hub_area_branch ON parking_hub(area_id, branch_id);

CREATE TABLE parking_spot_allocation
(
  allocation_id BIGSERIAL PRIMARY KEY,
  hub_id BIGINT NOT NULL REFERENCES parking_hub(hub_id) ON DELETE CASCADE,
  vehicle_id BIGINT NOT NULL REFERENCES vehicle_asset(vehicle_id) ON DELETE CASCADE,
  spot_identifier VARCHAR(80) NOT NULL,
  valid_from TIMESTAMPTZ NOT NULL,
  valid_to TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT parking_allocation_window_check CHECK (
    valid_to IS NULL OR valid_to > valid_from
  )
);

CREATE INDEX idx_parking_allocation_vehicle_dates
  ON parking_spot_allocation(vehicle_id, valid_from, valid_to);

CREATE TABLE membership_tier
(
  tier_id BIGSERIAL PRIMARY KEY,
  code VARCHAR(40) NOT NULL UNIQUE,
  name VARCHAR(120) NOT NULL,
  rank_order INT NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE vehicle_membership_eligibility
(
  eligibility_id BIGSERIAL PRIMARY KEY,
  vehicle_id BIGINT NOT NULL REFERENCES vehicle_asset(vehicle_id) ON DELETE CASCADE,
  tier_id BIGINT NOT NULL REFERENCES membership_tier(tier_id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (vehicle_id, tier_id)
);

CREATE TABLE saved_listing
(
  user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  listing_id BIGINT NOT NULL REFERENCES vehicle_listing(listing_id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, listing_id)
);

CREATE INDEX idx_saved_listing_user_created ON saved_listing(user_id, created_at DESC);

CREATE TABLE host_payout
(
  payout_id BIGSERIAL PRIMARY KEY,
  booking_id BIGINT NOT NULL UNIQUE REFERENCES booking(booking_id) ON DELETE CASCADE,
  owner_user_id BIGINT NOT NULL REFERENCES app_user(user_id),
  amount_cents INT NOT NULL CHECK (amount_cents > 0),
  currency VARCHAR(3) NOT NULL DEFAULT 'cad',
  stripe_transfer_id VARCHAR(100),
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  failure_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_host_payout_owner_status ON host_payout(owner_user_id, status);
