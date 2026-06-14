"""Fresh single baseline for current Metropolis schema.

Revision ID: 000001_new_base
Revises:
Create Date: 2026-06-14
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from sqlalchemy import text

from alembic import op

revision: str = "000001_new_base"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _project_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here.parents[3], here.parents[2].parent):
        if (candidate / "db" / "schema.sql").is_file():
            return candidate
    raise FileNotFoundError("Could not locate db/schema.sql from Alembic revision.")


def _read_schema_sql() -> str:
    schema_path = _project_root() / "db" / "schema.sql"
    return schema_path.read_text(encoding="utf-8")


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    row = bind.execute(
        text("SELECT to_regclass(:name)"),
        {"name": f"public.{table_name}"},
    ).scalar()
    return row is not None


def upgrade() -> None:
    # Empty database: bootstrap from the canonical snapshot only.
    # Existing databases (area already present) skip this revision body.
    if not _table_exists("area"):
        op.execute(_read_schema_sql())


def downgrade() -> None:
    # Baseline reset is intentionally non-reversible.
    pass
