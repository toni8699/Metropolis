"""Add expiry timestamp for email verification tokens.

Revision ID: 000013_verification_token_expiry
Revises: 000012_status_check_constraints
Create Date: 2026-06-29
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000013_verification_token_expiry"
down_revision: str | None = "000012_status_check_constraints"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE app_user
          ADD COLUMN IF NOT EXISTS verification_token_expires_at TIMESTAMPTZ
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE app_user
          DROP COLUMN IF EXISTS verification_token_expires_at
        """
    )
