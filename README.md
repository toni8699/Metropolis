# Metropolis Nexus (DriveBnb)

Peer-to-peer and fleet car rental marketplace. Renters search, book, and pay; hosts manage listings; admins sync fleet inventory. Includes map browse, Stripe checkout, real-time trip chat, and host KYC review.

**Stack:** React + Vite · FastAPI + Socket.IO · Neon Postgres · AWS S3 · Stripe · Google Maps

---

## Architecture

```
┌─────────────┐     REST / JWT      ┌──────────────────┐
│  Vercel     │ ──────────────────► │  Render          │
│  React SPA  │     Socket.IO       │  Uvicorn + Gunicorn│
└─────────────┘ ◄────────────────── └────────┬─────────┘
                                             │
                    ┌────────────────────────┼────────────────┐
                    ▼                        ▼                ▼
              Neon Postgres              AWS S3            Stripe
              (psycopg2 + Alembic)    (presigned PUT)   (webhooks)
```

| Layer | Details |
|-------|---------|
| **Frontend** | `frontend/` — React 18, Vite, Tailwind. Env baked at build (`VITE_*`). |
| **Backend** | `backend/` — FastAPI, raw SQL services, OpenAPI at `/docs` (Swagger) and `/redoc`. |
| **Database** | `db/schema.sql` snapshot + Alembic (`alembic upgrade head` bootstraps empty DB). |
| **Local** | Docker Compose — backend `:5000`, frontend `:3000`, Redis for Socket.IO. |
| **CI / deploy** | GitHub Actions on `main` → test → push image to GHCR → Render deploy hook. |

Production setup: [docs/production-deployment.md](docs/production-deployment.md)

---

## Testing

**Do not run integration tests against Neon.** Your `.env` `DATABASE_URL` is for the dev app. Pytest integration tests create/delete rows — use an isolated Postgres instead.

### Backend (full suite)

Uses local Postgres via `docker-compose.test.yml` (never reads Neon):

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml --profile test run --rm test
```

This spins up `postgres_test`, runs migrations, seeds CI fixtures, starts the API, and runs `pytest`.

### Backend (unit tests only)

Safe even when `.env` points at Neon — no DB writes:

```bash
cd backend && uv sync --extra dev
uv run pytest tests -v -k "not integration"
# or only *_unit.py files:
uv run pytest tests/test_*_unit.py tests/test_auth_jwt_unit.py -v
```

### Frontend

```bash
cd frontend && npm test          # Vitest unit tests
cd frontend && npm run lint
```

E2E (Playwright) runs on CI after merge to `main`; locally:

```bash
cd frontend && npm run test:e2e   # needs app + API running
```

### CI (GitHub Actions)

On push/PR to `main` or `develop`: Ruff → backend pytest (ephemeral Postgres) → frontend lint/test/build. Push to `main` also deploys and runs Playwright smoke.

### Clean test junk from Neon dev DB

If you already polluted Neon with local pytest:

```bash
docker compose exec backend python scripts/purge_test_listings.py          # preview
docker compose exec backend python scripts/purge_test_listings.py --execute
```

---

## Dev flow

### 1. One-time setup

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
# Fill DATABASE_URL, JWT_SECRET, AWS/S3 in .env
# Fill VITE_API_URL=http://localhost:5000 and VITE_GOOGLE_MAPS_API_KEY in frontend/.env.local

docker compose up --build
```

| Local | URL |
|-------|-----|
| App | http://localhost:3000 |
| API | http://localhost:5000 |
| Docs | http://localhost:5000/docs (Swagger) · `/redoc` |

### 2. Daily loop

```
edit code  →  docker compose up  →  lint / test  →  PR  →  merge main  →  prod deploy
```

- **Local:** hot reload via compose volumes. Restart backend after env or dependency changes.
- **Prod:** push to `main` deploys backend (Render via GHCR) and frontend (Vercel). Secrets live in Render / Vercel / GitHub — not in the repo.
- **DB:** schema change → new Alembic revision → `docker compose exec backend alembic upgrade head` → update `db/schema.sql` to match. Fresh DB needs Alembic only (no manual `psql`).

### 3. Commands

```bash
# Start / rebuild
docker compose up --build
docker compose build backend && docker compose up --build

# Lint
cd backend && uv run ruff check metropolis tests
cd frontend && npm run lint && npm run test

# Backend deps (first time / after pyproject change)
cd backend && uv sync --extra dev

# See "Testing" section above for pytest / integration tests

# Migrations
docker compose exec backend alembic upgrade head
# Optional fresh reset for mock/local DB
docker compose exec backend alembic downgrade base && docker compose exec backend alembic upgrade head

# Health
curl http://localhost:5000/api/health
```

[docs/architecture-summary.md](docs/architecture-summary.md)
