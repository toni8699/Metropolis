CREATE TABLE IF NOT EXISTS roles (
  id SERIAL PRIMARY KEY,
  name VARCHAR(64) NOT NULL UNIQUE
);

INSERT INTO roles (name)
VALUES
  ('guest'),
  ('host'),
  ('company_admin'),
  ('support_admin'),
  ('super_admin')
ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS user_roles (
  user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  role_id INT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS organizations (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(160) NOT NULL,
  type VARCHAR(32) NOT NULL
);

CREATE TABLE IF NOT EXISTS organization_members (
  user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  role VARCHAR(64) NOT NULL,
  PRIMARY KEY (user_id, organization_id)
);

ALTER TABLE vehicle_listing
  ADD COLUMN IF NOT EXISTS owner_organization_id BIGINT REFERENCES organizations(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS created_by_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE';

UPDATE vehicle_listing
SET created_by_user_id = COALESCE(created_by_user_id, owner_user_id);

ALTER TABLE vehicle_listing
  DROP CONSTRAINT IF EXISTS vehicle_listing_owner_mode_check;

ALTER TABLE vehicle_listing
  ADD CONSTRAINT vehicle_listing_owner_mode_check
  CHECK (
    (
      source_type = 'OWNER'
      AND (
        (owner_user_id IS NOT NULL AND owner_organization_id IS NULL)
        OR (owner_user_id IS NULL AND owner_organization_id IS NOT NULL)
      )
    )
    OR (source_type = 'FLEET' AND fleet_vehicle_vin IS NOT NULL)
  );

INSERT INTO user_roles (user_id, role_id)
SELECT u.user_id, r.id
FROM app_user u
JOIN roles r ON r.name = CASE u.role
  WHEN 'OWNER' THEN 'host'
  WHEN 'ADMIN' THEN 'super_admin'
  ELSE 'guest'
END
ON CONFLICT DO NOTHING;
