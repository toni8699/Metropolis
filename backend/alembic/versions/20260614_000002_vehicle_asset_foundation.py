"""Canonical vehicle asset foundation for managed-host marketplace.

Revision ID: 000002_vehicle_asset_foundation
Revises: 000001_new_base
Create Date: 2026-06-14
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "000002_vehicle_asset_foundation"
down_revision: str | None = "000001_new_base"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Enums (idempotent)
    # ------------------------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
          CREATE TYPE vehicle_category AS ENUM ('STANDARD', 'LUXURY', 'TRUCK', 'EV');
        EXCEPTION
          WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          CREATE TYPE vehicle_owner_type AS ENUM ('INDEPENDENT_HOST', 'FLEET_OWNER', 'COMPANY');
        EXCEPTION
          WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          CREATE TYPE vehicle_asset_status AS ENUM ('ONBOARDING', 'ACTIVE', 'MAINTENANCE', 'RETIRED');
        EXCEPTION
          WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          CREATE TYPE listing_visibility_status AS ENUM ('DRAFT', 'PUBLISHED', 'HIDDEN');
        EXCEPTION
          WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          CREATE TYPE management_assignment_status AS ENUM ('PENDING', 'ACTIVE', 'TERMINATED');
        EXCEPTION
          WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          CREATE TYPE compliance_event_type AS ENUM (
            'PHYSICAL_INSPECTION',
            'DOCUMENT_VERIFICATION',
            'SAFETY_RUN',
            'WEIGHT_TOW_VERIFICATION'
          );
        EXCEPTION
          WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          CREATE TYPE compliance_result AS ENUM ('PASSED', 'FAILED');
        EXCEPTION
          WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          CREATE TYPE insurance_coverage_type AS ENUM ('HOST_PERSONAL', 'PLATFORM_FLEET', 'TRIP_COMMERCIAL');
        EXCEPTION
          WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          CREATE TYPE parking_provider_type AS ENUM ('PLATFORM_OWNED', 'PARTNER', 'HOST_PROVIDED');
        EXCEPTION
          WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          CREATE TYPE booking_access_type AS ENUM ('DAILY_RENTAL', 'MEMBERSHIP');
        EXCEPTION
          WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    # ------------------------------------------------------------------
    # Canonical vehicle asset + operational layer tables
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vehicle_asset (
          vehicle_id BIGSERIAL PRIMARY KEY,
          vin VARCHAR(17) UNIQUE,
          vehicle_category vehicle_category NOT NULL DEFAULT 'STANDARD',
          estimated_value DECIMAL(12,2) CHECK (estimated_value IS NULL OR estimated_value >= 0),
          owner_type vehicle_owner_type NOT NULL,
          owner_party_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
          owner_party_name VARCHAR(160),
          asset_status vehicle_asset_status NOT NULL DEFAULT 'ONBOARDING',
          make VARCHAR(80),
          model VARCHAR(80),
          model_year INT,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT vehicle_asset_owner_identity_check CHECK (
            owner_party_user_id IS NOT NULL OR owner_party_name IS NOT NULL
          ),
          CONSTRAINT vehicle_asset_vin_len_check CHECK (
            vin IS NULL OR char_length(vin) BETWEEN 11 AND 17
          )
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_vehicle_asset_owner ON vehicle_asset(owner_type, owner_party_user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_vehicle_asset_status ON vehicle_asset(asset_status)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS management_program (
          program_id BIGSERIAL PRIMARY KEY,
          name VARCHAR(120) NOT NULL UNIQUE,
          commission_rate DECIMAL(5,4) NOT NULL CHECK (commission_rate >= 0 AND commission_rate <= 1),
          included_services JSONB NOT NULL DEFAULT '[]'::jsonb,
          is_active BOOLEAN NOT NULL DEFAULT TRUE,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vehicle_management_assignment (
          assignment_id BIGSERIAL PRIMARY KEY,
          vehicle_id BIGINT NOT NULL REFERENCES vehicle_asset(vehicle_id) ON DELETE CASCADE,
          manager_party_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL,
          manager_party_name VARCHAR(160),
          program_id BIGINT NOT NULL REFERENCES management_program(program_id) ON DELETE RESTRICT,
          start_date DATE NOT NULL,
          end_date DATE,
          status management_assignment_status NOT NULL DEFAULT 'PENDING',
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT vehicle_mgmt_assignment_dates_check CHECK (
            end_date IS NULL OR end_date >= start_date
          ),
          CONSTRAINT vehicle_mgmt_assignment_manager_check CHECK (
            manager_party_user_id IS NOT NULL OR manager_party_name IS NOT NULL
          )
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_vehicle_mgmt_assignment_vehicle ON vehicle_management_assignment(vehicle_id, status)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vehicle_compliance_event (
          compliance_event_id BIGSERIAL PRIMARY KEY,
          vehicle_id BIGINT NOT NULL REFERENCES vehicle_asset(vehicle_id) ON DELETE CASCADE,
          event_type compliance_event_type NOT NULL,
          result compliance_result NOT NULL,
          effective_until TIMESTAMPTZ,
          metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
          recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          recorded_by_user_id BIGINT REFERENCES app_user(user_id) ON DELETE SET NULL
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vehicle_compliance_vehicle_type ON vehicle_compliance_event(vehicle_id, event_type, recorded_at DESC)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vehicle_insurance_policy (
          policy_id BIGSERIAL PRIMARY KEY,
          vehicle_id BIGINT NOT NULL REFERENCES vehicle_asset(vehicle_id) ON DELETE CASCADE,
          provider_name VARCHAR(120) NOT NULL,
          policy_number VARCHAR(120) NOT NULL,
          coverage_type insurance_coverage_type NOT NULL,
          effective_from TIMESTAMPTZ NOT NULL,
          effective_to TIMESTAMPTZ NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT vehicle_insurance_dates_check CHECK (effective_to > effective_from),
          CONSTRAINT vehicle_insurance_unique_policy UNIQUE (provider_name, policy_number)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vehicle_insurance_vehicle_dates ON vehicle_insurance_policy(vehicle_id, effective_from, effective_to)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS parking_hub (
          hub_id BIGSERIAL PRIMARY KEY,
          name VARCHAR(160) NOT NULL,
          latitude DECIMAL(9,6) NOT NULL CHECK (latitude BETWEEN -90 AND 90),
          longitude DECIMAL(9,6) NOT NULL CHECK (longitude BETWEEN -180 AND 180),
          provider_type parking_provider_type NOT NULL,
          area_id INT REFERENCES area(areaid) ON DELETE SET NULL,
          branch_id INT REFERENCES branch(branchid) ON DELETE SET NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_parking_hub_area_branch ON parking_hub(area_id, branch_id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS parking_spot_allocation (
          allocation_id BIGSERIAL PRIMARY KEY,
          hub_id BIGINT NOT NULL REFERENCES parking_hub(hub_id) ON DELETE CASCADE,
          vehicle_id BIGINT NOT NULL REFERENCES vehicle_asset(vehicle_id) ON DELETE CASCADE,
          spot_identifier VARCHAR(80) NOT NULL,
          valid_from TIMESTAMPTZ NOT NULL,
          valid_to TIMESTAMPTZ,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT parking_allocation_window_check CHECK (
            valid_to IS NULL OR valid_to > valid_from
          )
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_parking_allocation_vehicle_dates ON parking_spot_allocation(vehicle_id, valid_from, valid_to)"
    )

    # ------------------------------------------------------------------
    # Commercial layer extension: membership compatibility
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS membership_tier (
          tier_id BIGSERIAL PRIMARY KEY,
          code VARCHAR(40) NOT NULL UNIQUE,
          name VARCHAR(120) NOT NULL,
          rank_order INT NOT NULL DEFAULT 0,
          is_active BOOLEAN NOT NULL DEFAULT TRUE,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vehicle_membership_eligibility (
          eligibility_id BIGSERIAL PRIMARY KEY,
          vehicle_id BIGINT NOT NULL REFERENCES vehicle_asset(vehicle_id) ON DELETE CASCADE,
          tier_id BIGINT NOT NULL REFERENCES membership_tier(tier_id) ON DELETE CASCADE,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          UNIQUE (vehicle_id, tier_id)
        )
        """
    )

    # ------------------------------------------------------------------
    # Bridge existing marketplace tables to new canonical model
    # ------------------------------------------------------------------
    op.execute(
        """
        ALTER TABLE vehicle_listing
        ADD COLUMN IF NOT EXISTS vehicle_id BIGINT REFERENCES vehicle_asset(vehicle_id) ON DELETE SET NULL
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_vehicle_listing_vehicle_id ON vehicle_listing(vehicle_id)")

    op.execute(
        """
        ALTER TABLE vehicle_listing
        ADD COLUMN IF NOT EXISTS visibility_status listing_visibility_status NOT NULL DEFAULT 'PUBLISHED'
        """
    )
    op.execute(
        """
        ALTER TABLE booking
        ADD COLUMN IF NOT EXISTS access_type booking_access_type NOT NULL DEFAULT 'DAILY_RENTAL'
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE booking DROP COLUMN IF EXISTS access_type")
    op.execute("ALTER TABLE vehicle_listing DROP COLUMN IF EXISTS visibility_status")
    op.execute("DROP INDEX IF EXISTS idx_vehicle_listing_vehicle_id")
    op.execute("ALTER TABLE vehicle_listing DROP COLUMN IF EXISTS vehicle_id")

    op.execute("DROP TABLE IF EXISTS vehicle_membership_eligibility")
    op.execute("DROP TABLE IF EXISTS membership_tier")
    op.execute("DROP TABLE IF EXISTS parking_spot_allocation")
    op.execute("DROP TABLE IF EXISTS parking_hub")
    op.execute("DROP TABLE IF EXISTS vehicle_insurance_policy")
    op.execute("DROP TABLE IF EXISTS vehicle_compliance_event")
    op.execute("DROP TABLE IF EXISTS vehicle_management_assignment")
    op.execute("DROP TABLE IF EXISTS management_program")
    op.execute("DROP TABLE IF EXISTS vehicle_asset")

    op.execute("DROP TYPE IF EXISTS booking_access_type")
    op.execute("DROP TYPE IF EXISTS parking_provider_type")
    op.execute("DROP TYPE IF EXISTS insurance_coverage_type")
    op.execute("DROP TYPE IF EXISTS compliance_result")
    op.execute("DROP TYPE IF EXISTS compliance_event_type")
    op.execute("DROP TYPE IF EXISTS management_assignment_status")
    op.execute("DROP TYPE IF EXISTS listing_visibility_status")
    op.execute("DROP TYPE IF EXISTS vehicle_asset_status")
    op.execute("DROP TYPE IF EXISTS vehicle_owner_type")
    op.execute("DROP TYPE IF EXISTS vehicle_category")
