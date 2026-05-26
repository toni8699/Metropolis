# Metropolis Nexus (DriveBnb)

React + Flask + Neon Postgres + S3. Copy `.env.example` → `.env` before first run.

## Start

```bash
docker compose up --build
```

- Frontend: http://localhost:3000  
- Backend: http://localhost:5000 · API docs: http://localhost:5000/docs  

Migrations run automatically on backend start.

## Rebuild

After `Dockerfile`, `requirements.txt`, or dependency changes:

```bash
docker compose build backend
docker compose up --build
```

Recompile backend lockfile (when `pyproject.toml` changes):

```bash
cd backend && uv pip compile pyproject.toml -o requirements.txt
docker compose build backend
```

## Database migrations

New migration:

```bash
cd backend
alembic revision -m "describe change"
# edit alembic/versions/<file>.py
```

Apply:

```bash
docker compose exec backend alembic upgrade head
```

Update `db/schema.sql` when the schema changes.

## Tests

Backend must be running and healthy.

```bash
# Compose test runner (waits for /api/health)
docker compose --profile test up --build backend test

# One-off (backend already up)
docker compose --profile test run --rm test

# Exec inside backend container
docker compose exec -e INTEGRATION_API_URL=http://127.0.0.1:5000 backend \
  pytest tests/test_search_integration.py -v
```

All integration tests:

```bash
docker compose exec -e INTEGRATION_API_URL=http://127.0.0.1:5000 backend \
  pytest tests -v
```

From host (API on localhost:5000):

```bash
cd backend && uv sync --extra dev
pytest tests/test_search_integration.py -v
```

## CI

GitHub Actions (`.github/workflows/ci.yml`) on push/PR to `main` or `develop`: Ruff, Postgres + migrations + pytest, Vite build. No GitHub secrets required for the default pipeline.

## Lint (before push)

Optional local check (matches CI backend-lint). Not hooked into `git commit`.

```bash
chmod +x scripts/lint.sh   # once
./scripts/lint.sh
```

Or manually:

```bash
cd backend && ruff check --fix metropolis tests scripts && ruff format metropolis tests scripts
ruff check tests && ruff format tests
```

CI still runs Ruff on every push/PR.
