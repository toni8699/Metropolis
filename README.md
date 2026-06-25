# Vroom

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
| **CI / deploy** | GitHub Actions on `main` / `develop` → lint + test → merge `main` deploys. |

Production setup: [docs/production-deployment.md](docs/production-deployment.md)

---

## Setup (one time)

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
# .env — DATABASE_URL, JWT_SECRET, AWS/S3
# frontend/.env.local — VITE_API_URL=http://localhost:5000, VITE_GOOGLE_MAPS_API_KEY

cd backend && uv sync --extra dev
cd ../frontend && npm install

docker compose up --build
```

| Local | URL |
|-------|-----|
| App | http://localhost:3000 |
| API | http://localhost:5000 |
| Docs | http://localhost:5000/docs · `/redoc` |

After `pyproject.toml` changes: `cd backend && uv sync --extra dev`.

---

## Workflow

```
edit  →  lint / test  →  PR to main or develop  →  CI  →  merge main  →  deploy
```

**Before you push** (from repo root):

```bash
# Backend
cd backend && uv run ruff check .
cd backend && uv run ruff format --check .
cd backend && uv run pytest tests -v

# Frontend
cd frontend && npm run lint
cd frontend && npm test
```

**CI** (`.github/workflows/ci.yml`) runs the same on every push/PR to `main` or `develop`: Ruff → backend pytest → frontend lint/test/build. Push to `main` also builds the backend image, deploys to Render, and runs Playwright smoke.

**Prod:** backend via Render (GHCR image), frontend via Vercel. Secrets live in Render / Vercel / GitHub — not in the repo.

**DB changes:** new Alembic revision → `docker compose exec backend alembic upgrade head` → update `db/schema.sql`.

More detail: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Testing

| What | Command |
|------|---------|
| Backend (day to day) | `cd backend && uv run pytest tests -v` |
| Backend lint | `cd backend && uv run ruff check .` and `uv run ruff format --check .` |
| Frontend | `cd frontend && npm test` |
| Frontend lint | `cd frontend && npm run lint` |
| Full backend suite + integration | see below |


**Full backend suite** (migrations, seed, API, all tests) — ephemeral local Postgres via Docker:

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml --profile test run --rm test
```

**E2E** (Playwright) — CI on `main` deploy; locally with app + API up:

```bash
cd frontend && npm run test:e2e
```

---

## Commands

```bash
docker compose up --build
docker compose build backend && docker compose up --build

docker compose exec backend alembic upgrade head
curl http://localhost:5000/api/health
```

[docs/architecture-summary.md](docs/architecture-summary.md)
