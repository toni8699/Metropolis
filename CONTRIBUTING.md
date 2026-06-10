# Contributing to Metropolis Nexus

## Database access pattern

- **Service layer:** use raw SQL via `psycopg2` and `metropolis.db.get_connection()`.
- **Schema changes:** add an Alembic revision under `backend/alembic/versions/` and update `db/schema.sql` when the snapshot should change.
- Do not add new SQLAlchemy ORM queries in services. Alembic may still use SQLAlchemy for migration metadata only.
- `sqlalchemy_models.py` is frozen (minimal stub for Flask-SQLAlchemy init); extend schema via `db/migrations/` only.

## API conventions

- Register endpoints as Flask blueprints under `backend/metropolis/api/`.
- Document routes with ApiFairy decorators so they appear in ReDoc at `/docs`.
- Protect non-public routes with `@require_auth()` or `@require_admin()` from `metropolis.auth`.

## Organizations schema

Tables `organizations` and `organization_members` exist from migration `004_multi_role_rbac.sql` but have **no runtime Python usage** yet. Do not build org admin UI unless explicitly scoped.

## Removed legacy APIs

The following were removed (unused by the React app):

- `GET /api/vehicles/available`
- `GET /api/reservations`

Fleet relocation simulation remains at `POST /api/admin/relocation/simulate` via `rental_service`.
