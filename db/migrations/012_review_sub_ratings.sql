-- Migration 012: Category sub-ratings on reviews (cleanliness, accuracy, communication).

BEGIN;

ALTER TABLE review
  ADD COLUMN IF NOT EXISTS cleanliness INT
    CHECK (cleanliness IS NULL OR cleanliness BETWEEN 1 AND 5),
  ADD COLUMN IF NOT EXISTS accuracy INT
    CHECK (accuracy IS NULL OR accuracy BETWEEN 1 AND 5),
  ADD COLUMN IF NOT EXISTS communication INT
    CHECK (communication IS NULL OR communication BETWEEN 1 AND 5);

COMMIT;
