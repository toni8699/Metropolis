"""Integration tests for fleet sync and admin fleet listings.

Requires: running API + DATABASE_URL.
"""

from __future__ import annotations

import uuid

import psycopg2
import pytest
import requests
from conftest import integration_env

API_URL, DATABASE_URL = integration_env()

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DATABASE_URL must be set (project .env)",
)

SYNC_VIN_PREFIX = "FSSYNC"


def _api(method: str, path: str, *, json: dict | None = None, token: str | None = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, f"{API_URL}{path}", headers=headers, json=json, timeout=15)


def _register(prefix: str) -> tuple[str, int]:
    from auth_test_helpers import register_and_login_http

    email = f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"
    token = register_and_login_http(
        API_URL,
        DATABASE_URL,
        email=email,
        password="FleetTest123!",
        full_name=prefix,
    )
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM app_user WHERE email = %s", (email,))
            user_id = int(cur.fetchone()[0])
    return token, user_id


def _create_admin(prefix: str) -> tuple[str, int]:
    email = f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"
    from werkzeug.security import generate_password_hash

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_user (
                  email, password_hash, role, full_name, is_admin, is_verified
                )
                VALUES (%s, %s, 'ADMIN'::user_role, %s, TRUE, TRUE)
                RETURNING user_id
                """,
                (email, generate_password_hash("FleetTest123!"), prefix),
            )
            user_id = cur.fetchone()[0]
        conn.commit()

    login_resp = _api("POST", "/api/auth/login", json={"email": email, "password": "FleetTest123!"})
    assert login_resp.status_code == 200, login_resp.text
    return login_resp.json()["token"], user_id


def _seed_fleet_vehicle(vin: str) -> None:
    """Insert a fleet vehicle + necessary FK rows if absent."""
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO area (areaid, areaname) VALUES (98001, 'Fleet Sync Area')"
                " ON CONFLICT (areaid) DO NOTHING"
            )
            cur.execute(
                "INSERT INTO branch (branchid, areaid, city) VALUES (98001, 98001, 'SyncCity')"
                " ON CONFLICT (branchid) DO NOTHING"
            )
            cur.execute(
                """
                INSERT INTO vehicle_asset (
                  vin,
                  vehicle_category,
                  owner_type,
                  owner_party_name,
                  asset_status,
                  make,
                  model,
                  branch_id,
                  fleet_status
                )
                VALUES (
                  %s,
                  'STANDARD'::vehicle_category,
                  'COMPANY'::vehicle_owner_type,
                  'Company Fleet',
                  'ACTIVE'::vehicle_asset_status,
                  'SyncMake',
                  'SyncModel',
                  98001,
                  'Available'
                )
                ON CONFLICT (vin) DO UPDATE
                SET
                  branch_id = EXCLUDED.branch_id,
                  fleet_status = EXCLUDED.fleet_status,
                  asset_status = EXCLUDED.asset_status
                """,
                (vin,),
            )
        conn.commit()


# ---------------------------------------------------------------------------
# Admin fleet listing endpoints
# ---------------------------------------------------------------------------


def test_non_admin_cannot_access_fleet_admin():
    token, _ = _register("fleet-renter-nonadmin")
    resp = _api("GET", "/api/listings?scope=fleet", token=token)
    assert resp.status_code == 403, resp.text


def test_unauthenticated_cannot_access_fleet_admin():
    resp = _api("GET", "/api/listings?scope=fleet")
    assert resp.status_code == 401, resp.text


def test_admin_can_list_fleet_listings():
    admin_token, _ = _create_admin("fleet-admin-list")
    resp = _api("GET", "/api/listings?scope=fleet", token=admin_token)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "listings" in body


def test_admin_fleet_sync_idempotent():
    """Syncing the same fleet vehicle twice should not duplicate listings."""
    vin = f"{SYNC_VIN_PREFIX}{uuid.uuid4().hex[:8].upper()}"
    _seed_fleet_vehicle(vin)
    admin_token, _ = _create_admin("fleet-admin-sync")

    resp1 = _api("POST", "/api/fleet/sync", token=admin_token)
    assert resp1.status_code == 200, resp1.text

    resp2 = _api("POST", "/api/fleet/sync", token=admin_token)
    assert resp2.status_code == 200, resp2.text

    listings_resp = _api("GET", "/api/listings?scope=fleet", token=admin_token)
    assert listings_resp.status_code == 200
    listings = listings_resp.json().get("listings", [])
    vins = [li.get("fleetVehicleVin") for li in listings]
    assert vins.count(vin) <= 1, "Sync should not create duplicate listings for the same VIN"
