#!/bin/sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
API_URL="${API_URL:-http://localhost:8080}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@drivebnb.local}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Admin123!}"

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

for bin in psql curl python3; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "$bin required."
    exit 1
  fi
done

if ! curl -fsS "$API_URL/api/health" >/dev/null; then
  echo "Backend not reachable at $API_URL."
  exit 1
fi

echo "Scrubbing users + listing/booking data (keeps branch/parking catalog)..."
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 <<'SQL'
TRUNCATE TABLE
  trip_event,
  booking_instruction,
  booking,
  listing_availability,
  listing_location,
  vehicle_listing,
  file_asset,
  owner_profile,
  app_user
RESTART IDENTITY CASCADE;
SQL

echo "Recreating admin user..."
REGISTER_PAYLOAD=$(cat <<EOF
{"email":"$ADMIN_EMAIL","password":"$ADMIN_PASSWORD","fullName":"Platform Admin","role":"admin"}
EOF
)
REGISTER_RESPONSE="$(curl -sS -X POST "$API_URL/api/auth/register" -H "Content-Type: application/json" -d "$REGISTER_PAYLOAD" || true)"
printf '%s\n' "$REGISTER_RESPONSE" | python3 -c "import sys,json
raw=sys.stdin.read().strip() or '{}'
data=json.loads(raw)
if data.get('status') != 'success':
    print('Admin recreation failed:', raw)
    raise SystemExit(1)
print('Admin recreated.')"

echo "Forcing admin flag in DB (safety)..."
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -c "UPDATE app_user SET is_admin = TRUE, role = 'ADMIN'::user_role WHERE email = '$ADMIN_EMAIL';"

echo "Logging in admin..."
LOGIN_PAYLOAD=$(cat <<EOF
{"email":"$ADMIN_EMAIL","password":"$ADMIN_PASSWORD"}
EOF
)
TOKEN="$(curl -sS -X POST "$API_URL/api/auth/login" -H "Content-Type: application/json" -d "$LOGIN_PAYLOAD" | python3 -c "import sys,json
data=json.load(sys.stdin)
token=data.get('token')
if not token:
    raise SystemExit(1)
print(token)")"

echo "Syncing company fleet listings..."
curl -sS -X POST "$API_URL/api/admin/fleet/sync-listings" -H "Authorization: Bearer $TOKEN" >/dev/null

echo "Done."
echo "Admin email: $ADMIN_EMAIL"
