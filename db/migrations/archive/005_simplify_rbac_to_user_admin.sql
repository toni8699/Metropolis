-- Simplify auth model to user/admin.
-- Safe migration: additive first, data backfill second, cleanup last.

ALTER TABLE app_user
  ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE app_user
SET is_admin = TRUE
WHERE role = 'ADMIN';

ALTER TABLE vehicle_listing
  ADD COLUMN IF NOT EXISTS is_company_owned BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE vehicle_listing
SET is_company_owned = TRUE
WHERE source_type = 'FLEET' OR owner_user_id IS NULL;

-- Optional cleanup for old multi-role table values.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'roles') THEN
    DELETE FROM roles
    WHERE name NOT IN ('user', 'admin');

    INSERT INTO roles (name)
    VALUES ('user'), ('admin')
    ON CONFLICT (name) DO NOTHING;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_roles') THEN
      DELETE FROM user_roles;
      INSERT INTO user_roles (user_id, role_id)
      SELECT
        u.user_id,
        r.id
      FROM app_user u
      JOIN roles r ON r.name = CASE WHEN u.is_admin THEN 'admin' ELSE 'user' END
      ON CONFLICT DO NOTHING;
    END IF;
  END IF;
END $$;
