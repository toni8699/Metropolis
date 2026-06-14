"""booking_chat_state for per-user read tracking in booking chat.

Revision ID: 000008_booking_chat_state
Revises: 000007_user_profile
Create Date: 2026-06-14
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000008_booking_chat_state"
down_revision: str | None = "000007_user_profile"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE booking_chat_state (
            booking_id BIGINT NOT NULL
                REFERENCES booking(booking_id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL
                REFERENCES app_user(user_id) ON DELETE CASCADE,
            last_read_message_id BIGINT
                REFERENCES booking_message(message_id) ON DELETE SET NULL,
            last_read_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (booking_id, user_id)
        );
        """
    )
    op.execute(
        """
        CREATE INDEX idx_booking_chat_state_user_booking
            ON booking_chat_state (user_id, booking_id);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS booking_chat_state;")
