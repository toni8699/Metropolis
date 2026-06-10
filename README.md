# Metropolis Nexus (DriveBnb)

Peer-to-peer and fleet car rental marketplace. Renters search, book, and pay; hosts manage listings; admins sync fleet inventory. Includes map browse, Stripe checkout, real-time trip chat, and host KYC review.

**Stack:** React + Vite · Flask + Socket.IO · Neon Postgres · AWS S3 · Stripe · Google Maps

---

## Architecture

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

| Layer | Details |
|-------|---------|
| **Frontend** | `frontend/` — React 18, Vite, Tailwind. Env baked at build (`VITE_*`). |
| **Backend** | `backend/` — Flask monolith, raw SQL services, ApiFairy docs at `/docs`. |
| **Database** | `db/` — Postgres via Neon; Alembic migrations + `schema.sql` snapshot. |
| **Local** | Docker Compose — backend `:5000`, frontend `:3000`, Redis for Socket.IO. |
| **CI / deploy** | GitHub Actions on `main` → test → push image to GHCR → Render deploy hook. |

Production setup: [docs/production-deployment.md](docs/production-deployment.md)

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
| Docs | http://localhost:5000/docs |

### 2. Daily loop

```
edit code  →  docker compose up  →  lint / test  →  PR  →  merge main  →  prod deploy
```

- **Local:** hot reload via compose volumes. Restart backend after env or dependency changes.
- **Prod:** push to `main` deploys backend (Render via GHCR) and frontend (Vercel). Secrets live in Render / Vercel / GitHub — not in the repo.
- **DB:** schema change → Alembic revision → `docker compose exec backend alembic upgrade head` → update `db/schema.sql`.

### 3. Commands

```bash
# Start / rebuild
docker compose up --build
docker compose build backend && docker compose up --build

# Lint
cd backend && ruff check metropolis tests
cd frontend && npm run lint && npm run test

# Integration tests (backend must be running)
docker compose --profile test run --rm test

docker compose exec -e INTEGRATION_API_URL=http://127.0.0.1:5000 -e RATELIMIT_ENABLED=0 backend \
  bash -c 'pip install -q pytest requests python-dotenv && python -m pytest tests -v --tb=short'

# Migrations
docker compose exec backend alembic upgrade head

# Health
curl http://localhost:5000/api/health
```

More detail: [CONTRIBUTING.md](CONTRIBUTING.md) · [docs/architecture-summary.md](docs/architecture-summary.md)
