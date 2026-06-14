# Metropolis Nexus — Architecture Summary

Peer-to-peer and company fleet car rental marketplace (McGill Comp 421 project).

---

## High-level overview

```
┌─────────────┐     REST / JWT      ┌──────────────────┐
│  Vercel     │ ──────────────────► │  Render          │
│  React SPA  │     Socket.IO       │  Flask + Gunicorn│
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
| API client | `frontend/src/utils/api.js` (port 5000 default) |

Key pages: `MapBrowsePage`, `ListingDetailPage`, `BookingCheckoutPage`, `TripsPage`, `InboxPage`, `OwnerDashboardPage`, `AdminDashboardPage`.

### Backend (`backend/`)

Flask 3 monolith, deployed on Render via Docker image pushed to GHCR.

| Concern | Detail |
|---------|--------|
| HTTP | Flask blueprints under `/api/*` and `/webhooks` |
| Auth | `PyJWT` Bearer tokens; `require_auth` / `require_admin` decorators |
| Database | `psycopg2` raw SQL via `get_connection()`; **no ORM queries** |
| Real-time | Flask-SocketIO + eventlet; Redis as message queue for multi-worker |
| API docs | ApiFairy + Marshmallow at `/docs` |
| Rate limits | Flask-Limiter (disabled in CI: `RATELIMIT_ENABLED=0`) |
| File uploads | `boto3` presigned PUT URLs to S3 |
| Payments | Stripe PaymentIntents (`payment_service.py`); mock path when no key set |

Service modules: `auth_service`, `marketplace_service`, `booking_service`, `payment_service`, `listing_service`, `fleet_service`, `kyc_service`, `message_service`, `review_service`, `uploads_service`, `rental_service`.

### Database (`db/`)

Neon PostgreSQL. Hybrid schema: legacy fleet tables (`area`, `branch`, `vehicle`, `employee`) plus marketplace tables (`app_user`, `vehicle_listing`, `booking`, `payment`, `review`, …).

Migrations are managed by **Alembic** (`backend/alembic/versions/`) from a fresh single baseline (`000001_new_base`). The `db/migrations/` folder contains read-only SQL fragments consumed by that baseline revision.

For details, see [architecture-diagrams.md](architecture-diagrams.md).

---

## Request lifecycle

1. Browser → `fetch` via `frontend/src/utils/api.js` → Flask blueprint
2. Blueprint validates JWT (`require_auth`) and request schema (Marshmallow)
3. Blueprint calls a service function
4. Service runs raw SQL via `psycopg2` `get_connection()` and returns a plain dict
5. Blueprint serializes the dict through a Marshmallow response schema → JSON

---

## Real-time chat

Socket.IO rooms named `booking_{id}`. JWT verified on `connect`. Redis backs broadcast across Gunicorn workers on Render.

---

## Payment flow

1. `POST /api/bookings` → booking created with status `PENDING`
2. `POST /api/bookings/:id/payment-intent` → `payment_service` creates a Stripe PaymentIntent (or returns `mock: true` in dev/CI)
3. Frontend confirms via `@stripe/react-stripe-js`
4. On success: booking transitions to `CONFIRMED` (instant-book / fleet) or `PENDING_APPROVAL` (host-approval P2P)
5. Stripe webhook (`/webhooks/stripe`) handles async confirmation edge cases

---

## CI / Deploy

```
push main
  → backend-lint (Ruff)
  → backend-test (Postgres service + Alembic + pytest)
  → frontend-lint (ESLint) + frontend-test (Vitest) + frontend-build
  → deploy: GHCR image → Render deploy hook
  → e2e: Playwright smoke tests
```

Vercel auto-deploys the frontend on every push to `main`.
