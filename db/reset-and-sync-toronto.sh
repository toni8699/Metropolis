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

if ! command -v curl >/dev/null 2>&1; then
  echo "curl required."
  exit 1
fi
if ! command -v psql >/dev/null 2>&1; then
  echo "psql required."
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 required."
  exit 1
fi

if ! curl -fsS "$API_URL/api/health" >/dev/null; then
  echo "Backend not reachable at $API_URL. Start backend first."
  echo "Example: cd backend && ./scripts/run-api.sh"
  exit 1
fi

echo "Applying idempotent migrations (001 -> 008)..."
sh "$ROOT_DIR/db/migrate.sh"

echo "Resetting to Toronto single-city baseline..."
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$ROOT_DIR/db/reset-single-city-toronto.sql"

echo "Ensuring admin user exists..."
REGISTER_PAYLOAD=$(cat <<EOF
{"email":"$ADMIN_EMAIL","password":"$ADMIN_PASSWORD","fullName":"Toronto Admin","role":"admin"}
EOF
)
REGISTER_RESPONSE="$(curl -sS -X POST "$API_URL/api/auth/register" -H "Content-Type: application/json" -d "$REGISTER_PAYLOAD" || true)"
printf '%s\n' "$REGISTER_RESPONSE" | python3 -c "import sys,json
raw=sys.stdin.read().strip() or '{}'
try:
    data=json.loads(raw)
except Exception:
    print('Admin register failed (non-JSON response).')
    print(raw)
    raise SystemExit(1)
status=data.get('status')
if status not in {'success','validation_error'}:
    print('Admin register failed:')
    print(raw)
    raise SystemExit(1)
print('Admin register status:', status)"

echo "Logging in admin..."
LOGIN_PAYLOAD=$(cat <<EOF
{"email":"$ADMIN_EMAIL","password":"$ADMIN_PASSWORD"}
EOF
)
TOKEN="$(curl -sS -X POST "$API_URL/api/auth/login" -H "Content-Type: application/json" -d "$LOGIN_PAYLOAD" | python3 -c "import sys,json
data=json.load(sys.stdin)
token=data.get('token')
if not token:
    print('')
    raise SystemExit(1)
print(token)")"

echo "Syncing fleet listings..."
SYNC_RESPONSE="$(curl -sS -X POST "$API_URL/api/admin/fleet/sync-listings" -H "Authorization: Bearer $TOKEN")"
printf '%s\n' "$SYNC_RESPONSE" | python3 -c "import sys,json
data=json.load(sys.stdin)
print('Sync result:', data)"

echo "Checking company location dropdown dataset..."
LOC_RESPONSE="$(curl -sS "$API_URL/api/admin/company-locations" -H "Authorization: Bearer $TOKEN")"
printf '%s\n' "$LOC_RESPONSE" | python3 -c "import sys,json
data=json.load(sys.stdin)
print('Areas:', len(data.get('areas', [])))
print('Branches:', len(data.get('branches', [])))
print('Parking spots:', len(data.get('parkingSpots', [])))"

LISTING_COUNT="$(curl -sS "$API_URL/api/market/listings?cityZone=toronto" | python3 -c "import sys,json
data=json.load(sys.stdin)
print(len(data.get('listings', [])))")"

echo "Done. Toronto listings count: $LISTING_COUNT"
echo "Admin email: $ADMIN_EMAIL"
