"""Add email verification columns to app_user.

Revision ID: 000002_email_verification
Revises: 000001_new_base
Create Date: 2026-06-17
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000002_email_verification"
down_revision: str | None = "000001_new_base"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE app_user
          ADD COLUMN IF NOT EXISTS is_verified BOOLEAN NOT NULL DEFAULT FALSE,
          ADD COLUMN IF NOT EXISTS verification_token TEXT
        """
    )
    op.execute(
        """
        UPDATE app_user
        SET is_verified = TRUE
        WHERE is_verified = FALSE
          AND verification_token IS NULL
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE app_user
          DROP COLUMN IF EXISTS verification_token,
          DROP COLUMN IF EXISTS is_verified
        """
    )
