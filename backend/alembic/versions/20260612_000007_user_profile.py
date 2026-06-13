"""Add driver profile fields to app_user.

Revision ID: 000007_user_profile
Revises: 000006_profile_photo
Create Date: 2026-06-12
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000007_user_profile"
down_revision: str | None = "000006_profile_photo"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE app_user
        ADD COLUMN IF NOT EXISTS lives VARCHAR(100),
        ADD COLUMN IF NOT EXISTS about TEXT,
        ADD COLUMN IF NOT EXISTS languages VARCHAR(150),
        ADD COLUMN IF NOT EXISTS work VARCHAR(100),
        ADD COLUMN IF NOT EXISTS is_approved_to_drive BOOLEAN NOT NULL DEFAULT FALSE
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE app_user
        DROP COLUMN IF EXISTS lives,
        DROP COLUMN IF EXISTS about,
        DROP COLUMN IF EXISTS languages,
        DROP COLUMN IF EXISTS work,
        DROP COLUMN IF EXISTS is_approved_to_drive
        """
    )
