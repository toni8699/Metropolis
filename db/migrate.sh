#!/bin/sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

if [ -z "${DATABASE_URL:-}" ] && [ -f "$ROOT_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$ROOT_DIR/.env"
  set +a
fi

if [ -z "${DATABASE_URL:-}" ]; then
  echo "Set DATABASE_URL in .env or environment."
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "psql required."
  exit 1
fi

MODE="${MIGRATION_MODE:-incremental}"

if [ "$MODE" = "clean" ]; then
  TABLE_EXISTS="$(psql "$DATABASE_URL" -Atqc "SELECT to_regclass('public.area') IS NOT NULL")"
  if [ "$TABLE_EXISTS" = "t" ]; then
    if [ "${CLEAN_RESET_DATABASE:-0}" = "1" ]; then
      echo "Clean mode with reset: dropping and recreating public schema..."
      psql "$DATABASE_URL" -v ON_ERROR_STOP=1 <<'SQL'
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
SQL
    else
      echo "Clean mode needs empty DB."
      echo "Use incremental mode, or run with CLEAN_RESET_DATABASE=1 to recreate schema."
      exit 1
    fi
  fi
  echo "Applying clean bootstrap migration 000_initial_clean.sql..."
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$ROOT_DIR/db/migrations/000_initial_clean.sql"
else
echo "Applying migrations 001 -> 008..."
  for migration in \
    001_marketplace_mvp.sql \
    002_listing_vehicle_fields.sql \
    003_s3_assets_and_regions.sql \
    004_multi_role_rbac.sql \
    005_simplify_rbac_to_user_admin.sql \
    006_company_location_sources.sql \
    007_listing_vehicle_specs.sql \
    008_listing_rich_details.sql
  do
    echo "  - $migration"
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$ROOT_DIR/db/migrations/$migration"
  done
fi

echo "Migrations applied."
