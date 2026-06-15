# Contributing to Metropolis Nexus

---

## Database access pattern

**Default: raw `psycopg2` via `get_connection()` — not an ORM.**

Core marketplace paths (auth, listings, bookings, payments, fleet, search, messages, reviews) stay raw SQL. Pydantic schemas (`schemas/*_models.py`) are for HTTP only; they are not database models.

To query the database in a service:

```python
from metropolis.db import get_connection
from psycopg2.extras import RealDictCursor

with get_connection() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM app_user WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
    conn.commit()  # required for writes
```

### ORM islands (exception, not the default)

SQLAlchemy ORM is allowed **only** for a new, self-contained feature that meets **all** of:

1. **New tables** (or tables not read/written by existing raw-SQL services).
2. **No cross-transaction with core flows** — e.g. not inside booking payment, conflict checks, or `FOR UPDATE` locks on `booking` / `vehicle_listing`.
3. **Bounded service** — one module under `services/` (e.g. `notification_service.py`), not sprinkled into `booking_service.py` / `listing_service.py`.
4. **Full stack for that island** — SQLAlchemy models in `models/`, Alembic revision, update `db/schema.sql`, tests use session/fixtures (not `get_connection` mocks).
5. **API shape unchanged** — services still return plain dicts; Pydantic models serialize at the router boundary; no ORM objects leak to routers.

**Start an ORM island when:** the feature is mostly CRUD, owns its tables, and would not join the core booking/listing graph in the same transaction.

**Do not start an ORM island when:** the change touches existing core tables, needs complex SQL (bbox search, fleet sync, booking locks), or is “just a few queries” in an existing service — extend raw SQL instead.

**Never:** SQLAlchemy init with stub models and no queries; ORM + raw SQL on the same table in the same service; partial models for tables still owned by raw SQL elsewhere.

When adding an island, document it in the service module docstring and add a one-line note under `models/README` (create if needed) listing which tables are ORM-backed.

---

## Project structure

```
backend/metropolis/
  routers/       # FastAPI route handlers — thin controllers (validate, auth, call service)
  services/      # Business logic + SQL
  schemas/       # Pydantic request/response models (*_models.py, camel.py)
  dependencies/  # FastAPI Depends (auth.py)
  core/          # config, db pool, errors, limiter
  asgi.py        # CombinedASGI: Socket.IO + FastAPI
  db.py          # get_connection() factory (services)
```

---

## Schema migrations

**Canonical snapshot:** `db/schema.sql` (full live schema).

**Incremental changes:** Alembic revisions in `backend/alembic/versions/`.

```bash
# Create a new migration
docker compose exec backend alembic revision -m "describe_change"

# Apply migrations
docker compose exec backend alembic upgrade head

# After applying, update db/schema.sql to match the final schema
```

Fresh database bootstrap: `alembic upgrade head` runs `db/schema.sql` once when
the database is empty. CI seeds test rows via `backend/scripts/seed_ci_database.py`.

---

## Running locally

```bash
cp .env.example .env
# Fill DATABASE_URL, JWT_SECRET, AWS/S3 keys

docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:5000 |
| API docs | http://localhost:5000/docs (Swagger) · `/redoc` |

---

## Tests

```bash
# Backend unit + integration tests (backend must be running)
docker compose --profile test run --rm test

# Frontend unit tests
cd frontend && npm test

# Lint
cd backend && ruff check metropolis tests
cd frontend && npm run lint
```

Backend tests live in `backend/tests/`. `conftest.py` loads project `.env` for integration tests.

---

## Environment variables

| Variable | Required | Notes |
|----------|----------|-------|
| `DATABASE_URL` | Yes | Postgres connection string |
| `JWT_SECRET` | Yes | Must be strong in production |
| `STRIPE_SECRET_KEY` | No | Omit for dev/CI — uses mock payment path |
| `STRIPE_WEBHOOK_SECRET` | No | Required only for webhook verification |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `S3_BUCKET` | No | Required for photo/KYC uploads |
| `GOOGLE_OAUTH_CLIENT_ID` | No | Required for Google sign-in |
| `FLASK_DEBUG` | No | Set to `0` in production |

Security checks in `metropolis/security.py` block `FLASK_DEBUG=0` with a weak `JWT_SECRET` or wildcard CORS.
