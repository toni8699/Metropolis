-- Migration 010: Deprecate legacy corporate booking tables.
-- Marketplace booking is the single source of truth for fleet availability.

BEGIN;

-- Remove bridge column added in 009 before dropping reservation.
ALTER TABLE booking
  DROP CONSTRAINT IF EXISTS booking_legacy_reservation_id_fkey;

DROP INDEX IF EXISTS idx_booking_legacy_reservation_id;

ALTER TABLE booking
  DROP COLUMN IF EXISTS legacy_reservation_id;

-- Drop child tables first (FK order).
DROP TABLE IF EXISTS agreement CASCADE;
DROP TABLE IF EXISTS rentalperiod CASCADE;
DROP TABLE IF EXISTS reservation CASCADE;
DROP TABLE IF EXISTS customer CASCADE;

COMMIT;
