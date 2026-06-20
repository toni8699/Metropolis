"""Feature catalog + is_vin_verified on vehicle_asset.

Revision ID: 000004_feature_catalog
Revises: 000003_vehicle_realignment
Create Date: 2026-06-19
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000004_feature_catalog"
down_revision: str | None = "000003_vehicle_realignment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE ref_feature (
          feature_id SERIAL PRIMARY KEY,
          code VARCHAR(64) NOT NULL UNIQUE,
          name VARCHAR(120) NOT NULL UNIQUE,
          icon_key VARCHAR(64) NOT NULL DEFAULT 'Check',
          category VARCHAR(32) NOT NULL,
          sort_order INT NOT NULL DEFAULT 0,
          is_active BOOLEAN NOT NULL DEFAULT TRUE
        );

        INSERT INTO ref_feature (code, name, icon_key, category, sort_order) VALUES
          ('APPLE_CARPLAY', 'Apple CarPlay', 'Smartphone', 'Tech', 10),
          ('ANDROID_AUTO', 'Android Auto', 'Smartphone', 'Tech', 20),
          ('BLUETOOTH', 'Bluetooth', 'Bluetooth', 'Tech', 30),
          ('SUNROOF', 'Sunroof', 'Sun', 'Comfort', 40),
          ('HEATED_SEATS', 'Heated Seats', 'Snowflake', 'Comfort', 50),
          ('AWD', 'AWD', 'ShieldCheck', 'Safety', 60),
          ('BACKUP_CAMERA', 'Backup Camera', 'UploadCloud', 'Safety', 70),
          ('BLIND_SPOT_WARNING', 'Blind Spot Warning', 'ShieldCheck', 'Safety', 80),
          ('KEYLESS_ENTRY', 'Keyless Entry', 'KeyRound', 'Comfort', 90);

        CREATE TABLE listing_feature (
          listing_id BIGINT NOT NULL REFERENCES vehicle_listing(listing_id) ON DELETE CASCADE,
          feature_id INT NOT NULL REFERENCES ref_feature(feature_id) ON DELETE CASCADE,
          PRIMARY KEY (listing_id, feature_id)
        );

        CREATE INDEX idx_listing_feature_feature ON listing_feature(feature_id);

        INSERT INTO listing_feature (listing_id, feature_id)
        SELECT DISTINCT vl.listing_id, rf.feature_id
        FROM vehicle_listing vl
        CROSS JOIN LATERAL
          jsonb_array_elements_text(COALESCE(vl.features, '[]'::jsonb)) AS feat(name)
        JOIN ref_feature rf ON rf.name = feat.name
        ON CONFLICT DO NOTHING;

        ALTER TABLE vehicle_asset
          ADD COLUMN IF NOT EXISTS is_vin_verified BOOLEAN NOT NULL DEFAULT FALSE;

        UPDATE vehicle_asset
        SET is_vin_verified = TRUE
        WHERE vin IS NOT NULL;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE vehicle_asset
          DROP COLUMN IF EXISTS is_vin_verified;

        DROP TABLE IF EXISTS listing_feature;
        DROP TABLE IF EXISTS ref_feature;
        """
    )
