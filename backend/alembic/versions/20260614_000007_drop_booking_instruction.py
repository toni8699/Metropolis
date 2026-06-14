"""Consolidate booking instructions into booking chat.

Revision ID: 000007_drop_booking_instruction
Revises: 000006_listing_lifecycle_unify
Create Date: 2026-06-14
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000007_drop_booking_instruction"
down_revision: str | None = "000006_listing_lifecycle_unify"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS booking_instruction")


def downgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS booking_instruction (
          instruction_id BIGSERIAL PRIMARY KEY,
          booking_id BIGINT NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
          owner_user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
          message TEXT NOT NULL,
          sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          read_at TIMESTAMPTZ
        )
        """
    )
