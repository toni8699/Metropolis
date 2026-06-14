# db/migrations — archived history

Historical numbered `.sql` fragments lived here before the schema was squashed
into a single canonical snapshot at `db/schema.sql`.

Those files are kept under `archive/` for reference only. **Do not add new
migration files here.**

## How schema changes work now

1. **Fresh database** — `alembic upgrade head` runs `db/schema.sql` once.
2. **Incremental change** — add a new Alembic revision under
   `backend/alembic/versions/`.
3. **After applying** — update `db/schema.sql` so the snapshot matches live
   schema.

```bash
# Create a new revision
docker compose exec backend alembic revision -m "describe_change"

# Apply pending migrations
docker compose exec backend alembic upgrade head
```

## Existing databases (already on old path)

If your DB already has tables and `alembic_version = 000001_new_base`, you
need no action — the squashed baseline is the same revision id with a simpler
body.

If you want a clean slate locally:

```bash
# destructive — drops all data
docker compose exec backend alembic downgrade base
docker compose exec backend alembic upgrade head
```

Or reset Neon / local Postgres and run `alembic upgrade head` only.
