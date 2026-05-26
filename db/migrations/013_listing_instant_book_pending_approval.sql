-- Per-listing instant book toggle + booking status for host approval queue.

ALTER TABLE vehicle_listing
  ADD COLUMN IF NOT EXISTS instant_book BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TYPE booking_status ADD VALUE IF NOT EXISTS 'PENDING_APPROVAL';
