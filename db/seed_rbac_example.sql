-- Example RBAC seed data for simplified user/admin auth.
-- Run after base seed + migration 005.

INSERT INTO app_user (email, password_hash, role, full_name, is_admin)
VALUES
  ('user1@example.com', 'pbkdf2:sha256:260000$seed$user', 'RENTER', 'User One', FALSE),
  ('host1@example.com', 'pbkdf2:sha256:260000$seed$host', 'OWNER', 'Host One', FALSE),
  ('admin1@example.com', 'pbkdf2:sha256:260000$seed$admin', 'ADMIN', 'Ops Admin', TRUE)
ON CONFLICT (email) DO NOTHING;

INSERT INTO vehicle_listing (
  owner_user_id,
  created_by_user_id,
  source_type,
  title,
  description,
  price_per_day,
  active,
  status,
  is_company_owned
)
SELECT
  u.user_id,
  u.user_id,
  'OWNER',
  'Host-owned compact car',
  'Direct host listing for RBAC example.',
  79.00,
  TRUE,
  'ACTIVE',
  FALSE
FROM app_user u
WHERE u.email = 'host1@example.com'
ON CONFLICT DO NOTHING;

INSERT INTO vehicle_listing (
  owner_user_id,
  created_by_user_id,
  source_type,
  title,
  description,
  price_per_day,
  active,
  status,
  is_company_owned
)
SELECT
  u.user_id,
  u.user_id,
  'OWNER',
  'Company-owned example listing',
  'Managed by admin account with company ownership flag.',
  110.00,
  TRUE,
  'ACTIVE',
  TRUE
FROM app_user u
WHERE u.email = 'admin1@example.com'
ON CONFLICT DO NOTHING;
