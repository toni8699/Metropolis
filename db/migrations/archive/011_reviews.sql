-- Migration 011: Reviews and ratings for completed marketplace bookings.

BEGIN;

DO $$
BEGIN
  CREATE TYPE review_target_type AS ENUM ('LISTING', 'RENTER');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS review (
  review_id BIGSERIAL PRIMARY KEY,
  booking_id BIGINT NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
  author_user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  target_type review_target_type NOT NULL,
  target_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
  target_listing_id BIGINT REFERENCES vehicle_listing(listing_id) ON DELETE CASCADE,
  rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT review_booking_author_target_unique UNIQUE (booking_id, author_user_id, target_type),
  CONSTRAINT review_listing_target_requires_listing CHECK (
    target_type <> 'LISTING' OR target_listing_id IS NOT NULL
  ),
  CONSTRAINT review_renter_target_requires_user CHECK (
    target_type <> 'RENTER' OR target_user_id IS NOT NULL
  )
);

CREATE INDEX IF NOT EXISTS idx_review_listing_target
  ON review(target_listing_id, target_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_review_booking
  ON review(booking_id);

COMMIT;
