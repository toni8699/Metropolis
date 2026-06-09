"""Apply historical SQL migrations 001-011 (idempotent).

Revision ID: 000001_sql_baseline
Revises:
Create Date: 2026-05-21

For databases already migrated via db/migrations/*.sql manually, run `alembic stamp head` instead.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from shutil import which

# revision identifiers, used by Alembic.
revision = "000001_sql_baseline"
down_revision = None
branch_labels = None
depends_on = None


def _project_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here.parents[3], here.parents[2].parent):
        if (candidate / "db" / "migrations").is_dir():
            return candidate
    raise FileNotFoundError("Could not locate db/migrations directory from Alembic revision.")


MIGRATIONS_DIR = _project_root() / "db" / "migrations"

SQL_MIGRATIONS = (
    "001_marketplace.sql",
    "002_listing_vehicle_fields.sql",
    "003_s3_assets_and_regions.sql",
    "004_multi_role_rbac.sql",
    "005_simplify_rbac_to_user_admin.sql",
    "006_company_location_sources.sql",
    "007_listing_vehicle_specs.sql",
    "008_listing_rich_details.sql",
    "009_schema_standardization.sql",
    "010_drop_legacy_booking_tables.sql",
    "011_reviews.sql",
)


def _run_sql_files() -> None:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for SQL baseline migration.")

    if not which("psql"):
        raise RuntimeError("psql is required to apply SQL migrations.")

    for filename in SQL_MIGRATIONS:
        path = MIGRATIONS_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing migration file: {path}")
        subprocess.run(
            ["psql", database_url, "-v", "ON_ERROR_STOP=1", "-f", str(path)],
            check=True,
        )


def upgrade() -> None:
    _run_sql_files()


def downgrade() -> None:
    # Baseline is not reversible automatically.
    pass
