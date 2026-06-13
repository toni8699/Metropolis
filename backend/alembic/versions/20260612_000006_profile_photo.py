"""Add profile_photo_url to app_user and USER_AVATAR upload scope.

Revision ID: 000006_profile_photo
Revises: 000005_payment
Create Date: 2026-06-12
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000006_profile_photo"
down_revision: str | None = "000005_payment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE app_user
        ADD COLUMN IF NOT EXISTS profile_photo_url TEXT
        """
    )
    op.execute(
        """
        ALTER TABLE file_asset
        DROP CONSTRAINT IF EXISTS file_asset_scope_check
        """
    )
    op.execute(
        """
        ALTER TABLE file_asset
        ADD CONSTRAINT file_asset_scope_check
        CHECK (scope IN ('FLEET', 'OWNER_LISTING', 'USER_DOC', 'USER_AVATAR'))
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE file_asset
        DROP CONSTRAINT IF EXISTS file_asset_scope_check
        """
    )
    op.execute(
        """
        ALTER TABLE file_asset
        ADD CONSTRAINT file_asset_scope_check
        CHECK (scope IN ('FLEET', 'OWNER_LISTING', 'USER_DOC'))
        """
    )
    op.execute(
        """
        ALTER TABLE app_user
        DROP COLUMN IF EXISTS profile_photo_url
        """
    )
