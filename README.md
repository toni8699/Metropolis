# Metropolis Nexus

Single-city P2P car-share MVP with fleet fallback.

- **Marketplace mode**: users list cars, renters book, owners send pickup instructions.
- **Fleet mode**: company vehicles are still available and can be exposed as map listings.

## Repository Layout

```text
backend/
  run.py                               Entry point (Flask app)
  metropolis/
    api/                               Blueprints (APIFairy documented)
    schemas/                           Marshmallow schemas
    services/                          Auth, rental, marketplace logic
    auth.py                            JWT auth utilities
    db.py                              Neon connection helper
  requirements.txt
  uv.lock
  scripts/
db/
  schema.sql                           Full schema (base + marketplace extension)
  migrate.sh                           Applies migrations (incremental or clean mode)
  migrations/000_initial_clean.sql     Canonical clean bootstrap entrypoint
  migrations/*.sql                     Incremental migration set
  seed.sql
  setup-neon.sh
frontend/
  src/                                 React + Tailwind app
```

## Setup

1. Create Neon database and put URL in `.env`:

   ```bash
   cp .env.example .env
   ```

2. For clean DB initialization:

   ```bash
   chmod +x db/setup-neon.sh backend/scripts/*.sh
   ./db/setup-neon.sh
   ```

3. Apply migrations (incremental compatibility path):

   ```bash
   chmod +x db/migrate.sh
   set -a && . ./.env && set +a
   ./db/migrate.sh
   ```

   For brand-new clean bootstrap (canonical entrypoint):

   ```bash
   MIGRATION_MODE=clean ./db/migrate.sh
   ```

4. Install Python dependencies with `uv`:

   ```bash
   # if needed: curl -LsSf https://astral.sh/uv/install.sh | sh
   ./backend/scripts/build.sh
   ```

   This uses `backend/pyproject.toml` as source of truth and creates/uses `backend/uv.lock`.

5. (Optional) Export a pip-compatible lock snapshot:

   ```bash
   ./backend/scripts/export-requirements.sh
   ```

6. Reset to Toronto-only launch dataset:

   ```bash
   chmod +x db/reset-single-city-toronto.sh
   ./db/reset-single-city-toronto.sh
   ```

7. One-shot reset + admin + fleet sync:

   ```bash
   chmod +x db/reset-and-sync-toronto.sh
   ./db/reset-and-sync-toronto.sh
   ```

   Optional env overrides:
   - `API_URL` (default `http://localhost:8080`)
   - `ADMIN_EMAIL` (default `admin@drivebnb.local`)
   - `ADMIN_PASSWORD` (default `Admin123!`)

8. Scrub all users and recreate only admin + fleet listings:

   ```bash
   chmod +x db/scrub-users-and-recreate-admin.sh
   ./db/scrub-users-and-recreate-admin.sh
   ```

9. Demo mode (company fleet only):
   - keep `ALLOW_USER_LISTINGS=0` (default)
   - users can browse/book only
   - only admin can add listings
   - later enable user listing with `ALLOW_USER_LISTINGS=1`

10. Admin company listing workflow:
   - open Admin Dashboard -> Create Listing
   - choose `Area`, then location source (`Branch` or `Designated Parking`)
   - choose source location from dropdown (no manual lat/lng for company listings)
   - confirm auto-filled address + map preview marker
   - create listing, then upload S3 photos from Listings section

## Backend API

Run:

```bash
./backend/scripts/run-api.sh
```

Server: `http://localhost:8080`

- API docs: [http://localhost:8080/docs](http://localhost:8080/docs)
- OpenAPI JSON: `http://localhost:8080/apispec.json`

### Core Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/register` | Register user/admin |
| POST | `/api/auth/login` | Login and get JWT |
| GET | `/api/me` | Current user (Bearer token) |
| GET | `/api/market/listings` | Map search listings (`bbox`, `cityZone`) |
| GET | `/api/market/listings/{id}` | Listing detail |
| GET | `/api/owner/listings` | Owner listings |
| POST | `/api/owner/listings` | Create owner listing |
| PATCH | `/api/owner/listings/{id}` | Update owner listing |
| POST | `/api/owner/listings/{id}/location` | Set listing parked location |
| POST | `/api/owner/listings/{id}/availability` | Add availability window |
| POST | `/api/bookings` | Create booking |
| GET | `/api/bookings/{id}` | Booking details + instruction timeline |
| POST | `/api/bookings/{id}/instructions` | Owner sends pickup instructions |
| POST | `/api/bookings/{id}/confirm-pickup` | Mark in progress |
| POST | `/api/bookings/{id}/complete` | Mark completed |
| GET | `/api/vehicles/available` | Legacy fleet analytics |
| GET | `/api/reservations` | Legacy reservation lookup |
| GET | `/api/admin/relocation/simulate` | Legacy relocation planner |
| POST | `/api/admin/fleet/sync-listings` | Mirror available fleet cars into marketplace listings |
| GET | `/api/admin/company-locations` | Area/branch/parking catalog for admin listing dropdowns |
| POST | `/api/uploads/presign` | Create presigned S3 upload URL |
| POST | `/api/uploads/complete` | Persist uploaded file metadata |

> Admin endpoints require admin token.

## Frontend (React + Tailwind)

Run:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Default URL: `http://localhost:5173`

Set:

- `VITE_API_URL=http://localhost:8080`
- `VITE_GOOGLE_MAPS_API_KEY=...` (optional; map fallback shown when missing)

### Implemented pages

- Map browse (`/`) with listing cards + map component
- Listing detail + quick booking (`/listings/:listingId`)
- Booking details + instruction timeline (`/bookings/:bookingId`)
- Owner dashboard + listing creation (`/owner`)
