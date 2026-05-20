from __future__ import annotations

from datetime import datetime
import hashlib

from flask import current_app
from psycopg2.extras import Json, RealDictCursor

from metropolis.db import get_connection


def _to_listing_row(row: dict) -> dict:
    return {
        "listingId": row["listing_id"],
        "sourceType": row["source_type"],
        "title": row["title"],
        "brand": row.get("brand"),
        "make": row.get("make"),
        "model": row.get("model"),
        "year": row.get("year"),
        "mileage": row.get("mileage"),
        "vehicleClassId": row.get("vehicle_class_id"),
        "description": row["description"],
        "guidelines": row.get("guidelines") or row.get("rules"),
        "transmission": row.get("transmission"),
        "fuelType": row.get("fuel_type"),
        "seats": row.get("seats"),
        "doors": row.get("doors"),
        "features": row.get("features") or [],
        "images": row.get("images") or row.get("photos_json") or [],
        "address": row.get("address") or row.get("pickup_address"),
        "latitude": float(row.get("latitude")) if row.get("latitude") is not None else (float(row["lat"]) if row["lat"] is not None else None),
        "longitude": float(row.get("longitude")) if row.get("longitude") is not None else (float(row["lng"]) if row["lng"] is not None else None),
        "rules": row["rules"],
        "pickupNotesTemplate": row["pickup_notes_template"],
        "pricePerDay": float(row["price_per_day"]),
        "photos": row["photos_json"] or [],
        "active": row["active"],
        "status": row.get("status"),
        "ownerUserId": row["owner_user_id"],
        "isCompanyOwned": bool(row.get("is_company_owned")),
        "ownerName": row["owner_name"],
        "fleetVehicleVin": row["fleet_vehicle_vin"],
        "lat": float(row["lat"]) if row["lat"] is not None else None,
        "lng": float(row["lng"]) if row["lng"] is not None else None,
        "cityZone": row["city_zone"],
        "geohash": row["geohash"],
        "pickupAddress": row.get("pickup_address"),
        "locationSourceType": row.get("location_source_type"),
        "branchId": row.get("branch_id"),
        "parkingSpotId": row.get("parking_spot_id"),
        "createdByUserId": row.get("created_by_user_id"),
        "createdAt": row["created_at"].isoformat(),
        "updatedAt": row["updated_at"].isoformat(),
    }


def _to_booking_row(row: dict, instructions: list[dict]) -> dict:
    return {
        "bookingId": row["booking_id"],
        "listingId": row["listing_id"],
        "listingTitle": row["listing_title"],
        "sourceType": row["source_type"],
        "ownerUserId": row["owner_user_id"],
        "renterUserId": row["renter_user_id"],
        "startAt": row["start_at"].isoformat(),
        "endAt": row["end_at"].isoformat(),
        "status": row["status"],
        "priceSnapshot": row["price_snapshot_json"],
        "createdAt": row["created_at"].isoformat(),
        "updatedAt": row["updated_at"].isoformat(),
        "instructions": instructions,
    }


def _simple_geohash(lat: float, lng: float) -> str:
    return f"{round(lat, 2)}:{round(lng, 2)}"


CITY_COORDS = {
    "montreal": (45.5017, -73.5673),
    "toronto": (43.6532, -79.3832),
    "vancouver": (49.2827, -123.1207),
    "calgary": (51.0447, -114.0719),
    "ottawa": (45.4215, -75.6972),
}


def _fleet_coords(city: str, vin: str) -> tuple[float, float]:
    city_key = (city or "").lower()
    base = CITY_COORDS.get(city_key, (45.5017, -73.5673))
    digest = hashlib.sha256(vin.encode("utf-8")).hexdigest()
    lat_jitter = (int(digest[:4], 16) % 100) / 10000.0
    lng_jitter = (int(digest[4:8], 16) % 100) / 10000.0
    return base[0] + lat_jitter, base[1] + lng_jitter


class MarketplaceService:
    def _can_manage_listing(self, actor: dict, listing: dict) -> bool:
        return bool(actor.get("isAdmin")) or listing.get("owner_user_id") == actor["userId"]

    def _fetch_listing_ownership(self, cur, listing_id: int) -> dict | None:
        cur.execute(
            """
            SELECT listing_id, owner_user_id
            FROM vehicle_listing
            WHERE listing_id = %s
            """,
            (listing_id,),
        )
        return cur.fetchone()

    def _resolve_company_location(self, cur, payload: dict) -> dict:
        source_type = str(payload.get("locationSourceType") or "").upper()
        branch_id = payload.get("branchId")
        parking_spot_id = payload.get("parkingSpotId")
        selected_area_id = payload.get("areaId")
        if source_type not in {"BRANCH", "PARKING_SPOT"}:
            return {"status": "validation_error", "message": "locationSourceType must be BRANCH or PARKING_SPOT."}

        if source_type == "BRANCH":
            if not branch_id:
                return {"status": "validation_error", "message": "branchId required for BRANCH source."}
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
                return {"status": "validation_error", "message": "Selected branch is not in selected area."}
            if row["lat"] is None or row["lng"] is None:
                return {"status": "validation_error", "message": "Selected branch missing coordinates."}
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
            return {"status": "validation_error", "message": "parkingSpotId required for PARKING_SPOT source."}
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
            return {"status": "validation_error", "message": "Selected parking spot is not in selected area."}
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

    def create_listing(self, actor: dict, payload: dict) -> dict:
        if not actor.get("isAdmin") and not bool(current_app.config.get("ALLOW_USER_LISTINGS", False)):
            return {
                "status": "forbidden",
                "message": "User vehicle listings disabled for this demo. Admin fleet only.",
            }
        is_company_owned = bool(payload.get("isCompanyOwned")) and bool(actor.get("isAdmin"))
        owner_user_id = actor["userId"]
        # Keep manual admin-created company listings compatible with existing
        # listing table constraints (fleet rows require fleet_vehicle_vin).
        source_type = "OWNER"

        brand = payload.get("brand")
        make = payload.get("make")
        model = payload.get("model")
        year = payload.get("year")
        mileage = payload.get("mileage")
        vehicle_class_id = payload.get("vehicleClassId")
        transmission = payload.get("transmission")
        fuel_type = payload.get("fuelType")
        seats = payload.get("seats")
        doors = payload.get("doors")
        features = payload.get("features")
        images = payload.get("images")
        address = payload.get("address")
        latitude = payload.get("latitude")
        longitude = payload.get("longitude")
        if mileage is not None:
            mileage = int(mileage)
        if vehicle_class_id is not None:
            vehicle_class_id = int(vehicle_class_id)
        if seats is not None:
            seats = int(seats)
        if doors is not None:
            doors = int(doors)
        if latitude is not None:
            latitude = float(latitude)
        if longitude is not None:
            longitude = float(longitude)
        if mileage is not None and int(mileage) < 0:
            return {"status": "validation_error", "message": "mileage must be >= 0."}
        if seats is not None and seats <= 0:
            return {"status": "validation_error", "message": "seats must be > 0."}
        if doors is not None and doors <= 0:
            return {"status": "validation_error", "message": "doors must be > 0."}
        if features is None:
            features = []
        if images is None:
            images = payload.get("photos", [])
        title = payload.get("title")
        if not title:
            parts = [p for p in [brand, make, model, str(year) if year else None] if p]
            title = " ".join(parts) if parts else "User listed car"

        try:
            with get_connection() as conn:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                if is_company_owned:
                    company_source_type = str(payload.get("locationSourceType") or "").upper()
                    if company_source_type in {"BRANCH", "PARKING_SPOT"}:
                        location = self._resolve_company_location(cur, payload)
                        if location["status"] != "success":
                            return location
                        lat = location["lat"]
                        lng = location["lng"]
                        city_zone = location["cityZone"]
                        pickup_address = location["pickupAddress"]
                        location_source_type = location["locationSourceType"]
                        branch_id = location["branchId"]
                        parking_spot_id = location["parkingSpotId"]
                        address = address or pickup_address
                        latitude = latitude if latitude is not None else lat
                        longitude = longitude if longitude is not None else lng
                    else:
                        lat = payload.get("lat")
                        lng = payload.get("lng")
                        city_zone = payload.get("cityZone")
                        if lat is None and latitude is not None:
                            lat = latitude
                        if lng is None and longitude is not None:
                            lng = longitude
                        if lat is None or lng is None or not city_zone:
                            return {
                                "status": "validation_error",
                                "message": "lat, lng, and cityZone required for custom company-owned listings.",
                            }
                        lat = float(lat)
                        lng = float(lng)
                        pickup_address = payload.get("pickupAddress") or address
                        location_source_type = None
                        branch_id = None
                        parking_spot_id = None
                        if address is None:
                            address = pickup_address
                        if latitude is None:
                            latitude = lat
                        if longitude is None:
                            longitude = lng
                else:
                    lat = payload.get("lat")
                    lng = payload.get("lng")
                    city_zone = payload.get("cityZone")
                    if lat is None or lng is None or not city_zone:
                        return {
                            "status": "validation_error",
                            "message": "lat, lng, and cityZone required for user-owned listings.",
                        }
                    pickup_address = None
                    location_source_type = None
                    branch_id = None
                    parking_spot_id = None
                    if latitude is None:
                        latitude = float(lat)
                    if longitude is None:
                        longitude = float(lng)

                if is_company_owned:
                    if not make or not model:
                        return {
                            "status": "validation_error",
                            "message": "make and model are required for company-owned listings.",
                        }
                    if mileage is None:
                        return {
                            "status": "validation_error",
                            "message": "mileage is required for company-owned listings.",
                        }
                    if vehicle_class_id is None:
                        return {
                            "status": "validation_error",
                            "message": "vehicleClassId is required for company-owned listings.",
                        }
                    cur.execute(
                        "SELECT classid FROM vehicleclass WHERE classid = %s",
                        (int(vehicle_class_id),),
                    )
                    if not cur.fetchone():
                        return {"status": "validation_error", "message": "Invalid vehicleClassId."}

                cur.execute(
                    """
                    INSERT INTO owner_profile (user_id, verification_status)
                    VALUES (%s, 'PENDING')
                    ON CONFLICT (user_id) DO NOTHING
                    """,
                    (owner_user_id,),
                )
                cur.execute(
                    """
                    INSERT INTO vehicle_listing
                    (
                      owner_user_id, created_by_user_id, source_type, title, brand, make, model, year, mileage, vehicle_class_id,
                      description, guidelines, transmission, fuel_type, seats, doors, features, images, address, latitude, longitude,
                      rules, pickup_notes_template, price_per_day, photos_json, active, status,
                      is_company_owned, location_source_type, branch_id, parking_spot_id, pickup_address
                    )
                    VALUES (
                      %s, %s, %s::listing_source_type, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s,
                      %s, %s, %s, %s::jsonb, TRUE, 'ACTIVE',
                      %s, %s, %s, %s, %s
                    )
                    RETURNING listing_id
                    """,
                    (
                        owner_user_id,
                        actor["userId"],
                        source_type,
                        title,
                        brand,
                        make,
                        model,
                        year,
                        mileage,
                        vehicle_class_id,
                        payload.get("description"),
                        payload.get("guidelines") or payload.get("rules"),
                        transmission,
                        fuel_type,
                        seats,
                        doors,
                        Json(features),
                        Json(images),
                        address,
                        latitude,
                        longitude,
                        payload.get("rules"),
                        payload.get("pickupNotesTemplate"),
                        payload["pricePerDay"],
                        Json(payload.get("photos", images)),
                        is_company_owned,
                        location_source_type,
                        branch_id,
                        parking_spot_id,
                        pickup_address,
                    ),
                )
                listing_id = cur.fetchone()["listing_id"]
                cur.execute(
                    """
                    INSERT INTO listing_location (listing_id, lat, lng, geohash, city_zone)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        listing_id,
                        lat,
                        lng,
                        _simple_geohash(lat, lng),
                        city_zone,
                    ),
                )
                conn.commit()
            return self.get_listing(listing_id)
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            if "column" in msg and "vehicle_listing" in msg and "does not exist" in msg:
                return {
                    "status": "validation_error",
                    "message": "Database schema is outdated (missing vehicle_listing columns). Run latest DB migrations, then retry.",
                }
            raise

    def get_listing(self, listing_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT l.*, loc.lat, loc.lng, loc.geohash, loc.city_zone, u.full_name AS owner_name
                    FROM vehicle_listing l
                    LEFT JOIN listing_location loc ON loc.listing_id = l.listing_id
                    LEFT JOIN app_user u ON u.user_id = l.owner_user_id
                    WHERE l.listing_id = %s
                    """,
                    (listing_id,),
                )
                row = cur.fetchone()
        if not row:
            return {"status": "not_found", "message": "Listing not found."}
        return {"status": "success", "listing": _to_listing_row(row)}

    def owner_listings(self, actor: dict) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT l.*, loc.lat, loc.lng, loc.geohash, loc.city_zone, u.full_name AS owner_name
                    FROM vehicle_listing l
                    LEFT JOIN listing_location loc ON loc.listing_id = l.listing_id
                    LEFT JOIN app_user u ON u.user_id = l.owner_user_id
                    WHERE l.owner_user_id = %s
                    ORDER BY l.created_at DESC
                    """,
                    (actor["userId"],),
                )
                rows = cur.fetchall()
        return {"status": "success", "listings": [_to_listing_row(row) for row in rows]}

    def admin_listings(self) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT l.*, loc.lat, loc.lng, loc.geohash, loc.city_zone, u.full_name AS owner_name
                    FROM vehicle_listing l
                    LEFT JOIN listing_location loc ON loc.listing_id = l.listing_id
                    LEFT JOIN app_user u ON u.user_id = l.owner_user_id
                    ORDER BY l.created_at DESC
                    LIMIT 500
                    """
                )
                rows = cur.fetchall()
        return {"status": "success", "listings": [_to_listing_row(row) for row in rows]}

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
                areas = [{"areaId": row["areaid"], "areaName": row["areaname"]} for row in cur.fetchall()]

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

                cur.execute(
                    """
                    SELECT classid, classname
                    FROM vehicleclass
                    ORDER BY classname ASC
                    """
                )
                vehicle_classes = [
                    {"vehicleClassId": row["classid"], "name": row["classname"]} for row in cur.fetchall()
                ]

        return {
            "status": "success",
            "areas": areas,
            "branches": branches,
            "parkingSpots": parking_spots,
            "vehicleClasses": vehicle_classes,
        }

    def search_listings(self, query: dict) -> dict:
        clauses = ["l.active = TRUE"]
        params = []
        if query.get("cityZone"):
            clauses.append("loc.city_zone = %s")
            params.append(query["cityZone"])
        if query.get("bbox"):
            min_lng, min_lat, max_lng, max_lat = [float(x) for x in query["bbox"].split(",")]
            clauses.extend(["loc.lng BETWEEN %s AND %s", "loc.lat BETWEEN %s AND %s"])
            params.extend([min_lng, max_lng, min_lat, max_lat])

        where_sql = " AND ".join(clauses)
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    SELECT l.*, loc.lat, loc.lng, loc.geohash, loc.city_zone, u.full_name AS owner_name
                    FROM vehicle_listing l
                    LEFT JOIN listing_location loc ON loc.listing_id = l.listing_id
                    LEFT JOIN app_user u ON u.user_id = l.owner_user_id
                    WHERE {where_sql}
                    ORDER BY l.updated_at DESC
                    LIMIT 500
                    """,
                    tuple(params),
                )
                rows = cur.fetchall()
        return {"status": "success", "listings": [_to_listing_row(row) for row in rows]}

    def update_listing(self, actor: dict, listing_id: int, payload: dict) -> dict:
        fields = []
        params = []
        mapping = {
            "title": "title",
            "brand": "brand",
            "make": "make",
            "model": "model",
            "year": "year",
            "mileage": "mileage",
            "vehicleClassId": "vehicle_class_id",
            "description": "description",
            "guidelines": "guidelines",
            "transmission": "transmission",
            "fuelType": "fuel_type",
            "seats": "seats",
            "doors": "doors",
            "features": "features",
            "images": "images",
            "address": "address",
            "latitude": "latitude",
            "longitude": "longitude",
            "rules": "rules",
            "pickupNotesTemplate": "pickup_notes_template",
            "pricePerDay": "price_per_day",
            "photos": "photos_json",
            "active": "active",
            "isCompanyOwned": "is_company_owned",
        }
        for key, column in mapping.items():
            if key in payload:
                fields.append(f"{column} = %s")
                params.append(Json(payload[key]) if key in {"photos", "features", "images"} else payload[key])
        if not fields:
            return {"status": "validation_error", "message": "No fields to update."}

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                listing = self._fetch_listing_ownership(cur, listing_id)
                if not listing or not self._can_manage_listing(actor, listing):
                    return {"status": "not_found", "message": "Listing not found for actor."}
                fields.append("updated_at = %s")
                params.append(datetime.utcnow())
                params.append(listing_id)
                cur.execute(
                    f"""
                    UPDATE vehicle_listing
                    SET {", ".join(fields)}
                    WHERE listing_id = %s
                    RETURNING listing_id
                    """,
                    tuple(params),
                )
                if not cur.fetchone():
                    return {"status": "not_found", "message": "Listing not found for actor."}
                conn.commit()
        return self.get_listing(listing_id)

    def upsert_location(self, actor: dict, listing_id: int, payload: dict) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                listing = self._fetch_listing_ownership(cur, listing_id)
                if not listing or not self._can_manage_listing(actor, listing):
                    return {"status": "not_found", "message": "Listing not found for actor."}
                cur.execute(
                    """
                    INSERT INTO listing_location (listing_id, lat, lng, geohash, city_zone, last_parked_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (listing_id) DO UPDATE
                    SET lat = EXCLUDED.lat,
                        lng = EXCLUDED.lng,
                        geohash = EXCLUDED.geohash,
                        city_zone = EXCLUDED.city_zone,
                        last_parked_at = NOW()
                    """,
                    (
                        listing_id,
                        payload["lat"],
                        payload["lng"],
                        _simple_geohash(payload["lat"], payload["lng"]),
                        payload["cityZone"],
                    ),
                )
                conn.commit()
        return self.get_listing(listing_id)

    def add_availability(self, actor: dict, listing_id: int, payload: dict) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                listing = self._fetch_listing_ownership(cur, listing_id)
                if not listing or not self._can_manage_listing(actor, listing):
                    return {"status": "not_found", "message": "Listing not found for actor."}
                cur.execute(
                    """
                    INSERT INTO listing_availability (listing_id, start_at, end_at, status)
                    VALUES (%s, %s, %s, %s::availability_status)
                    RETURNING availability_id, listing_id, start_at, end_at, status
                    """,
                    (
                        listing_id,
                        payload["startAt"],
                        payload["endAt"],
                        payload.get("status", "AVAILABLE"),
                    ),
                )
                row = cur.fetchone()
                conn.commit()
        return {
            "status": "success",
            "availability": {
                "availabilityId": row["availability_id"],
                "listingId": row["listing_id"],
                "startAt": row["start_at"].isoformat(),
                "endAt": row["end_at"].isoformat(),
                "status": row["status"],
            },
        }

    def create_booking(self, renter_user_id: int, payload: dict) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT listing_id, title, owner_user_id, source_type, price_per_day, active
                    FROM vehicle_listing
                    WHERE listing_id = %s
                    FOR UPDATE
                    """,
                    (payload["listingId"],),
                )
                listing = cur.fetchone()
                if not listing or not listing["active"]:
                    return {"status": "not_found", "message": "Listing not found or inactive."}
                cur.execute(
                    """
                    SELECT 1
                    FROM booking
                    WHERE listing_id = %s
                      AND status IN ('PENDING', 'CONFIRMED', 'IN_PROGRESS')
                      AND NOT (%s >= end_at OR %s <= start_at)
                    LIMIT 1
                    """,
                    (payload["listingId"], payload["startAt"], payload["endAt"]),
                )
                if cur.fetchone():
                    return {"status": "validation_error", "message": "Listing unavailable for selected window."}
                cur.execute(
                    """
                    INSERT INTO booking (listing_id, renter_user_id, start_at, end_at, status, price_snapshot_json)
                    VALUES (%s, %s, %s, %s, 'CONFIRMED', %s::jsonb)
                    RETURNING booking_id
                    """,
                    (
                        payload["listingId"],
                        renter_user_id,
                        payload["startAt"],
                        payload["endAt"],
                        Json({"pricePerDay": float(listing["price_per_day"])}),
                    ),
                )
                booking_id = cur.fetchone()["booking_id"]
                cur.execute(
                    """
                    INSERT INTO trip_event (booking_id, event_type, actor_user_id, metadata_json)
                    VALUES (%s, 'BOOKING_CREATED', %s, %s::jsonb)
                    """,
                    (booking_id, renter_user_id, Json({"source": listing["source_type"]})),
                )
                conn.commit()
        return self.get_booking(booking_id, renter_user_id, False)

    def get_booking(self, booking_id: int, requester_user_id: int, requester_is_admin: bool) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT b.*, l.title AS listing_title, l.owner_user_id, l.source_type
                    FROM booking b
                    JOIN vehicle_listing l ON l.listing_id = b.listing_id
                    WHERE b.booking_id = %s
                    """,
                    (booking_id,),
                )
                row = cur.fetchone()
                if not row:
                    return {"status": "not_found", "message": "Booking not found."}
                is_renter = row["renter_user_id"] == requester_user_id
                is_owner = row["owner_user_id"] == requester_user_id
                if not (requester_is_admin or is_renter or is_owner):
                    return {"status": "forbidden", "message": "No access to this booking."}
                cur.execute(
                    """
                    SELECT instruction_id, owner_user_id, message, sent_at, read_at
                    FROM booking_instruction
                    WHERE booking_id = %s
                    ORDER BY sent_at ASC
                    """,
                    (booking_id,),
                )
                instructions = [
                    {
                        "instructionId": r["instruction_id"],
                        "ownerUserId": r["owner_user_id"],
                        "message": r["message"],
                        "sentAt": r["sent_at"].isoformat(),
                        "readAt": r["read_at"].isoformat() if r["read_at"] else None,
                    }
                    for r in cur.fetchall()
                ]
        return {"status": "success", "booking": _to_booking_row(row, instructions)}

    def send_instruction(self, booking_id: int, owner_user_id: int, message: str) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT b.booking_id
                    FROM booking b
                    JOIN vehicle_listing l ON l.listing_id = b.listing_id
                    WHERE b.booking_id = %s AND l.owner_user_id = %s
                    """,
                    (booking_id, owner_user_id),
                )
                if not cur.fetchone():
                    return {"status": "not_found", "message": "Booking not found for owner."}
                cur.execute(
                    """
                    INSERT INTO booking_instruction (booking_id, owner_user_id, message)
                    VALUES (%s, %s, %s)
                    RETURNING instruction_id, sent_at
                    """,
                    (booking_id, owner_user_id, message),
                )
                instruction = cur.fetchone()
                cur.execute(
                    """
                    INSERT INTO trip_event (booking_id, event_type, actor_user_id, metadata_json)
                    VALUES (%s, 'INSTRUCTION_SENT', %s, %s::jsonb)
                    """,
                    (booking_id, owner_user_id, Json({"instructionId": instruction["instruction_id"]})),
                )
                conn.commit()
        return {
            "status": "success",
            "instruction": {
                "instructionId": instruction["instruction_id"],
                "ownerUserId": owner_user_id,
                "message": message,
                "sentAt": instruction["sent_at"].isoformat(),
                "readAt": None,
            },
        }

    def transition_booking_status(
        self,
        booking_id: int,
        actor_user_id: int,
        actor_is_admin: bool,
        target_status: str,
    ) -> dict:
        status = target_status.upper()
        if status not in {"IN_PROGRESS", "COMPLETED", "CANCELLED"}:
            return {"status": "validation_error", "message": "Unsupported booking status transition."}
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT b.booking_id, b.status, b.renter_user_id, l.owner_user_id
                    FROM booking b
                    JOIN vehicle_listing l ON l.listing_id = b.listing_id
                    WHERE b.booking_id = %s
                    FOR UPDATE
                    """,
                    (booking_id,),
                )
                row = cur.fetchone()
                if not row:
                    return {"status": "not_found", "message": "Booking not found."}
                is_owner = row["owner_user_id"] == actor_user_id
                is_renter = row["renter_user_id"] == actor_user_id
                if not (actor_is_admin or is_owner or is_renter):
                    return {"status": "forbidden", "message": "No access to this booking."}
                cur.execute(
                    """
                    UPDATE booking
                    SET status = %s::booking_status, updated_at = NOW()
                    WHERE booking_id = %s
                    """,
                    (status, booking_id),
                )
                cur.execute(
                    """
                    INSERT INTO trip_event (booking_id, event_type, actor_user_id, metadata_json)
                    VALUES (%s, %s, %s, %s::jsonb)
                    """,
                    (booking_id, f"STATUS_{status}", actor_user_id, Json({"from": row["status"], "to": status})),
                )
                conn.commit()
        return self.get_booking(booking_id, actor_user_id, actor_is_admin)

    def delete_listing(self, actor: dict, listing_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                listing = self._fetch_listing_ownership(cur, listing_id)
                if not listing:
                    return {"status": "not_found", "message": "Listing not found."}
                if not self._can_manage_listing(actor, listing):
                    return {"status": "forbidden", "message": "No listing access."}
                cur.execute("DELETE FROM vehicle_listing WHERE listing_id = %s", (listing_id,))
                conn.commit()
        return {"status": "success"}

    def admin_bookings(self) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        b.booking_id, b.listing_id, b.renter_user_id, b.start_at, b.end_at, b.status,
                        b.price_snapshot_json, b.created_at, b.updated_at,
                        l.title AS listing_title, l.source_type, l.owner_user_id
                    FROM booking b
                    JOIN vehicle_listing l ON l.listing_id = b.listing_id
                    ORDER BY b.created_at DESC
                    LIMIT 200
                    """
                )
                rows = cur.fetchall()
        return {"status": "success", "bookings": [_to_booking_row(row, []) for row in rows]}

    def admin_analytics(self) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        COUNT(DISTINCT l.listing_id) AS listing_count,
                        COUNT(DISTINCT b.booking_id) AS booking_count,
                        COALESCE(SUM((b.price_snapshot_json->>'pricePerDay')::numeric), 0) AS gross_daily_revenue
                    FROM vehicle_listing l
                    LEFT JOIN booking b ON b.listing_id = l.listing_id
                    """
                )
                row = cur.fetchone()
        return {
            "status": "success",
            "analytics": {
                "listingCount": int(row["listing_count"] or 0),
                "bookingCount": int(row["booking_count"] or 0),
                "grossDailyRevenue": float(row["gross_daily_revenue"] or 0),
            },
        }

    def sync_fleet_listings(self) -> dict:
        created = 0
        existing = 0
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT v.vin, v.make, v.model, v.status, b.city, a.areaName
                    FROM Vehicle v
                    JOIN Branch b ON b.branchID = v.branchID
                    JOIN Area a ON a.areaID = b.areaID
                    WHERE v.status = 'Available'
                    LIMIT 500
                    """
                )
                fleet_rows = cur.fetchall()
                for row in fleet_rows:
                    cur.execute(
                        """
                        SELECT listing_id
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
                        cur.execute(
                            """
                            UPDATE listing_location
                            SET lat = %s, lng = %s, geohash = %s, city_zone = %s, last_parked_at = NOW()
                            WHERE listing_id = %s
                            """,
                            (lat, lng, _simple_geohash(lat, lng), city_zone, hit["listing_id"]),
                        )
                        continue
                    cur.execute(
                        """
                        INSERT INTO vehicle_listing
                        (
                          source_type, fleet_vehicle_vin, title, brand, make, model, year,
                          description, rules, pickup_notes_template, price_per_day, photos_json, active,
                          is_company_owned
                        )
                        VALUES ('FLEET', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, TRUE, TRUE)
                        RETURNING listing_id
                        """,
                        (
                            row["vin"],
                            f"{row['make']} {row['model']} (Fleet)",
                            row["make"],
                            row["make"],
                            row["model"],
                            None,
                            f"Company fleet vehicle parked in {row['city']}.",
                            "Return with same fuel level.",
                            "Follow app instructions for pickup kiosk.",
                            65.0,
                            Json([]),
                        ),
                    )
                    listing_id = cur.fetchone()["listing_id"]
                    cur.execute(
                        """
                        INSERT INTO listing_location (listing_id, lat, lng, geohash, city_zone)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (listing_id, lat, lng, _simple_geohash(lat, lng), city_zone),
                    )
                    created += 1
                conn.commit()
        return {"status": "success", "created": created, "existing": existing}
