-- Metropolis rental schema (PostgreSQL / Neon)
-- Reference snapshot of the base schema. Incremental changes: Alembic (backend/alembic).
-- When adding tables/columns via Alembic, update this file to match the final state.

CREATE TABLE Area
(
  areaID INT NOT NULL PRIMARY KEY,
  areaName VARCHAR(100) NOT NULL
);

CREATE TABLE Branch
(
  branchID INT NOT NULL PRIMARY KEY,
  address VARCHAR(200),
  phone_number VARCHAR(20),
  city VARCHAR(100),
  areaID INT NOT NULL,
  FOREIGN KEY (areaID) REFERENCES Area(areaID)
);

-- Marketplace + auth extension (single-city launch schema)

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
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE owner_profile
(
  user_id BIGINT PRIMARY KEY REFERENCES app_user(user_id) ON DELETE CASCADE,
  verification_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
  payout_ref TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE vehicle_listing
(
  listing_id BIGSERIAL PRIMARY KEY,
  owner_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
  fleet_vehicle_vin CHAR(17),
  source_type listing_source_type NOT NULL,
  title VARCHAR(120) NOT NULL,
  make VARCHAR(80),
  model VARCHAR(80),
  year INT,
  description TEXT,
  rules TEXT,
  pickup_notes_template TEXT,
  price_per_day DECIMAL(10,2) NOT NULL CHECK (price_per_day >= 0),
  photos_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
  instant_book BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT vehicle_listing_status_active_consistency CHECK (
    (status = 'ACTIVE' AND active = TRUE)
    OR (status = 'INACTIVE' AND active = FALSE)
  ),
  CHECK (
    (source_type = 'OWNER' AND owner_user_id IS NOT NULL AND fleet_vehicle_vin IS NULL) OR
    (source_type = 'FLEET' AND fleet_vehicle_vin IS NOT NULL)
  )
);

CREATE TABLE listing_location
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

CREATE INDEX idx_listing_availability_listing_window ON listing_availability(listing_id, start_at, end_at);

CREATE TABLE booking
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

CREATE INDEX idx_booking_listing_window ON booking(listing_id, start_at, end_at);
CREATE INDEX idx_booking_renter ON booking(renter_user_id);

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

-- Canonical vehicle asset foundation (post-baseline revamp phase 1)

CREATE TYPE vehicle_category AS ENUM ('STANDARD', 'LUXURY', 'TRUCK', 'EV');
CREATE TYPE vehicle_owner_type AS ENUM ('INDEPENDENT_HOST', 'FLEET_OWNER', 'COMPANY');
CREATE TYPE vehicle_asset_status AS ENUM ('ONBOARDING', 'ACTIVE', 'MAINTENANCE', 'RETIRED');
CREATE TYPE listing_visibility_status AS ENUM ('DRAFT', 'PUBLISHED', 'HIDDEN');
CREATE TYPE management_assignment_status AS ENUM ('PENDING', 'ACTIVE', 'TERMINATED');
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

CREATE TABLE vehicle_asset
(
  vehicle_id BIGSERIAL PRIMARY KEY,
  vin VARCHAR(17) UNIQUE,
  vehicle_category vehicle_category NOT NULL DEFAULT 'STANDARD',
  estimated_value DECIMAL(12,2) CHECK (estimated_value IS NULL OR estimated_value >= 0),
  owner_type vehicle_owner_type NOT NULL,
  owner_party_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
  owner_party_name VARCHAR(160),
  asset_status vehicle_asset_status NOT NULL DEFAULT 'ONBOARDING',
  make VARCHAR(80),
  model VARCHAR(80),
  model_year INT,
  branch_id INT REFERENCES branch(branchid) ON DELETE SET NULL,
  odometer_km INT CHECK (odometer_km IS NULL OR odometer_km >= 0),
  fleet_status VARCHAR(30),
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

CREATE INDEX idx_vehicle_mgmt_assignment_vehicle ON vehicle_management_assignment(vehicle_id, status);

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

ALTER TABLE vehicle_listing
  ADD COLUMN vehicle_id BIGINT REFERENCES vehicle_asset(vehicle_id) ON DELETE SET NULL,
  ADD COLUMN visibility_status listing_visibility_status NOT NULL DEFAULT 'PUBLISHED';

CREATE INDEX idx_vehicle_listing_vehicle_id ON vehicle_listing(vehicle_id);
CREATE INDEX idx_vehicle_listing_fleet_vin ON vehicle_listing(fleet_vehicle_vin);

ALTER TABLE booking
  ADD COLUMN access_type booking_access_type NOT NULL DEFAULT 'DAILY_RENTAL';
