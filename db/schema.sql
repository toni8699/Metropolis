-- Metropolis rental schema (PostgreSQL / Neon)
-- Reference snapshot of the base schema. Incremental changes: Alembic (backend/alembic).
-- When adding tables/columns via Alembic, update this file to match the final state.

CREATE TABLE Area
(
  areaID INT NOT NULL PRIMARY KEY,
  areaName VARCHAR(100) NOT NULL
);

CREATE TABLE VehicleClass
(
  classID INT NOT NULL PRIMARY KEY,
  className VARCHAR(100) NOT NULL,
  securityDeposit DECIMAL(10,2) NOT NULL
);

CREATE TABLE Branch
(
  branchID INT NOT NULL PRIMARY KEY,
  address VARCHAR(200),
  phone_number VARCHAR(20),
  city VARCHAR(100),
  areaID INT NOT NULL,
  managerID INT,
  FOREIGN KEY (areaID) REFERENCES Area(areaID)
);

CREATE TABLE Employee
(
  eID INT NOT NULL PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  salary DECIMAL(12,2),
  branchID INT NOT NULL,
  supervisorID INT,
  FOREIGN KEY (branchID) REFERENCES Branch(branchID),
  FOREIGN KEY (supervisorID) REFERENCES Employee(eID)
);

CREATE TABLE BranchManager
(
  eID INT NOT NULL PRIMARY KEY,
  branchID INT NOT NULL UNIQUE,
  FOREIGN KEY (eID) REFERENCES Employee(eID),
  FOREIGN KEY (branchID) REFERENCES Branch(branchID)
);

ALTER TABLE Branch
  ADD CONSTRAINT fk_branch_manager FOREIGN KEY (managerID) REFERENCES Employee(eID);

CREATE TABLE Vehicle
(
  vin CHAR(17) NOT NULL PRIMARY KEY,
  license_plate VARCHAR(20),
  mileage INT,
  model VARCHAR(100),
  status VARCHAR(30),
  make VARCHAR(50),
  classID INT NOT NULL,
  branchID INT NOT NULL,
  FOREIGN KEY (classID) REFERENCES VehicleClass(classID),
  FOREIGN KEY (branchID) REFERENCES Branch(branchID)
);

CREATE TABLE Relocation
(
  sourceAreaID INT NOT NULL,
  targetAreaID INT NOT NULL,
  fee DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (sourceAreaID, targetAreaID),
  FOREIGN KEY (sourceAreaID) REFERENCES Area(areaID),
  FOREIGN KEY (targetAreaID) REFERENCES Area(areaID),
  CHECK (sourceAreaID <> targetAreaID)
);

-- Marketplace + auth extension (single-city MVP)

CREATE TYPE user_role AS ENUM ('RENTER', 'OWNER', 'ADMIN');
CREATE TYPE listing_source_type AS ENUM ('OWNER', 'FLEET');
CREATE TYPE booking_status AS ENUM (
  'PENDING',
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

CREATE TABLE booking_instruction
(
  instruction_id BIGSERIAL PRIMARY KEY,
  booking_id BIGINT NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
  owner_user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  message TEXT NOT NULL,
  sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  read_at TIMESTAMPTZ
);

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
