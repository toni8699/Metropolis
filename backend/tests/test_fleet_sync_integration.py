"""Integration tests for fleet sync and admin fleet listings.

Requires: running API + DATABASE_URL.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import psycopg2
import pytest
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_URL = os.environ.get("INTEGRATION_API_URL", "http://localhost:5000").rstrip("/")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

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


def _register(prefix: str, admin: bool = False) -> tuple[str, int]:
    email = f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"
    role = "admin" if admin else "user"
    resp = _api(
        "POST",
        "/api/auth/register",
        json={"email": email, "password": "FleetTest123!", "fullName": prefix, "role": role},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    return body["token"], int(body["user"]["userId"])


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
    admin_token, _ = _register("fleet-admin-list", admin=True)
    resp = _api("GET", "/api/listings?scope=fleet", token=admin_token)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "listings" in body


def test_admin_fleet_sync_idempotent():
    """Syncing the same fleet vehicle twice should not duplicate listings."""
    vin = f"{SYNC_VIN_PREFIX}{uuid.uuid4().hex[:8].upper()}"
    _seed_fleet_vehicle(vin)
    admin_token, _ = _register("fleet-admin-sync", admin=True)

    resp1 = _api("POST", "/api/fleet/sync", token=admin_token)
    assert resp1.status_code == 200, resp1.text

    resp2 = _api("POST", "/api/fleet/sync", token=admin_token)
    assert resp2.status_code == 200, resp2.text

    listings_resp = _api("GET", "/api/listings?scope=fleet", token=admin_token)
    assert listings_resp.status_code == 200
    listings = listings_resp.json().get("listings", [])
    vins = [li.get("fleetVehicleVin") for li in listings]
    assert vins.count(vin) <= 1, "Sync should not create duplicate listings for the same VIN"


def test_relocation_simulation_returns_result():
    admin_token, _ = _register("fleet-admin-reloc", admin=True)
    resp = _api("GET", "/api/simulations/relocation", token=admin_token)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "relocationNeeded" in body
    assert "moves" in body


def test_non_admin_cannot_run_relocation():
    token, _ = _register("fleet-renter-reloc")
    resp = _api("GET", "/api/simulations/relocation", token=token)
    assert resp.status_code == 403, resp.text
