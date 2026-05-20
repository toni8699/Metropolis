-- Reset data for Toronto-only launch while preserving schema for future expansion.
-- Safe to run multiple times.

DO $$
DECLARE
  target_tables text[] := ARRAY[
    'trip_event',
    'booking_instruction',
    'booking',
    'listing_availability',
    'listing_location',
    'vehicle_listing',
    'file_asset',
    'owner_profile',
    'company_parking_spot',
    'app_user',
    'agreement',
    'rentalperiod',
    'reservation',
    'customer',
    'relocation',
    'branchmanager',
    'employee',
    'vehicle',
    'branch',
    'vehicleclass',
    'area',
    'region'
  ];
  truncate_sql text;
BEGIN
  SELECT
    'TRUNCATE TABLE '
    || string_agg(format('public.%I', tbl), ', ')
    || ' RESTART IDENTITY CASCADE'
  INTO truncate_sql
  FROM unnest(target_tables) AS tbl
  WHERE to_regclass(format('public.%s', tbl)) IS NOT NULL;

  IF truncate_sql IS NOT NULL THEN
    EXECUTE truncate_sql;
  END IF;
END $$;

-- Legacy fleet core entities (Toronto only).
INSERT INTO area (areaid, areaname)
VALUES (1, 'Toronto');

INSERT INTO vehicleclass (classid, classname, securitydeposit)
VALUES
  (10, 'Economy', 100.00),
  (11, 'Compact', 150.00),
  (12, 'SUV', 250.00),
  (13, 'Truck', 300.00);

INSERT INTO branch (branchid, address, phone_number, city, areaid, managerid, lat, lng)
VALUES
  (100, '200 King St W, Toronto, ON M5H 3T4', '416-555-0101', 'Toronto', 1, NULL, 43.648690, -79.380260),
  (101, '1200 Sheppard Ave E, Toronto, ON M2K 2S5', '416-555-0142', 'Toronto', 1, NULL, 43.762420, -79.337470),
  (102, '205 Queens Quay W, Toronto, ON M5J 2Y7', '416-555-0188', 'Toronto', 1, NULL, 43.638450, -79.380930);

INSERT INTO employee (eid, name, salary, branchid, supervisorid)
VALUES
  (200, 'Ava Toronto', 60000, 100, NULL),
  (201, 'Liam Toronto', 54000, 100, 200),
  (202, 'Noah Toronto', 61000, 101, NULL),
  (203, 'Emma Toronto', 53000, 101, 202);

INSERT INTO branchmanager (eid, branchid)
VALUES
  (200, 100),
  (202, 101);

UPDATE branch SET managerid = 200 WHERE branchid = 100;
UPDATE branch SET managerid = 202 WHERE branchid = 101;

INSERT INTO vehicle (vin, license_plate, mileage, model, status, make, classid, branchid)
VALUES
  ('TORONTO0000000001', 'TOR100', 18000, 'Corolla', 'Available', 'Toyota', 10, 100),
  ('TORONTO0000000002', 'TOR101', 22000, 'Civic', 'Available', 'Honda', 10, 100),
  ('TORONTO0000000003', 'TOR102', 26000, 'Rogue', 'Available', 'Nissan', 12, 100),
  ('TORONTO0000000004', 'TOR103', 19500, 'Camry', 'Available', 'Toyota', 11, 101),
  ('TORONTO0000000005', 'TOR104', 30000, 'CX-5', 'Maintenance', 'Mazda', 12, 101),
  ('TORONTO0000000006', 'TOR105', 28000, 'F-150', 'Available', 'Ford', 13, 101);

INSERT INTO company_parking_spot (name, area_id, branch_id, address, lat, lng, city_zone, is_active)
VALUES
  ('Liberty Village Lot A', 1, 100, '34 Hanna Ave, Toronto, ON M6K 0C3', 43.640980, -79.423510, 'toronto-liberty-village', TRUE),
  ('Distillery District Spot', 1, 100, '55 Mill St, Toronto, ON M5A 3C4', 43.650290, -79.359580, 'toronto-distillery-district', TRUE),
  ('North York Centre Parking', 1, 101, '5050 Yonge St, North York, ON M2N 5P2', 43.769100, -79.414800, 'toronto-north-york-centre', TRUE),
  ('Harbourfront Underground', 1, 102, '235 Queens Quay W, Toronto, ON M5J 2G8', 43.637420, -79.384360, 'toronto-harbourfront', TRUE),
  ('Leslieville Reserved Bay', 1, NULL, '935 Queen St E, Toronto, ON M4M 1J7', 43.660970, -79.338210, 'toronto-leslieville', TRUE);

-- Keep expansion-ready region model if table exists.
DO $$
BEGIN
  IF to_regclass('public.region') IS NOT NULL THEN
    INSERT INTO region (code, display_name, country_code, is_active)
    VALUES ('toronto', 'Toronto', 'CA', TRUE)
    ON CONFLICT (code) DO UPDATE
    SET display_name = EXCLUDED.display_name,
        country_code = EXCLUDED.country_code,
        is_active = EXCLUDED.is_active;
  END IF;
END $$;
