"""Saved listings (user favorites).

Revision ID: 000008_saved_listings
Revises: 000007_search_filter_enums
Create Date: 2026-06-20
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000008_saved_listings"
down_revision: str | None = "000007_search_filter_enums"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS saved_listing
        (
          user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
          listing_id BIGINT NOT NULL REFERENCES vehicle_listing(listing_id) ON DELETE CASCADE,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          PRIMARY KEY (user_id, listing_id)
        );

        CREATE INDEX IF NOT EXISTS idx_saved_listing_user_created
          ON saved_listing(user_id, created_at DESC);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS saved_listing;")
