"""booking_message table for renter/host trip chat.

Revision ID: 000004_booking_message
Revises: 000003_instant_book
Create Date: 2026-05-28
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000004_booking_message"
down_revision: str | None = "000003_instant_book"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE booking_message (
            message_id BIGSERIAL PRIMARY KEY,
            booking_id BIGINT NOT NULL
                REFERENCES booking(booking_id) ON DELETE CASCADE,
            sender_id BIGINT NOT NULL
                REFERENCES app_user(user_id) ON DELETE CASCADE,
            message_text TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        """
        CREATE INDEX idx_booking_message_booking_created
            ON booking_message (booking_id, created_at);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS booking_message;")
