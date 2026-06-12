"""Add category sub-ratings to review table.

Revision ID: 000002_review_sub_ratings
Revises: 31f6267c43dc
Create Date: 2026-05-21
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000002_review_sub_ratings"
down_revision: str | None = "000001_sql_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE review
          ADD COLUMN IF NOT EXISTS cleanliness INT
            CHECK (cleanliness IS NULL OR cleanliness BETWEEN 1 AND 5),
          ADD COLUMN IF NOT EXISTS accuracy INT
            CHECK (accuracy IS NULL OR accuracy BETWEEN 1 AND 5),
          ADD COLUMN IF NOT EXISTS communication INT
            CHECK (communication IS NULL OR communication BETWEEN 1 AND 5);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE review
          DROP COLUMN IF EXISTS communication,
          DROP COLUMN IF EXISTS accuracy,
          DROP COLUMN IF EXISTS cleanliness;
        """
    )
