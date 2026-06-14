"""Fresh single baseline for current Metropolis schema.

Revision ID: 000001_new_base
Revises:
Create Date: 2026-06-14
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from alembic import op
from sqlalchemy import text

revision: str = "000001_new_base"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _project_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here.parents[3], here.parents[2].parent):
        if (candidate / "db" / "schema.sql").is_file():
            return candidate
    raise FileNotFoundError("Could not locate db/schema.sql from Alembic revision.")


def _read_schema_sql() -> str:
    schema_path = _project_root() / "db" / "schema.sql"
    return schema_path.read_text(encoding="utf-8")


def _read_migration_sql(filename: str) -> str:
    path = _project_root() / "db" / "migrations" / filename
    return path.read_text(encoding="utf-8")


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    row = bind.execute(
        text("SELECT to_regclass(:name)"),
        {"name": f"public.{table_name}"},
    ).scalar()
    return row is not None


def upgrade() -> None:
    # Base schema snapshot (fleet + marketplace core).
    # In CI/hosting, some environments may already have legacy tables created
    # outside Alembic; skip raw base bootstrap in that case to avoid duplicates.
    if not _table_exists("area"):
        op.execute(_read_schema_sql())

    # Re-apply historical SQL deltas that are not fully reflected in schema.sql.
    for sql_file in (
        "002_listing_vehicle_fields.sql",
        "003_s3_assets_and_regions.sql",
        "004_multi_role_rbac.sql",
        "005_simplify_rbac_to_user_admin.sql",
        "006_company_location_sources.sql",
        "007_listing_vehicle_specs.sql",
        "008_listing_rich_details.sql",
        "009_schema_standardization.sql",
        "010_drop_legacy_booking_tables.sql",
        "011_reviews.sql",
        "012_review_sub_ratings.sql",
        "013_listing_instant_book_pending_approval.sql",
    ):
        op.execute(_read_migration_sql(sql_file))

    # Trip chat tables.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS booking_message (
            message_id BIGSERIAL PRIMARY KEY,
            booking_id BIGINT NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
            sender_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
            message_text TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_booking_message_booking_created
          ON booking_message (booking_id, created_at)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS booking_chat_state (
            booking_id BIGINT NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
            last_read_message_id BIGINT REFERENCES booking_message(message_id) ON DELETE SET NULL,
            last_read_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (booking_id, user_id)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_booking_chat_state_user_booking
          ON booking_chat_state (user_id, booking_id)
        """
    )

    # Keep file upload scopes aligned with uploads_service.
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
    # Baseline reset is intentionally non-reversible.
    pass
