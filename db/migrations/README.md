# db/migrations — Baseline SQL fragments (read-only)

These numbered `.sql` files are read by the Alembic fresh baseline revision
(`backend/alembic/versions/20260614_000001_new_base.py`) to reconstruct the
current schema from scratch.

**Do not add new migration files here.**

All new schema changes must go through **Alembic**:

```bash
# Create a new revision
docker compose exec backend alembic revision -m "describe_change"

# Apply all pending migrations
docker compose exec backend alembic upgrade head
```

Active migration files live in `backend/alembic/versions/`.

The current full schema snapshot is in `db/schema.sql`.
