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
  scripts/
db/
  schema.sql                           Full schema (base + marketplace extension)
  migrations/001_marketplace_mvp.sql   Incremental migration for existing DBs
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

3. For existing DBs, apply only marketplace migration:

   ```bash
   set -a && . ./.env && set +a
   psql "$DATABASE_URL" -f db/migrations/001_marketplace_mvp.sql
   ```

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
| POST | `/api/auth/register` | Register renter/owner/admin |
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

> Admin endpoints require `ADMIN` token.

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
