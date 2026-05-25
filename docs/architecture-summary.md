# Metropolis Nexus (DriveBnb) — Architectural Summary

**Purpose:** Handoff document for AI/human reviewers to suggest improvements, testing strategies, and DevOps setups.  
**Codebase:** Monorepo at project root — `frontend/`, `backend/`, `db/`, `tests/`.  
**Last aligned with:** migrations through `012_review_sub_ratings.sql`, Flask marketplace + fleet hybrid model.

Related diagrams: [`architecture-diagrams.md`](./architecture-diagrams.md).

---

## 1. System Overview & Business Model Integration

### What the product is

Metropolis Nexus (branded DriveBnb in Docker images) is a **hybrid car rental marketplace**: peer-to-peer listings from individual hosts coexist with **company fleet** inventory sourced from a traditional rental schema (`area`, `branch`, `vehicle`). Renters discover vehicles on a map, book date ranges, manage trips, and leave reviews. Hosts onboard listings; admins sync fleet vehicles into marketplace listings and run relocation/utilization tooling.

### P2P vs traditional fleet (how the code unifies them)

Both models share one marketplace surface: the `vehicle_listing` table with a discriminating `source_type` enum:

| Aspect | P2P (`OWNER`) | Fleet (`FLEET`) |
|--------|----------------|-----------------|
| Inventory source | Host-created via `HostOnboardingFlow` / owner APIs | `Vehicle` rows synced by `POST /api/admin/fleet/sync-listings` |
| Ownership | `owner_user_id` required; `fleet_vehicle_vin` null | `fleet_vehicle_vin` → `vehicle(vin)`; often `is_company_owned = TRUE` |
| Location | Host-provided lat/lng → `listing_location` | `location_source_type` `BRANCH` or `PARKING_SPOT` (migration 006) |
| Booking conflict | Per `listing_id` | Per `listing_id` **and** per `fleet_vehicle_vin` (one physical car, multiple listing rows possible) |
| Host visibility | `GET /api/owner/bookings` (`_HOST_LISTING_FILTER`) | `GET /api/admin/bookings` (`_COMPANY_FLEET_FILTER`) |
| UI label | “Individual host” | “DriveBnb Fleet” when `sourceType === "FLEET"` |

**Single booking pipeline:** Renters always use `POST /api/bookings` → `marketplace_service.create_booking()`. There is no separate checkout for “traditional” rental; legacy endpoints (`/api/vehicles/available`, `/api/reservations?email=`) read fleet tables via `rental_service` but are **not wired into the React booking UI**.

**Traditional fleet ops (parallel):** `rental_service` implements branch utilization stats, inter-area relocation fee simulation (`relocation` table), and email-based reservation lookup against the unified `booking` table. Legacy tables `customer`, `reservation`, `rentalperiod`, `agreement` were dropped in migration `010`.

### High-level architecture

| Pattern | Actual implementation |
|---------|-------------------------|
| Style | **Modular monolith** — one Flask process, blueprint-per-domain API, service layer |
| Clients | **Single React SPA** (Vite) — renter `/app/*`, host `/host/*`, admin `/admin` |
| API | **REST/JSON** over HTTP, JWT Bearer auth, OpenAPI via ApiFairy at `/docs` |
| Data | **Neon PostgreSQL** (managed, external to Docker Compose) |
| Files | **AWS S3** presigned uploads (browser PUT) |
| Mobile | **Not present** in repository |
| Message bus / workers | **None** |
| API gateway | **None** — Flask listens directly (port 5000) |

```
┌─────────────────────────────────────────────────────────┐
│  React SPA (Vite) — marketplace + host + admin routes   │
└───────────────────────────┬─────────────────────────────┘
                            │ REST + JWT
┌───────────────────────────▼─────────────────────────────┐
│  Flask monolith (metropolis)                              │
│  api/* → services/* → psycopg2 / boto3                  │
└─────┬───────────────────────────────┬───────────────────┘
      │                               │
      ▼                               ▼
 Neon PostgreSQL                  AWS S3
 (fleet + marketplace tables)     (photos, USER_DOC)
```

---

## 2. Technology Stack

### Frontend

| Layer | Choice | Notes |
|-------|--------|-------|
| Framework | **React 18** | `frontend/package.json` |
| Build | **Vite 5** | Dev `:5173`, Docker `:3000` |
| Routing | **React Router 6** | `frontend/src/App.jsx` |
| Styling | **Tailwind CSS 3** | PostCSS |
| Server state | **TanStack React Query 5** | Used on data-heavy pages |
| Local auth state | **React Context** | `AuthContext.jsx` + `localStorage` (`accessToken`, `authUser`) |
| Forms / validation | **react-hook-form**, **Zod** | Host onboarding, etc. |
| Maps | **@react-google-maps/api**, **@vis.gl/react-google-maps** | `VITE_GOOGLE_MAPS_API_KEY` |
| Charts | **Recharts** | Host/admin dashboards |
| Mobile | **N/A** | No React Native / Expo / second client |

No Redux, Zustand, or Next.js. No frontend test runner (no Jest/Vitest/Cypress in `package.json`).

### Backend

| Layer | Choice | Notes |
|-------|--------|-------|
| Language | **Python 3.10+** (Docker 3.11-slim) | `backend/pyproject.toml` |
| Framework | **Flask 3** | `backend/metropolis/__init__.py` |
| API docs | **ApiFairy 1.4** (ReDoc UI) | `APIFAIRY_UI = "redoc"` |
| Validation | **Marshmallow**, **webargs** | Schemas under `backend/metropolis/schemas/` |
| Auth | **PyJWT** HS256 | `@require_auth`, `@require_admin` in `metropolis/auth.py` |
| Password hashing | **Werkzeug** | `auth_service` |
| Rate limiting | **Flask-Limiter** | By remote IP; default limits empty in code |
| HTTP server (prod-capable) | **Gunicorn** in deps | Dev uses `python run.py` |
| Protocol | **REST JSON** only | No GraphQL, gRPC, WebSockets |

**Data access is split:** Most business logic uses **raw SQL via psycopg2** (`metropolis/db.py`). **SQLAlchemy** is initialized (`flask-sqlalchemy`) and models exist for `app_user` and `vehicle_listing` only — Alembic baseline, not the primary query path for bookings/market.

### Databases & caching

| Component | Status |
|-----------|--------|
| Primary DB | **PostgreSQL on Neon** — `DATABASE_URL` in root `.env` |
| ORM | **SQLAlchemy 2** — partial models in `sqlalchemy_models.py` |
| Migrations | **Alembic** (`backend/alembic/`) + SQL scripts (`db/migrations/`, `db/schema.sql` snapshot) |
| Redis | **Not used** |
| Elasticsearch / search index | **Not used** — listing search is SQL `bbox` / `city_zone` |
| Connection pooling | **Per-request connections** via `get_connection()` context manager (no PgBouncer config in repo) |

### Third-party integrations

| Integration | Status | Implementation |
|-------------|--------|----------------|
| **Payments (Stripe, etc.)** | **Not integrated** | Checkout shows mock card UI (`BookingCheckoutPage.jsx`); `booking.price_snapshot_json` stores `{ pricePerDay }` only |
| **Payouts** | **Schema only** | `owner_profile.payout_ref` — unused in booking flow |
| **KYC / identity** | **Internal MVP** | `owner_profile.verification_status`; S3 scope `USER_DOC` — no Onfido/Persona/etc. |
| **Maps / geolocation** | **Client-side Google Maps** | No backend geocoding proxy |
| **GPS / telematics** | **Simulated for fleet** | `_fleet_coords(city, vin)` in `marketplace_service.py`; no device API |
| **Object storage** | **AWS S3** | `uploads_service` presign + `file_asset` / `listing_image` |
| **OAuth / SSO** | **Not present** | Email/password register + login only |

---

## 3. Core Modules & Data Models (Briefly)

### User roles (runtime vs schema)

| Role | How enforced | Capabilities |
|------|----------------|--------------|
| **Renter** | Default `app_user`; JWT `role: "user"` | Browse, book, trips, reviews |
| **Individual host** | User with `vehicle_listing` where `source_type='OWNER'` and `is_company_owned=FALSE`; `hasListings` on `/api/me` | Owner dashboard, listing CRUD, booking instructions |
| **Fleet operator / admin** | `app_user.is_admin = TRUE` | `/admin`, fleet sync, relocation sim, fleet bookings analytics |
| **Fleet operator (org)** | `organizations` + `organization_members` tables (migration 004) | **Schema exists; no Python service references found** — incomplete feature |

Legacy `user_role` enum (`RENTER`, `OWNER`, `ADMIN`) remains in older schema snapshots; runtime auth simplified to **`is_admin` boolean** (migration 005) plus optional `roles` / `user_roles` junction.

### API modules (Flask blueprints)

| Prefix | Module | Responsibility |
|--------|--------|----------------|
| `/api` | `health`, `me` | Health, current user profile |
| `/api/auth` | `auth` | Register, login |
| `/api/market` | `market` | Public listings, search, reviews read |
| `/api/bookings` | `bookings` | Create/list bookings, trip lifecycle, reviews write |
| `/api/owner` | `owner` | Host listings, analytics, owner bookings |
| `/api/admin` | `admin` | Fleet sync, relocation, admin CRUD/analytics |
| `/api/uploads` | `uploads` | S3 presign + complete |
| `/api/vehicles` | `vehicles` | Fleet availability by area (legacy) |
| `/api/reservations` | `reservations` | Email booking lookup (legacy) |

### Service layer

| Service | File | Scope |
|---------|------|--------|
| `marketplace_service` | `marketplace_service.py` (~1391 LOC) | Listings, search, bookings, conflicts, fleet sync, reviews aggregation |
| `rental_service` | `rental_service.py` | Branch stats, relocation simulation, legacy reservation queries |
| `auth_service` | `auth_service.py` | Register/login password hashing |
| `review_service` | `review_service.py` | Review CRUD, 30-day window, sub-ratings |
| `uploads_service` | `uploads_service.py` | S3 presign policies by scope |

### Key entities & relationships

| Entity | Table | Notes |
|--------|-------|-------|
| **User** | `app_user` | PK `user_id`; JWT subject |
| **Owner profile** | `owner_profile` | 1:1 user; verification + payout ref |
| **Roles** | `roles`, `user_roles` | M:N; synced from `is_admin` |
| **Fleet vehicle** | `vehicle` | PK `vin`; `status` string (`Available`, `Maintenance`, …) — **no `maintenance_log` table** |
| **Fleet topology** | `area`, `branch`, `vehicleclass`, `employee`, `relocation`, `company_parking_spot` | Traditional rental schema |
| **Listing** | `vehicle_listing` | Bridge P2P/fleet; `source_type`, `fleet_vehicle_vin`, `is_company_owned` |
| **Listing geo** | `listing_location` | 1:1 listing; lat/lng, `city_zone` |
| **Availability windows** | `listing_availability` | `AVAILABLE` / `BLOCKED` — not fully driving search/book yet |
| **Booking** | `booking` | Unified P2P + fleet; status enum; **`price_snapshot_json` replaces Payment entity** |
| **Trip audit** | `trip_event`, `booking_instruction` | Lifecycle + host messages |
| **Review** | `review` | Post-`COMPLETED`; sub-ratings `cleanliness`, `accuracy`, `communication` (012) |
| **Media** | `file_asset`, `listing_image` | S3-backed M:N listing images |
| **Payment** | — | **Not modeled** |
| **MaintenanceLog** | — | **Not modeled**; use `vehicle.status` |

---

## 4. Current Testing Setup

### Frameworks installed

| Area | Tool | Config |
|------|------|--------|
| Backend dev deps | **pytest 8**, **requests**, **ruff** | `backend/pyproject.toml` `[project.optional-dependencies] dev` |
| Root pytest | `pytest.ini` — `testpaths = tests`, `pythonpath = backend` | |
| Frontend | **None** | No test scripts or runners in `frontend/package.json` |
| E2E | **None** | No Playwright/Cypress |

### Existing tests

| File | Type | What it covers |
|------|------|----------------|
| `tests/test_reviews_integration.py` | **Integration** (HTTP + DB) | Full reviews flow: create booking via API, enforce `COMPLETED` before review, 30-day window, duplicate review rejection, listing `averageRating` / `reviewCount` math |

**Requirements for integration tests:**

- Running backend at `INTEGRATION_API_URL` (default `http://localhost:5000`)
- `DATABASE_URL` set (same Neon DB as API — tests mutate data)
- At least one active listing in DB
- Optional: `INTEGRATION_EMAIL`, `INTEGRATION_PASSWORD`, `INTEGRATION_LISTING_ID`

**Not covered (gaps):** unit tests for services, booking conflict logic, fleet sync, auth, uploads, owner/admin APIs, frontend components, contract tests, load tests, CI automation.

### Linting

- **Ruff** configured for backend (`E`, `F`, `I`, `B`, `UP`); no pre-commit hook in repo.

---

## 5. Current Infrastructure & DevOps

### Deployment / hosting

| Environment | Mechanism | Details |
|-------------|-----------|---------|
| **Local dev** | Manual terminals or **Docker Compose** | `docker-compose.yml`: `backend` + `frontend` only |
| **Database** | **Neon** (external SaaS) | Connection via root `.env` `DATABASE_URL`; no Postgres container |
| **Object storage** | **AWS S3** | Credentials in `.env` |
| **Production** | **Not defined in repo** | No Terraform, Kubernetes, Heroku, Vercel, or AWS ECS manifests |
| **Frontend prod build** | `npm run build` (Vite) | Static assets; no CDN/deploy config committed |

Backend Docker image: `python:3.11-slim`, installs `requirements.txt`, runs `alembic upgrade head` then `python run.py` on compose start.

### CI/CD

| Item | Status |
|------|--------|
| GitHub Actions | **None** (no `.github/workflows/`) |
| GitLab CI | **None** |
| Automated test on push | **None** |
| Automated deploy | **None** |

### Logs & monitoring

| Concern | Status |
|---------|--------|
| Application logging | **Minimal** — Alembic `logging.config` only; no structured app logger in Flask services |
| APM (Datadog, New Relic) | **None** |
| Error tracking (Sentry) | **None** |
| Metrics / Prometheus | **None** |
| Centralized logs | **None** |
| Health check | `GET` health blueprint exists for basic liveness |

Operational visibility today is effectively **Docker/terminal stdout** and **Neon/AWS consoles** outside the app.

---

## 6. Key Constraints or Known Pain Points

### Business / product gaps

1. **No real payments** — Bookings auto-`CONFIRMED` on create; no `PENDING` → capture → confirm; checkout fees computed client-side only and not persisted server-side.
2. **No dual payout logic** — `payout_ref` unused; fleet vs host revenue split not implemented.
3. **KYC is cosmetic** — Status field + document upload; no vendor workflow or booking gates.

### Booking & availability

4. **Search ignores date range** — Frontend sends `start`/`end` to `GET /api/market/listings`; `search_listings()` filters only `active`, `cityZone`, `bbox` — renters may see unavailable cars.
5. **`listing_availability` underused** — Table exists; conflict logic uses overlapping `booking` rows only.
6. **Instant confirmation** — `create_booking` inserts `CONFIRMED` directly (MVP); no host approval step for P2P.
7. **Fleet VIN conflicts** — Correctly handled in SQL, but multiple FLEET listings per VIN possible after sync — operational complexity.

### Architecture & code health

8. **`marketplace_service.py` concentration** — ~1400 lines; listings, bookings, fleet sync, analytics intertwined — high change risk.
9. **Dual DB access patterns** — psycopg2 raw SQL + partial SQLAlchemy models — ORM migrations don't match query layer mental model.
10. **Legacy API surface** — `/api/reservations`, `/api/vehicles` parallel marketplace without frontend consumers — confusion for new contributors.
11. **Organizations RBAC** — DB tables without backend usage — dead schema path.
12. **Simulated fleet GPS** — Not suitable for real telematics or live fleet map.

### Security & ops

13. **JWT secret default** — `change-me-dev-secret` in config if unset.
14. **Integration tests hit production-like Neon** — Risk of data pollution; no test DB isolation in CI.
15. **No connection pooling** — New psycopg2 connection per service call pattern via `get_connection()`.
16. **CORS / rate limits** — Configured but default limiter limits empty; production hardening not documented.

### Performance (inferred)

17. **Listing search `LIMIT 500`** without pagination — map browse may degrade with inventory growth.
18. **Hydration per listing** — `_hydrate_listing_rows` may N+1 on photos/ratings for large result sets (verify when profiling).

---

## Appendix: Quick reference paths

| Topic | Path |
|-------|------|
| Frontend entry | `frontend/src/main.jsx`, `App.jsx` |
| API client | `frontend/src/utils/api.js` |
| Booking UI | `frontend/src/pages/BookingCheckoutPage.jsx`, `ListingDetailPage.jsx` |
| Booking API | `backend/metropolis/api/bookings.py` |
| Core domain logic | `backend/metropolis/services/marketplace_service.py` |
| Fleet / relocation | `backend/metropolis/services/rental_service.py` |
| Schema snapshot | `db/schema.sql` |
| Migrations | `db/migrations/001`–`012` |
| Integration tests | `tests/test_reviews_integration.py` |
| Docker dev | `docker-compose.yml` |
| Env template | `.env.example`, `frontend/.env.example` |

---

## Suggested review focus areas (for downstream AI)

1. Payment state machine + idempotent webhooks + separate `payments` table.  
2. Date-aware search using `listing_availability` + `booking` exclusion in one query.  
3. Split `marketplace_service` into listing / booking / fleet modules.  
4. CI: ephemeral Postgres, `pytest` on PR, optional Neon branch for integration.  
5. Frontend Vitest + MSW; Playwright smoke for book → trips.  
6. Observability: structured JSON logs, request ID, Sentry, health/readiness split.  
7. Production deploy blueprint (e.g. Fly.io/ECS + S3 + Neon + CloudFront).  
8. Remove or implement organizations; deprecate legacy reservation endpoints explicitly.
