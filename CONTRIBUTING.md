# Contributing to Vroom

---

## Database access pattern

**Default: raw `psycopg2` via `get_connection()` — not an ORM.**

Core marketplace paths (auth, listings, bookings, payments, fleet, search, messages, reviews) stay raw SQL. Pydantic schemas (`schemas/*_models.py`) are for HTTP only; they are not database models.

To query the database in a service:

```python
from vroom.core.db import get_connection
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
backend/vroom/
  routers/       # FastAPI route handlers — thin controllers (validate, auth, call service)
  services/      # Business logic + SQL
  schemas/       # Pydantic request/response models (*_models.py, camel.py)
  dependencies/  # FastAPI Depends (auth.py)
  core/          # config, db pool, errors, limiter
  asgi.py        # CombinedASGI: Socket.IO + FastAPI
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

See [README.md — Setup](README.md#setup-one-time). Short version:

```bash
cp .env.example .env && cp frontend/.env.example frontend/.env.local
cd backend && uv sync --extra dev && cd ../frontend && npm install
docker compose up --build
```

---

## Tests

### Before a PR

```bash
cd backend && uv run ruff check .
cd backend && uv run ruff format --check .
cd backend && uv run pytest tests -v

cd frontend && npm run lint && npm test
```

CI runs the same checks on push/PR to `main` or `develop`.

### Backend

| Layer | Location | Needs DB? |
|-------|----------|-----------|
| Unit | `backend/tests/test_*_unit.py`, mocks | No |
| Integration | `backend/tests/test_*_integration.py`, `test_fastapi_auth.py` | Yes — local Postgres + API |

```bash
cd backend && uv sync --extra dev   # first time / after pyproject change
uv run pytest tests -v              # unit tests; integration skipped if no test DB
```

Full suite (what CI runs):

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml --profile test run --rm test
```

That starts `postgres_test`, migrates, seeds `scripts/seed_ci_database.py`, starts the API, runs all of `pytest`.

### Frontend

```bash
cd frontend && npm test        # Vitest — src/**/*.test.{js,jsx}
cd frontend && npm run lint
cd frontend && npm run build   # CI also checks production build
```

E2E: `npm run test:e2e` (Playwright, `frontend/e2e/`). CI smoke runs on push to `main` after deploy.

### Adding tests

- Pure logic / service helpers → `test_*_unit.py`, mock `get_connection` or external clients.
- HTTP + database flows → `test_*_integration.py`; use the Docker test command above before merging.
- New integration file → add filename to `_INTEGRATION_TEST_FILES` in `backend/tests/conftest.py`.

---

## Dependencies

Source of truth: `backend/pyproject.toml`. Lockfile: `backend/uv.lock`.

```bash
cd backend
uv sync --extra dev          # local dev + test tools
uv sync --frozen --extra dev # CI — exact pins
```

Docker prod images use `backend/requirements.txt` (prod export, no dev). After changing `pyproject.toml`:

```bash
cd backend
uv lock
uv export --frozen --no-dev -o requirements.txt
```


## Environment variables

| Variable | Required | Notes |
|----------|----------|-------|
| `DATABASE_URL` | Yes | Postgres connection string |
| `JWT_SECRET` | Yes | Must be strong in production |
| `STRIPE_SECRET_KEY` | No | Omit for dev/CI — uses mock payment path |
| `STRIPE_WEBHOOK_SECRET` | No | Required only for webhook verification |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `S3_BUCKET` | No | Required for photo/KYC uploads |
| `GOOGLE_OAUTH_CLIENT_ID` | No | Required for Google sign-in |
| `DEBUG` | No | Set to `0` in production |

Security checks in `vroom/security.py` block `DEBUG=0` with a weak `JWT_SECRET` or wildcard CORS.
