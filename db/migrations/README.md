# db/migrations — Historical SQL (read-only)

These numbered `.sql` files (`000_initial_clean.sql` through `014_*.sql`) are a **read-only historical record** of the schema evolution before Alembic was adopted.

**Do not add new migration files here.**

All schema changes must go through **Alembic**:

```bash
# Create a new revision
docker compose exec backend alembic revision -m "describe_change"

# Apply all pending migrations
docker compose exec backend alembic upgrade head
```

Active migration files live in `backend/alembic/versions/`.

The current full schema snapshot is in `db/schema.sql`.
