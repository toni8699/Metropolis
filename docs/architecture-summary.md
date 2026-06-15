# Metropolis Nexus — Architecture Summary

Peer-to-peer and company fleet car rental marketplace.

---

## High-level overview

```
┌─────────────┐     REST / JWT      ┌──────────────────┐
│  Vercel     │ ──────────────────► │  Render          │
│  React SPA  │     Socket.IO       │  Gunicorn+Uvicorn│
└─────────────┘ ◄────────────────── └────────┬─────────┘
                                             │
                    ┌────────────────────────┼────────────────┐
                    ▼                        ▼                ▼
              Neon Postgres              AWS S3            Stripe
              (psycopg2 + Alembic)    (presigned PUT)   (webhooks)
```

---

## Layers

### Frontend (`frontend/`)

React 18 + Vite 5 SPA, deployed on Vercel. All config via `VITE_*` env vars baked at build time.

| Concern | Library |
|---------|---------|
| Routing | React Router 6 (`/`, `/app/*`, `/host`, `/admin`) |
| Styling | Tailwind CSS |
| Map | `@react-google-maps/api` |
| Payments | `@stripe/react-stripe-js` + `StripePaymentForm` |
| Real-time chat | `socket.io-client` via `useBookingChat` hook |
| API client | `frontend/src/shared/api/api.js` (port 5000 default) |

Key pages: `MapBrowsePage`, `ListingDetailPage`, `BookingCheckoutPage`, `TripsPage`, `InboxPage`, `HostDashboardPage` (owner + admin modes via `mode` prop).

### Backend (`backend/`)

FastAPI ASGI app (`metropolis.asgi:app`), deployed on Render via Docker image pushed to GHCR.

| Concern | Detail |
|---------|--------|
| HTTP | FastAPI routers under `/api/*` and `/webhooks` |
| Auth | `PyJWT` Bearer tokens; `Depends(get_current_user)` / `require_admin` |
| Database | `psycopg2` raw SQL via `get_connection()`; **no ORM queries** |
| Real-time | `python-socketio` ASGI + Redis manager for multi-worker |
| API docs | FastAPI OpenAPI — Swagger at `/docs`, ReDoc at `/redoc` |
| Rate limits | slowapi (disabled in CI: `RATELIMIT_ENABLED=0`) |
| Background jobs | ARQ worker (`metropolis.jobs.booking_sweep`) via Redis |
| File uploads | `boto3` presigned PUT URLs to S3 |
| Payments | Stripe PaymentIntents (`payment_service.py`); mock path when no key set |

Service modules: `auth_service`, `listing_service`, `booking_service`, `fleet_service`, `payment_service`, `kyc_service`, `message_service`, `review_service`, `uploads_service`.

### Database (`db/`)

Neon PostgreSQL. Corporate geography (`area`, `branch`) plus marketplace tables (`app_user`, `vehicle_listing`, `booking`, `payment`, `review`, …) and fleet asset tables (`vehicle_asset`, …).

**Migrations:** Alembic (`backend/alembic/versions/`). Baseline revision `000001_new_base` loads `db/schema.sql` on an empty database. After any revision, update `db/schema.sql` to match live schema.

For details, see [architecture-diagrams.md](architecture-diagrams.md).

---

## Request lifecycle

1. Browser → `fetch` via `frontend/src/shared/api/api.js` → FastAPI router
2. Router validates JWT (`Depends`) and request body/query (Pydantic)
3. Router calls a service function
4. Service runs raw SQL via `psycopg2` `get_connection()` and returns a plain dict
5. Router returns a Pydantic response model → JSON (camelCase via `CamelModel`)

---

## Real-time chat

Socket.IO rooms named `booking_{id}`. JWT verified on `connect`. Redis backs broadcast across Gunicorn Uvicorn workers on Render.

---

## Payment flow

1. `POST /api/bookings` → booking created with status `PENDING`
2. `POST /api/bookings/:id/payments` → `payment_service` creates a Stripe PaymentIntent (or returns `mock: true` in dev/CI)
3. Frontend confirms via `@stripe/react-stripe-js`
4. On success: booking transitions to `CONFIRMED` (instant-book / fleet) or `PENDING_APPROVAL` (host-approval P2P)
5. Stripe webhook (`/webhooks/stripe`) handles async confirmation edge cases

---

## CI / Deploy

```
push main
  → backend-lint (Ruff)
  → backend-test (Postgres service + Alembic + uvicorn + pytest)
  → frontend-lint (ESLint) + frontend-test (Vitest) + frontend-build
  → deploy: GHCR image → Render deploy hook
  → e2e: Playwright smoke tests
```

Vercel auto-deploys the frontend on every push to `main`.
