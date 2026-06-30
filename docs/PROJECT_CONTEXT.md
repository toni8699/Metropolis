# Vroom — Project Context

Durable reference for coding agents. Built from verified repository audits (stack, data
flow, security, database). Facts cite exact paths. "Current behavior" and "Recommendation"
are kept separate; recommendations are NOT implemented unless stated.

Companion docs: `docs/architecture-summary.md`, `docs/architecture-diagrams.md`,
`docs/database-schema.md`, `docs/production-deployment.md`.

---

## 1. Project purpose

Vroom is a real product: a peer-to-peer **and** company-fleet car-rental marketplace.
Renters search/book vehicles; owners (independent hosts) and the company (fleet) list
vehicles; payments run through Stripe; hosts receive payouts via Stripe Connect.

Note: the repo path contains `Comp 421` (legacy). Treat this as a shipping product, not a
course project — no grading/demo shortcuts (`.cursor/rules/project-context.mdc`).

Naming: the **product brand is "Vroom"** (frontend logo, `STRIPE_CONNECT_BUSINESS_NAME`
default), but the **codebase is internally named "Metropolis"** — `metropolis-backend`
(`backend/pyproject.toml`), `metropolis-frontend` (`frontend/package.json`), OpenAPI title
`Metropolis Nexus API` (`core/config.py`), test fixtures `*@metropolis.test`. These refer to
the same system; do not "fix" one to match the other.

## 2. Architecture summary

React SPA (Vercel) ⇄ FastAPI ASGI app (Render, Gunicorn+Uvicorn) over REST/JWT + Socket.IO.
Data in Neon PostgreSQL (raw SQL via `psycopg2`). Files in AWS S3 (presigned PUT). Payments
via Stripe. Background jobs via ARQ + Redis. See `docs/architecture-summary.md` for the
diagram and request lifecycle.

## 3. Repository structure

```
backend/
  vroom/
    main.py            # FastAPI app factory, middleware, router registration
    asgi.py            # combined FastAPI + Socket.IO ASGI entrypoint (CombinedASGI)
    security.py        # startup security checks (JWT secret, CORS)
    text_sanitize.py   # user-text sanitization helper
    hateoas.py         # link/relation helpers
    trip_inspection_angles.py + data/  # trip-inspection angle manifest
    core/              # config.py, db.py, errors.py, limiter.py
    dependencies/      # auth.py (JWT, access contexts)
    routers/           # auth, me, analytics, users, fleet, listings, vehicles,
                       #   bookings, messages, uploads, payouts, webhooks, health
    services/          # business logic (raw SQL): auth_, listing_, booking_, payment_,
                       #   payout_, message_, review_, kyc_, fleet_, trip_inspection_, ...
    sockets/           # booking_chat.py (Socket.IO server + Redis manager)
    schemas/           # Pydantic models (camel.py -> CamelModel)
    jobs/              # booking_sweep.py (ARQ worker + cron)
  tests/               # pytest suite (unit + *_integration; real Postgres)
  alembic/versions/    # migrations (hand-written)
  scripts/             # seed_marketplace.py, seed_ci_database.py, create_admin.py, ...
db/schema.sql          # canonical schema snapshot (source of truth)
frontend/
  src/
    main.jsx, app/App.jsx
    shared/api/api.js  # fetch wrapper (JWT from localStorage)
    shared/lib/        # socket.js, uploadPresigned.js
    context/           # AuthContext, SavedListings, GoogleMaps providers
    features/, views/  # feature folders + page components
docs/                  # architecture + this file
.github/workflows/ci.yml
docker-compose.yml, backend/Dockerfile.prod
```

## 4. Technology stack

| Layer | Tech (verified) | Evidence |
|---|---|---|
| Frontend | React 18.3, Vite 5.4, react-router-dom 6, Tailwind 3.4 | `frontend/package.json` |
| FE libs | lucide-react, recharts, date-fns, react-day-picker, react-easy-crop, socket.io-client, @stripe/stripe-js, @stripe/react-stripe-js, @stripe/connect-js, @stripe/react-connect-js (embedded Connect), @react-google-maps/api | `frontend/package.json` |
| Backend | Python 3.10+ (`requires-python >=3.10`, ruff target py310), FastAPI 0.137, Starlette, uvicorn (dev) / gunicorn+UvicornWorker (prod) | `backend/pyproject.toml`, `requirements.txt`, `docker-entrypoint.prod.sh` |
| DB access | PostgreSQL (Neon), `psycopg2-binary`, raw SQL, SQLAlchemy `QueuePool` only for pooling | `backend/vroom/core/db.py`, `.cursor/rules/data-access.mdc` |
| Migrations | Alembic 1.18 (hand-written, no autogenerate) | `backend/alembic/` |
| Auth | PyJWT 2.12 (HS256 Bearer), Google OAuth ID-token verify | `backend/vroom/dependencies/auth.py`, `services/auth_service.py` |
| Realtime | python-socketio (`AsyncServer`); `AsyncRedisManager` when `REDIS_URL` set, else in-process single-worker | `backend/vroom/sockets/booking_chat.py` (server), `asgi.py` (mount) |
| Jobs | arq + Redis | `backend/vroom/jobs/booking_sweep.py` |
| Storage | boto3 → S3 presigned | `backend/vroom/services/uploads_service.py` |
| Email | resend | `backend/vroom/services/mail_service.py` |
| Payments | Stripe (PaymentIntents + Connect Accounts v2) | `backend/vroom/services/payment_service.py`, `payout_service.py` |
| Rate limit | slowapi | `backend/vroom/core/limiter.py` |
| Testing | pytest (backend), Vitest + Playwright (frontend) | `backend/pyproject.toml`, `frontend/package.json` |

## 5. Frontend architecture

- SPA entry `frontend/src/main.jsx` wraps `App` with `BrowserRouter`, `AuthProvider`,
  `SavedListingsProvider`, `GoogleMapsProvider`. Routes in `frontend/src/app/App.jsx`
  (public, `/app/*` authenticated, `/host`, `/admin` role-guarded).
- State: React Context (no Redux). Auth/session in `frontend/src/context/AuthContext.jsx`.
- API client `frontend/src/shared/api/api.js`: `fetch` wrapper, attaches JWT Bearer from
  `localStorage`, parses errors. Build-time config via `VITE_*` (`frontend/.env.example`).
- Realtime: `frontend/src/shared/lib/socket.js` joins/leaves `booking_{id}` rooms (auth via
  JWT in the socket `auth.token`); booking chat in `features/bookings`/`features/chat`.
- Uploads: `frontend/src/shared/lib/uploadPresigned.js` (presign → PUT to S3 → complete).
- API contract is camelCase (backend `CamelModel`); frontend sends/expects camelCase.
- Large FE surfaces beyond browse/listing: **host dashboard** (`features/host`, panels for
  listings/availability/bookings/payouts/users/KYC), **trip-inspection wizard**
  (`features/bookings`, photo capture/compare per angle manifest), **embedded Stripe Connect**
  payouts (`PayoutEmbeddedOnboarding`/`PayoutEmbeddedManagement` via `@stripe/connect-js`),
  and **analytics** dashboards (recharts).

## 6. Backend architecture

- App factory `backend/vroom/main.py`: lifespan (DB init/dispose, socket loop bind), CORS,
  rate limiter, exception handlers, router registration under `/api/*` and `/webhooks`.
- Combined ASGI in `backend/vroom/asgi.py` routes HTTP vs Socket.IO by path.
- Layering: router (validate + auth `Depends`) → service (raw SQL, returns plain dict) →
  router serializes via Pydantic `CamelModel`.
- Config centralized in `backend/vroom/core/config.py` (pydantic-settings, `.env`).
- Errors mapped centrally in `backend/vroom/core/errors.py` (service status dict → HTTP;
  generic 500 message to avoid leakage).
- Data access rule (`.cursor/rules/data-access.mdc`): raw SQL default; ORM islands only for
  new self-contained tables meeting all listed criteria. Never mix ORM + raw SQL on the same
  table in one service.
- Router surface (`main.py`): `health`, `auth`, `me`, `analytics`, `users`, `fleet`,
  `listings`, `vehicles`, `bookings`, `messages`, `uploads`, `payouts`, `webhooks`. Beyond
  the core rent/list/pay path, notable subsystems are **messaging/chat** (`messages` router +
  `message_service.py` + `sockets/booking_chat.py`, scoped to booking participants),
  **trip inspection** (`trip_inspection_service.py`, check-in/check-out photo phases),
  **fleet/company ops** (`fleet_service.py`), **KYC/host verification** (`kyc_service.py`,
  `owner_profile.verification_status`), **reviews** (`review_service.py`), and **saved
  listings** (`saved_listing_service.py`).

## 7. Database and domain model

Source of truth: `db/schema.sql` (Alembic baseline loads it on empty DB). Full detail in
`docs/database-schema.md` and the audit. Highlights:

- **Core tables:** `app_user`, `owner_profile`, `vehicle_asset`, `vehicle_listing`,
  `listing_location`, `listing_availability`, `booking`, `payment`, `trip_event`,
  `review`, `saved_listing`, `host_payout`, plus fleet/ops tables (`management_*`,
  `vehicle_compliance_event`, `vehicle_insurance_policy`, `parking_*`, `membership_*`) that
  are **schema-only** (no service code yet) and legacy `area`/`branch`.
- **DB enums:** `user_role`, `booking_status`, `listing_source_type`, `availability_status`,
  `review_target_type`, `vehicle_asset_status`, `trip_inspection_phase`, etc. (`schema.sql:32-59`).
- **Free-text status (no enum/CHECK):** `payment.status`, `host_payout.status`,
  `owner_profile.verification_status`, `vehicle_listing.status` (state machine enforced in app).
- **Key constraints:** `app_user.email` unique; one `payment` per booking
  (`idx_payment_booking_id` unique); one `host_payout` per booking; review unique per
  `(booking_id, author_user_id, target_type)`; rating 1..5; lat/lng bounds; date ordering;
  listing status↔active consistency CHECK (`schema.sql:306`).
- **Stored function + trigger:** `sync_listing_cache_from_asset` keeps `vehicle_listing`
  spec columns in sync with `vehicle_asset` (`schema.sql:216-250`).
- **`title` vs `listing_title` contract:** `vehicle_listing.title` (NOT NULL) is the canonical
  vehicle label composed from make/model/year at create time; `listing_title` (nullable) is the
  optional host-supplied display override. Create writes them distinctly and update only touches
  `listing_title` (`listing_service.py`, helpers `compose_canonical_title` /
  `resolve_optional_listing_title` in `marketplace_common.py`). Reads should prefer
  `COALESCE(listing_title, title)` for display.

### Domain lifecycles (state machines live in services)

- **Booking** (`booking_status`): `PENDING` → (payment) → `CONFIRMED` (instant/fleet) or
  `PENDING_APPROVAL` (owner + not instant) → `CONFIRMED` (approve) / `CANCELLED` (reject) →
  `IN_PROGRESS` (pickup in window) → `COMPLETED` (complete or auto-sweep). Cancel allowed
  before trip start per role. Source: `backend/vroom/services/booking_service.py`,
  `booking_support.py`.
- **Listing** (`status`): `ACTIVE` ⇄ `INACTIVE`; `ARCHIVED` on soft-delete (blocked if active
  bookings). Source: `backend/vroom/services/listing_service.py`.
- **Payment** (`status`): `pending` → `succeeded` (no `failed`/`refunded` modeled).
- **Host payout** (`status`): `pending_onboarding`/`pending`/`succeeded`/`failed`/`skipped`
  (`backend/vroom/services/payout_service.py`).

### Data ownership

- Listing: `owner_user_id`; access via `require_listing_access`
  (`backend/vroom/dependencies/auth.py`), `_can_manage_listing` (`listing_service.py`).
- Booking: renter OR listing owner OR admin (`booking_service.get_booking`).
- Admin override via JWT `isAdmin` claim.

### Soft-delete / archival

- Listings soft-delete to `ARCHIVED`. Bookings never deleted (FK `ON DELETE RESTRICT` from
  booking→listing). Trip-inspection `file_asset` rows purged ~30 days post-completion and
  orphan S3 keys swept (`backend/vroom/jobs/booking_sweep.py`).

## 8. Main data flows

- **Register/login:** `frontend AuthContext` → `api.js` → `routers/auth.py` →
  `services/auth_service.py` (werkzeug password hash; JWT issued; Google OAuth ID-token verify).
- **Create listing:** host form → `routers/listings.py` → `services/listing_service.py`
  (VIN decode via NHTSA, features, location). Status `ACTIVE`.
- **Search:** `features/browse` → `routers/listings.py` →
  `services/marketplace_common.py` `build_listing_search_filters` → SQL. Server-side geo
  filters are `city_zone` and `bbox` (lng/lat BETWEEN); date-aware availability via
  `listing_available_for_window_sql`. (See debt: `lat`/`lng`/`radius` params dropped.)
- **Profile update:** `routers/me.py` → `services/auth_service.py`.
- **Payment:** `BookingCheckoutPage` → `POST /api/bookings` (PENDING) →
  `POST /api/bookings/:id/payments` → `services/payment_service.py` (PaymentIntent or mock
  when no key) → frontend confirm → webhook `/webhooks/stripe` (`routers/webhooks.py`).
- **Upload:** `uploadPresigned.js` → presign (`uploads_service.py`) → PUT to S3 → complete.
- **Messaging:** client `socket.js` connects with JWT → `sockets/booking_chat.py` (`connect`
  validates token, `join_room` calls `message_service.assert_booking_participant`); REST sends
  persist via `routers/messages.py` and broadcast through `emit_booking_message` to the
  `booking_{id}` room.
- **Trip inspection:** check-in/check-out photo phases via `trip_inspection_service.py`;
  inspection `file_asset` rows purged ~`TRIP_INSPECTION_RETENTION_DAYS` after completion by the
  sweep job.

## 9. Authentication and authorization

- JWT Bearer (HS256), decode/create in `backend/vroom/dependencies/auth.py`. Token stored
  client-side in `localStorage` (`frontend/src/shared/api/api.js`).
- Dependencies: `get_current_user`, `require_admin`, `verified_user_required`,
  `require_listing_access`; access contexts `UserContext`, `ListingAccessContext`.
- Google OAuth: server verifies Google ID token in `services/auth_service.py`.
- Email verification: `is_verified` + `verification_token` (+ `verification_token_expires_at`,
  24h TTL) on `app_user`; gated routes use `verified_user_required`.

## 10. Security protections

Current (verified):
- Parameterized SQL everywhere (psycopg2) — SQL-injection protected.
- Centralized generic 500 messages (`core/errors.py`) avoid internal leakage.
- CORS configured from `CORS_ORIGINS`; startup checks reject default JWT secret and warn on
  broad CORS in production (`backend/vroom/security.py`).
- Rate limiting via slowapi (`core/limiter.py`), keyed by user id or IP.
- Stripe webhook signature verification (`services/payment_service.py`).
- `.env` files git-ignored (`.gitignore`); no secrets tracked.
- Frontend avoids `dangerouslySetInnerHTML`.

Recommendations (NOT implemented — see debt):
- Move JWT off `localStorage` to httpOnly cookie (XSS token theft risk) — design below.
- Add password-reset flow (currently missing).

### Design: JWT → httpOnly cookie migration (NOT implemented)

Goal: stop exposing the JWT to JavaScript (XSS token theft) while keeping the existing
HS256 token and `get_current_user` logic.

- **Issue the cookie (auth router).** On `login`/`register`/Google OAuth success, in addition
  to (or instead of) returning `token` in the JSON body, set it as a cookie:
  `response.set_cookie(key="access_token", value=token, httponly=True, secure=True,
  samesite="lax", max_age=JWT_EXPIRES_HOURS*3600, path="/")`. Add a `logout` route that calls
  `response.delete_cookie("access_token")`.
- **Read the cookie (auth dependency).** In `dependencies/auth.py`, extend the token extractor
  to read `request.cookies.get("access_token")` first, then fall back to the `Authorization:
  Bearer` header. The Bearer fallback keeps the Socket.IO `auth.token` path and any
  service-to-service calls working during/after migration.
- **CSRF protection.** Cookies are sent automatically, so add CSRF defense for state-changing
  requests. Use the double-submit pattern: set a non-httpOnly `csrf_token` cookie at login, have
  the frontend echo it in an `X-CSRF-Token` header (add to `shared/api/api.js`), and validate
  header == cookie in a dependency on unsafe methods (POST/PATCH/PUT/DELETE). `samesite="lax"`
  already blocks most cross-site form posts; the token closes the gap.
- **CORS with credentials.** Set `allow_credentials=True` on the CORS middleware and replace any
  wildcard origin with the explicit frontend origin(s) from `CORS_ORIGINS` (wildcard + credentials
  is rejected by browsers). Frontend `fetch` must send `credentials: "include"`.
- **Frontend.** Remove `localStorage` token storage in `shared/api/api.js`; rely on the cookie
  for REST. For Socket.IO, fetch a short-lived token from a small authenticated endpoint (or keep
  the Bearer fallback) since WS cannot read httpOnly cookies cross-origin reliably.
- **Rollout.** Ship cookie issuance + dependency dual-read first (header still works), migrate the
  frontend, then drop `localStorage`. No DB or token-format changes required.

## 11. External integrations

| Service | Use | Code |
|---|---|---|
| Stripe | PaymentIntents + Connect Accounts v2 payouts | `services/payment_service.py`, `payout_service.py`, `routers/webhooks.py` |
| AWS S3 | listing/inspection photos, presigned PUT | `services/uploads_service.py` |
| Resend | transactional email / verification | `services/mail_service.py` |
| Google Maps | browse map + host location picker | frontend `GoogleMapsProvider` |
| Google OAuth | sign-in | `services/auth_service.py` |
| NHTSA vPIC | VIN decode | `services/listing_service.py` |
| Redis | Socket.IO manager + ARQ queue | `asgi.py`, `jobs/booking_sweep.py` |

## 12. Environment variables

Backend settings are defined in `backend/vroom/core/config.py` (`Settings`), the source of
truth (`.env.example` is the dev sample, `.env.production.example` the prod checklist). Read
by `Settings`: `DATABASE_URL`, `DB_POOL_MIN`, `DB_POOL_MAX`, `PORT`, `DEBUG`, `CORS_ORIGINS`,
`JWT_SECRET`, `JWT_ALG`, `JWT_EXPIRES_HOURS`, `ALLOW_USER_LISTINGS`, `REQUIRE_VIN_FOR_P2P`,
`AWS_REGION`, `S3_BUCKET_NAME`, `S3_PRESIGN_TTL_SECONDS`, `STRIPE_SECRET_KEY`,
`STRIPE_WEBHOOK_SECRET`, `STRIPE_CONNECT_BUSINESS_NAME`, `STRIPE_CONNECT_BUSINESS_URL`,
`STRIPE_CONNECT_SUPPORT_EMAIL`, `STRIPE_CONNECT_API_VERSION`, `GOOGLE_OAUTH_CLIENT_ID`,
`RESEND_API_KEY`, `MAIL_FROM`, `FRONTEND_BASE_URL`, `REDIS_URL`, `RATELIMIT_ENABLED`,
`BOOKING_SWEEP_ENABLED`, `BOOKING_SWEEP_INTERVAL_SEC`, `UPLOAD_SWEEP_ENABLED`,
`UPLOAD_SWEEP_ORPHAN_GRACE_HOURS`, `TRIP_INSPECTION_RETENTION_DAYS`.
Not in `Settings` (read elsewhere/unused): `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` (boto3
reads from env directly), `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET` are also read via
`os.environ` in `payment_service.py`, and `LOG_LEVEL`/`TEST_DATABASE_URL` appear in env files
but are not loaded by `Settings` (`TEST_DATABASE_URL` is consumed by `tests/conftest.py`).

Frontend (`frontend/.env.example`, build-time `VITE_*`):
`VITE_API_URL`, `VITE_GOOGLE_MAPS_API_KEY`, `VITE_GOOGLE_MAP_ID`,
`VITE_STRIPE_PUBLISHABLE_KEY`, `VITE_GOOGLE_OAUTH_CLIENT_ID`.

Behavior: without `STRIPE_SECRET_KEY`, checkout auto-completes a mock payment (dev/CI).

## 13. Testing strategy

- Backend: pytest against a real Postgres (CI service container; `TEST_DATABASE_URL` locally).
  Do NOT run pytest against the dev app DB (`.env.example:4`).
- Frontend: Vitest (unit) + Playwright (e2e smoke). ESLint for lint.
- CI (`.github/workflows/ci.yml`): backend-lint (Ruff) → backend-test (Alembic + pytest) →
  frontend-lint/test/build → deploy → Playwright. `RATELIMIT_ENABLED=0` in CI.

## 14. Deployment and infrastructure

- Backend: Docker image (`backend/Dockerfile.prod`) → GHCR → Render deploy hook. Container
  runs `alembic upgrade head` then Gunicorn+UvicornWorker (`docker-entrypoint.prod.sh`).
- Frontend: Vercel, SPA rewrites (`frontend/vercel.json`), auto-deploy on push to `main`.
- Local: `docker-compose.yml` (redis, backend, worker, frontend; test profile).
- Details: `docs/production-deployment.md`.

## 15. Coding conventions

- Backend follows `.cursor/rules/fast-api.mdc` (Annotated `Depends`, Pydantic v2, PyJWT,
  domain-organized packages). Lint/format with Ruff.
- Data access per `.cursor/rules/data-access.mdc` (raw SQL default; ORM islands restricted).
- API JSON is camelCase via `schemas/camel.py`; DB/Python is snake_case.
- "Lazy senior dev" rule (`.cursor/rules/ponytail.mdc`): least code, mark intentional
  simplifications with `ponytail:` comments naming the ceiling/upgrade path.
- Services return status dicts (`{"status": ...}`) consumed by `core/errors.py`.

## 16. Known technical debt

- **Owner/P2P duplicate-VIN double-booking: closed.** `vehicle_asset.vin` is `UNIQUE` and
  `create_listing` always inserts a fresh `vehicle_asset`, so two owner listings cannot reference
  the same physical VIN. A duplicate-VIN create now returns a clean `validation_error`
  (`listing_service.py`, Postgres `23505` handling) rather than a 500.
- **Fleet-VIN booking race (narrower, still open):** this applies only to *fleet* listing rows
  that share the free-text `vehicle_listing.fleet_vehicle_vin` (a different column from the unique
  `vehicle_asset.vin`). The overlap check (`booking_service._has_active_booking_conflict`) accounts
  for sibling rows sharing `fleet_vehicle_vin`, but `create_booking` takes `SELECT … FOR UPDATE`
  on only the single `vehicle_listing` row being booked, and there is no DB exclusion constraint on
  `fleet_vehicle_vin`. Risk: concurrent bookings of two fleet listing rows sharing one
  `fleet_vehicle_vin` are not serialized by that lock (`booking_service.py:200-297`).
- **Status fields:** `payment.status`, `host_payout.status`, `owner_profile.verification_status`
  now carry DB CHECK constraints (migration `000012`); `vehicle_listing.status` is still
  governed by the status/active consistency CHECK rather than an enum.
- **Payment failure states unmodeled in the service:** the CHECK permits
  `failed`/`refunded`/`canceled`, but `payment_service.py` only writes `pending`→`succeeded`.
- **Auth gaps:** JWT in `localStorage`; no password reset. (Email verification tokens now
  expire after 24h — migration `000013`.)
- **Duplicated/denormalized fields:** `vehicle_listing` caches asset spec columns (trigger-
  synced); multiple geography systems (`area`/`branch` vs `region` vs `city_zone`);
  `latitude/longitude` vs `lat/lng` naming.
- **Schema-only fleet/ops tables** without service code.

## 17. Important invariants

- `db/schema.sql` is the canonical schema; the Alembic baseline loads it. After any
  migration, update `db/schema.sql` to match.
- One `payment` and at most one `host_payout` per booking (unique indexes).
- Bookings are never hard-deleted (FK RESTRICT preserves history); listings soft-delete.
- All DB writes go through `get_connection()` + explicit `conn.commit()`; status-changing
  flows take `SELECT … FOR UPDATE` row locks before mutating.
- API payloads are camelCase; never return raw ORM objects (return dicts).
- Money is stored in integer cents (`amount_cents`); currency default `cad`.
- Pytest must target a test DB, never the dev/prod app DB.

## 18. Rules future agents must follow

- Do not modify files during audits/read-only tasks.
- Keep raw-SQL data-access pattern; do not introduce ORM into core services without explicit
  request (`.cursor/rules/data-access.mdc`).
- Any schema change = Alembic revision **and** matching `db/schema.sql` update.
- Preserve camelCase API contract (`schemas/camel.py`); coordinate FE/BE field changes.
- Add a row lock for any new booking/listing/payment state transition. For **fleet** logic,
  remember the existing `FOR UPDATE` locks only one `vehicle_listing` row — sibling rows
  sharing a `fleet_vehicle_vin` are not covered (see §16); account for this in new flows.
- Do not rename "Metropolis" ↔ "Vroom"; they are the same system (codename vs brand, see §1).
- Never log secrets/PII (`password_hash`, tokens, Stripe ids, VIN); never commit `.env`.
- Validate at trust boundaries; keep generic external error messages (`core/errors.py`).
- Follow `.cursor/rules/fast-api.mdc` and `ponytail.mdc`; leave one runnable check for
  non-trivial logic.

## 19. Unknown or unverified areas

- Multiple listing rows sharing one `fleet_vehicle_vin` is by design (both search availability
  and booking-conflict SQL join siblings on it); whether seed/prod data actually creates such
  duplicates in practice is not confirmed.
- `hydrate_listing_rows` (`marketplace_common.py`) batches images/ratings/features with
  `WHERE … = ANY(%s)` queries keyed by all listing ids (not N+1); verified, no longer a
  concern.
- Actual production CORS/Swagger exposure (depends on deployed env values, not code).
- Live behavior of schema-only fleet/ops subsystems (no service code located).
- Production monitoring/analytics tooling — none found in code; unverified externally.

## 20. Keeping this document updated

- Treat this as architectural reference, not task history. Update on structural changes:
  new domain/service, schema change, auth/payment flow change, new integration, or deploy
  topology change.
- When updating: cite exact file paths; keep "current behavior" vs "recommendation"
  separate; do not paste large code blocks; do not invent unverified facts (mark as
  Unknown).
- When a debt item in §16 is fixed, move it out of debt and update the relevant section +
  §17 invariants.
- Keep in sync with `docs/architecture-summary.md`, `docs/database-schema.md`, and
  `.cursor/rules/*`. If they conflict, the code + `db/schema.sql` win; fix the doc.
