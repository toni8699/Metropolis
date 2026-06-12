# Contributing to Metropolis Nexus

---

## Database access pattern

**All database queries use raw `psycopg2` — not SQLAlchemy ORM.**

`backend/metropolis/models/sqlalchemy_models.py` contains a minimal stub so Flask-SQLAlchemy initialises; it is not used for queries. Do not add ORM queries there.

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

---

## Project structure

```
backend/metropolis/
  api/          # Flask blueprints — thin controllers (validate, auth, call service)
  services/     # Business logic + SQL
  schemas/      # Marshmallow request/response schemas
  models/       # SQLAlchemy stub (do not add ORM queries)
  auth.py       # JWT decorators: require_auth, require_admin
  db.py         # get_connection() factory
```

---

## Schema migrations

Use **Alembic** for all schema changes:

```bash
# Create a new migration
docker compose exec backend alembic revision --autogenerate -m "describe_change"

# Apply migrations
docker compose exec backend alembic upgrade head

# After applying, update the snapshot
# (copy current schema.sql from db)
```

The `db/migrations/` folder contains historical numbered SQL files — treat as read-only history. All new migrations go through `backend/alembic/versions/`.

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
| API docs | http://localhost:5000/docs |

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

Backend tests live in `backend/tests/` and `tests/` (root). Both paths are in `pytest.ini`.

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
