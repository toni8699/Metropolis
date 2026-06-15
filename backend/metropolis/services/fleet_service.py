from __future__ import annotations

import hashlib

from psycopg2.extras import RealDictCursor

from metropolis.db import get_connection
from metropolis.services.booking_rows import to_booking_row
from metropolis.services.marketplace_common import (
    _BOOKING_SELECT_SQL,
    _COMPANY_FLEET_FILTER,
    _HOST_LISTING_FILTER,
    CITY_COORDS,
    LISTING_SELECT_SQL,
    _fetch_dashboard_analytics,
    _simple_geohash,
    _upsert_listing_location,
    hydrate_listing_rows,
)

_VEHICLE_CATEGORY_OPTIONS = [
    {"vehicleCategory": "STANDARD", "name": "Standard"},
    {"vehicleCategory": "LUXURY", "name": "Luxury"},
    {"vehicleCategory": "TRUCK", "name": "Truck"},
    {"vehicleCategory": "EV", "name": "EV"},
]


def _fleet_coords(city: str, vin: str) -> tuple[float, float]:
    city_key = (city or "").lower()
    base = CITY_COORDS.get(city_key, (45.5017, -73.5673))
    digest = hashlib.sha256(vin.encode("utf-8")).hexdigest()
    lat_jitter = (int(digest[:4], 16) % 100) / 10000.0
    lng_jitter = (int(digest[4:8], 16) % 100) / 10000.0
    return base[0] + lat_jitter, base[1] + lng_jitter


class FleetService:
    def _resolve_company_location(self, cur, payload: dict) -> dict:
        source_type = str(payload.get("locationSourceType") or "").upper()
        branch_id = payload.get("branchId")
        parking_spot_id = payload.get("parkingSpotId")
        selected_area_id = payload.get("areaId")
        if source_type not in {"BRANCH", "PARKING_SPOT"}:
            return {
                "status": "validation_error",
                "message": "locationSourceType must be BRANCH or PARKING_SPOT.",
            }

        if source_type == "BRANCH":
            if not branch_id:
                return {
                    "status": "validation_error",
                    "message": "branchId required for BRANCH source.",
                }
            cur.execute(
                """
                SELECT b.branchid, b.areaid, b.address, b.lat, b.lng, a.areaname
                FROM branch b
                JOIN area a ON a.areaid = b.areaid
                WHERE b.branchid = %s
                """,
                (int(branch_id),),
            )
            row = cur.fetchone()
            if not row:
                return {"status": "not_found", "message": "Branch not found."}
            if selected_area_id and int(selected_area_id) != int(row["areaid"]):
                return {
                    "status": "validation_error",
                    "message": "Selected branch is not in selected area.",
                }
            if row["lat"] is None or row["lng"] is None:
                return {
                    "status": "validation_error",
                    "message": "Selected branch missing coordinates.",
                }
            return {
                "status": "success",
                "locationSourceType": "BRANCH",
                "branchId": int(row["branchid"]),
                "parkingSpotId": None,
                "pickupAddress": row["address"],
                "lat": float(row["lat"]),
                "lng": float(row["lng"]),
                "cityZone": str(row["areaname"]).lower().replace(" ", "-"),
            }

        if not parking_spot_id:
            return {
                "status": "validation_error",
                "message": "parkingSpotId required for PARKING_SPOT source.",
            }
        cur.execute(
            """
            SELECT id, area_id, branch_id, address, lat, lng, city_zone
            FROM company_parking_spot
            WHERE id = %s AND is_active = TRUE
            """,
            (int(parking_spot_id),),
        )
        row = cur.fetchone()
        if not row:
            return {"status": "not_found", "message": "Parking spot not found."}
        if selected_area_id and int(selected_area_id) != int(row["area_id"]):
            return {
                "status": "validation_error",
                "message": "Selected parking spot is not in selected area.",
            }
        return {
            "status": "success",
            "locationSourceType": "PARKING_SPOT",
            "branchId": None,
            "parkingSpotId": int(row["id"]),
            "pickupAddress": row["address"],
            "lat": float(row["lat"]),
            "lng": float(row["lng"]),
            "cityZone": row["city_zone"],
        }

    def admin_listings(self) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    {LISTING_SELECT_SQL}
                    WHERE {_COMPANY_FLEET_FILTER}
                    ORDER BY l.created_at DESC
                    LIMIT 500
                    """
                )
                listings = hydrate_listing_rows(cur, cur.fetchall())
        return {"status": "success", "listings": listings}

    def admin_host_listings(self) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    {LISTING_SELECT_SQL}
                    WHERE {_HOST_LISTING_FILTER}
                    ORDER BY l.created_at DESC
                    LIMIT 500
                    """
                )
                listings = hydrate_listing_rows(cur, cur.fetchall())
        return {"status": "success", "listings": listings}

    def admin_company_locations(self) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT areaid, areaname
                    FROM area
                    ORDER BY areaname ASC
                    """
                )
                areas = [
                    {"areaId": row["areaid"], "areaName": row["areaname"]} for row in cur.fetchall()
                ]

                cur.execute(
                    """
                    SELECT branchid, areaid, city, address, lat, lng
                    FROM branch
                    ORDER BY areaid ASC, branchid ASC
                    """
                )
                branches = [
                    {
                        "branchId": row["branchid"],
                        "areaId": row["areaid"],
                        "name": f"Branch {row['branchid']} ({row['city']})",
                        "address": row["address"],
                        "lat": float(row["lat"]) if row["lat"] is not None else None,
                        "lng": float(row["lng"]) if row["lng"] is not None else None,
                    }
                    for row in cur.fetchall()
                ]

                cur.execute(
                    """
                    SELECT id, name, area_id, branch_id, address, lat, lng, city_zone
                    FROM company_parking_spot
                    WHERE is_active = TRUE
                    ORDER BY area_id ASC, id ASC
                    """
                )
                parking_spots = [
                    {
                        "parkingSpotId": row["id"],
                        "name": row["name"],
                        "areaId": row["area_id"],
                        "branchId": row["branch_id"],
                        "address": row["address"],
                        "lat": float(row["lat"]),
                        "lng": float(row["lng"]),
                        "cityZone": row["city_zone"],
                    }
                    for row in cur.fetchall()
                ]

                vehicle_classes = list(_VEHICLE_CATEGORY_OPTIONS)

        return {
            "status": "success",
            "areas": areas,
            "branches": branches,
            "parkingSpots": parking_spots,
            "vehicleClasses": vehicle_classes,
        }

    def list_vehicle_classes(self) -> list[dict]:
        return list(_VEHICLE_CATEGORY_OPTIONS)

    def admin_bookings(self) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    {_BOOKING_SELECT_SQL}
                    WHERE {_COMPANY_FLEET_FILTER}
                    ORDER BY b.created_at DESC
                    LIMIT 200
                    """
                )
                rows = cur.fetchall()
        return {"status": "success", "bookings": [to_booking_row(row) for row in rows]}

    def admin_analytics(self) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                analytics = _fetch_dashboard_analytics(cur, _COMPANY_FLEET_FILTER)
        return {"status": "success", "analytics": analytics}

    def sync_fleet_listings(self) -> dict:
        created = 0
        existing = 0
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                      va.vin,
                      va.make,
                      va.model,
                      COALESCE(va.fleet_status, 'Available') AS status,
                      b.city,
                      a.areaName,
                      va.branch_id
                    FROM vehicle_asset va
                    JOIN Branch b ON b.branchID = va.branch_id
                    JOIN Area a ON a.areaID = b.areaID
                    WHERE va.owner_type = 'COMPANY'::vehicle_owner_type
                      AND va.vin IS NOT NULL
                      AND COALESCE(va.fleet_status, 'Available') = 'Available'
                    LIMIT 500
                    """
                )
                fleet_rows = cur.fetchall()
                for row in fleet_rows:
                    cur.execute(
                        """
                        SELECT vehicle_id
                        FROM vehicle_asset
                        WHERE vin = %s
                        """,
                        (row["vin"],),
                    )
                    vehicle_id = cur.fetchone()["vehicle_id"]
                    cur.execute(
                        """
                        SELECT listing_id, vehicle_id
                        FROM vehicle_listing
                        WHERE source_type = 'FLEET' AND fleet_vehicle_vin = %s
                        """,
                        (row["vin"],),
                    )
                    hit = cur.fetchone()
                    lat, lng = _fleet_coords(row["city"], row["vin"])
                    city_zone = row["areaname"].lower().replace(" ", "-")
                    if hit:
                        existing += 1
                        if hit.get("vehicle_id") is None:
                            cur.execute(
                                """
                                UPDATE vehicle_listing
                                SET vehicle_id = %s, updated_at = NOW()
                                WHERE listing_id = %s
                                """,
                                (vehicle_id, hit["listing_id"]),
                            )
                        cur.execute(
                            """
                            UPDATE listing_location
                            SET lat = %s,
                                lng = %s,
                                geohash = %s,
                                city_zone = %s,
                                last_parked_at = NOW()
                            WHERE listing_id = %s
                            """,
                            (lat, lng, _simple_geohash(lat, lng), city_zone, hit["listing_id"]),
                        )
                        continue
                    cur.execute(
                        """
                        INSERT INTO vehicle_listing
                        (
                          source_type, fleet_vehicle_vin, vehicle_id, title, make, model, year,
                          description, guidelines, pickup_notes_template, price_per_day, active,
                          is_company_owned
                        )
                        VALUES ('FLEET', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, TRUE)
                        RETURNING listing_id
                        """,
                        (
                            row["vin"],
                            vehicle_id,
                            f"{row['make']} {row['model']} (Fleet)",
                            row["make"],
                            row["model"],
                            None,
                            f"Company fleet vehicle parked in {row['city']}.",
                            "Return with same fuel level.",
                            "Follow app instructions for pickup kiosk.",
                            65.0,
                        ),
                    )
                    listing_id = cur.fetchone()["listing_id"]
                    _upsert_listing_location(
                        cur,
                        listing_id,
                        lat=lat,
                        lng=lng,
                        city_zone=city_zone,
                        pickup_address=f"Fleet branch area ({row['city']})",
                    )
                    created += 1
                conn.commit()
        return {"status": "success", "created": created, "existing": existing}


fleet_service = FleetService()
