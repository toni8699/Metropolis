#!/bin/sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

if [ -z "${DATABASE_URL:-}" ]; then
  if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$ROOT_DIR/.env"
    set +a
  fi
fi

if [ -z "${DATABASE_URL:-}" ]; then
  echo "Set DATABASE_URL in .env or your shell (Neon connection string)."
  exit 1
fi

echo "Applying schema..."
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$ROOT_DIR/db/schema.sql"

echo "Loading seed data..."
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$ROOT_DIR/db/seed.sql"

echo "Database ready."
