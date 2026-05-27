"""add foo column

Revision ID: 31f6267c43dc
Revises: 000001_sql_baseline
Create Date: 2026-05-21 13:17:23.966278

"""

from __future__ import annotations

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "31f6267c43dc"
down_revision: str | None = "000001_sql_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
