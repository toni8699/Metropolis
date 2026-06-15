from __future__ import annotations

from datetime import datetime

from flask import current_app
from psycopg2.extras import Json, RealDictCursor

from metropolis.db import get_connection
from metropolis.services.marketplace_common import (
    _BOOKING_HOLD_STATUSES,
    _LISTING_AVAILABLE_FOR_WINDOW_SQL,
    LISTING_SELECT_SQL,
    _associate_listing_image_urls,
    _fetch_dashboard_analytics,
    _listing_image_urls,
    _resolve_guidelines,
    _resolve_search_window,
    _upsert_listing_location,
    hydrate_listing_rows,
)


class ListingService:
    @staticmethod
    def _apply_lifecycle_compat(payload: dict) -> dict:
        normalized = dict(payload)
        status_input = normalized.get("status")
        has_status = status_input is not None and str(status_input).strip() != ""
        if has_status:
            status = str(status_input).strip().upper()
            if status not in {"ACTIVE", "INACTIVE"}:
                raise ValueError("status must be ACTIVE or INACTIVE.")
            normalized["status"] = status
            normalized["active"] = status == "ACTIVE"
            return normalized

        if "active" in normalized:
            normalized["status"] = "ACTIVE" if bool(normalized.get("active")) else "INACTIVE"
        return normalized

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

    def create_listing(self, actor: dict, payload: dict) -> dict:
        if not actor.get("isAdmin") and not bool(
            current_app.config.get("ALLOW_USER_LISTINGS", False)
        ):
            return {
                "status": "forbidden",
                "message": "User vehicle listings are disabled. Admin fleet only.",
            }
        is_company_owned = bool(payload.get("isCompanyOwned")) and bool(actor.get("isAdmin"))
        owner_user_id = actor["userId"]
        # Keep manual admin-created company listings compatible with existing
        # listing table constraints (fleet rows require fleet_vehicle_vin).
        source_type = "OWNER"

        brand = payload.get("brand")
        make = payload.get("make") or brand
        model = payload.get("model")
        year = payload.get("year")
        mileage = payload.get("mileage")
        transmission = payload.get("transmission")
        fuel_type = payload.get("fuelType")
        seats = payload.get("seats")
        doors = payload.get("doors")
        features = payload.get("features")
        image_urls = _listing_image_urls(payload)
        address = payload.get("pickupAddress")
        latitude = payload.get("latitude")
        longitude = payload.get("longitude")
        guidelines = _resolve_guidelines(payload)
        if mileage is not None:
            mileage = int(mileage)
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
        title = payload.get("title")
        if not title:
            parts = [p for p in [make, model, str(year) if year else None] if p]
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
                        location_address = location["pickupAddress"]
                        location_source_type = location["locationSourceType"]
                        branch_id = location["branchId"]
                        parking_spot_id = location["parkingSpotId"]
                        if address is None:
                            address = location_address
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
                                "message": (
                                    "lat, lng, and cityZone required for custom "
                                    "company-owned listings."
                                ),
                            }
                        lat = float(lat)
                        lng = float(lng)
                        location_address = payload.get("pickupAddress")
                        location_source_type = None
                        branch_id = None
                        parking_spot_id = None
                        if address is None:
                            address = location_address
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
                    location_address = payload.get("pickupAddress")
                    location_source_type = None
                    branch_id = None
                    parking_spot_id = None
                    if address is None:
                        address = location_address

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
                cur.execute(
                    """
                    INSERT INTO owner_profile (user_id, verification_status)
                    VALUES (%s, 'PENDING')
                    ON CONFLICT (user_id) DO NOTHING
                    """,
                    (owner_user_id,),
                )
                owner_type = "COMPANY" if is_company_owned else "INDEPENDENT_HOST"
                owner_party_name = "Company Managed" if is_company_owned else None
                asset_status = "ACTIVE"
                cur.execute(
                    """
                    INSERT INTO vehicle_asset (
                      vehicle_category,
                      owner_type,
                      owner_party_user_id,
                      owner_party_name,
                      asset_status,
                      make,
                      model,
                      model_year
                    )
                    VALUES (
                      'STANDARD'::vehicle_category,
                      %s::vehicle_owner_type,
                      %s,
                      %s,
                      %s::vehicle_asset_status,
                      %s,
                      %s,
                      %s
                    )
                    RETURNING vehicle_id
                    """,
                    (
                        owner_type,
                        owner_user_id,
                        owner_party_name,
                        asset_status,
                        make,
                        model,
                        year,
                    ),
                )
                vehicle_id = cur.fetchone()["vehicle_id"]
                pickup_address = address or location_address
                cur.execute(
                    """
                    INSERT INTO vehicle_listing
                    (
                      owner_user_id, created_by_user_id, vehicle_id, source_type, title, make,
                      model, year, mileage,
                      description, guidelines, transmission, fuel_type, seats, doors,
                      features, pickup_notes_template, price_per_day, active, status,
                      is_company_owned, instant_book, location_source_type, branch_id,
                      parking_spot_id
                    )
                    VALUES (
                      %s, %s, %s, %s::listing_source_type, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s::jsonb,
                      %s, %s, TRUE, 'ACTIVE',
                      %s, %s, %s, %s, %s
                    )
                    RETURNING listing_id
                    """,
                    (
                        owner_user_id,
                        actor["userId"],
                        vehicle_id,
                        source_type,
                        title,
                        make,
                        model,
                        year,
                        mileage,
                        payload.get("description"),
                        guidelines,
                        transmission,
                        fuel_type,
                        seats,
                        doors,
                        Json(features),
                        payload.get("pickupNotesTemplate"),
                        payload["pricePerDay"],
                        is_company_owned,
                        bool(payload.get("instantBook", True)),
                        location_source_type,
                        branch_id,
                        parking_spot_id,
                    ),
                )
                listing_id = cur.fetchone()["listing_id"]
                _upsert_listing_location(
                    cur,
                    listing_id,
                    lat=float(lat),
                    lng=float(lng),
                    city_zone=city_zone,
                    pickup_address=pickup_address,
                )
                if image_urls:
                    _associate_listing_image_urls(cur, listing_id, image_urls, owner_user_id)
                conn.commit()
            return self.get_listing(listing_id)
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            if "column" in msg and "vehicle_listing" in msg and "does not exist" in msg:
                return {
                    "status": "validation_error",
                    "message": (
                        "Database schema is outdated (missing vehicle_listing columns). "
                        "Run latest DB migrations, then retry."
                    ),
                }
            raise

    def get_listing(self, listing_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    {LISTING_SELECT_SQL}
                    WHERE l.listing_id = %s
                    """,
                    (listing_id,),
                )
                row = cur.fetchone()
                if not row:
                    return {"status": "not_found", "message": "Listing not found."}
                listing = hydrate_listing_rows(cur, [row])[0]
        return {"status": "success", "listing": listing}

    def list_listing_booked_ranges(self, listing_id: int) -> dict:
        """Return booking windows that block new reservations on this listing (and fleet VIN)."""
        status_sql = ", ".join(["%s::booking_status"] * len(_BOOKING_HOLD_STATUSES))
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT listing_id, source_type, fleet_vehicle_vin, active
                    FROM vehicle_listing
                    WHERE listing_id = %s
                    """,
                    (listing_id,),
                )
                listing = cur.fetchone()
                if not listing or not listing["active"]:
                    return {"status": "not_found", "message": "Listing not found."}
                cur.execute(
                    f"""
                    SELECT b.start_at, b.end_at
                    FROM booking b
                    JOIN vehicle_listing vl ON vl.listing_id = b.listing_id
                    WHERE b.status IN ({status_sql})
                      AND (
                        b.listing_id = %s
                        OR (
                          %s = 'FLEET'
                          AND %s IS NOT NULL
                          AND vl.fleet_vehicle_vin = %s
                        )
                      )
                    ORDER BY b.start_at ASC
                    """,
                    (
                        *_BOOKING_HOLD_STATUSES,
                        listing_id,
                        listing["source_type"],
                        listing.get("fleet_vehicle_vin"),
                        listing.get("fleet_vehicle_vin"),
                    ),
                )
                rows = cur.fetchall()
        return {
            "status": "success",
            "ranges": [
                {
                    "startAt": row["start_at"].isoformat(),
                    "endAt": row["end_at"].isoformat(),
                }
                for row in rows
            ],
        }

    def owner_listings(self, actor: dict) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    {LISTING_SELECT_SQL}
                    WHERE l.owner_user_id = %s
                      AND l.source_type = 'OWNER'
                    ORDER BY l.created_at DESC
                    """,
                    (actor["userId"],),
                )
                listings = hydrate_listing_rows(cur, cur.fetchall())
        return {"status": "success", "listings": listings}

    def search_listings(self, query: dict) -> dict:
        clauses = ["COALESCE(l.status, 'ACTIVE') = 'ACTIVE'"]
        params: list = []
        if query.get("cityZone"):
            clauses.append("loc.city_zone = %s")
            params.append(query["cityZone"])
        if query.get("bbox"):
            min_lng, min_lat, max_lng, max_lat = (float(x) for x in query["bbox"].split(","))
            clauses.extend(["loc.lng BETWEEN %s AND %s", "loc.lat BETWEEN %s AND %s"])
            params.extend([min_lng, max_lng, min_lat, max_lat])

        window = _resolve_search_window(query)
        if window is not None:
            start_at, end_at = window
            clauses.append(_LISTING_AVAILABLE_FOR_WINDOW_SQL)
            params.extend([end_at, start_at, end_at, start_at])

        where_sql = " AND ".join(clauses)
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    {LISTING_SELECT_SQL}
                    WHERE {where_sql}
                    ORDER BY l.updated_at DESC
                    LIMIT 500
                    """,
                    tuple(params),
                )
                listings = hydrate_listing_rows(cur, cur.fetchall())
        return {"status": "success", "listings": listings}

    def update_listing(self, actor: dict, listing_id: int, payload: dict) -> dict:
        try:
            payload = self._apply_lifecycle_compat(payload)
        except ValueError as exc:
            return {"status": "validation_error", "message": str(exc)}
        if "rules" in payload and "guidelines" not in payload:
            payload = {**payload, "guidelines": payload["rules"]}
        if "make" not in payload and payload.get("brand") is not None:
            payload = {**payload, "make": payload.get("brand")}

        vehicle_mapping = {
            "title": "title",
            "make": "make",
            "model": "model",
            "year": "year",
            "mileage": "mileage",
            "description": "description",
            "guidelines": "guidelines",
            "transmission": "transmission",
            "fuelType": "fuel_type",
            "seats": "seats",
            "doors": "doors",
            "features": "features",
            "pickupNotesTemplate": "pickup_notes_template",
            "pricePerDay": "price_per_day",
            "active": "active",
            "status": "status",
            "isCompanyOwned": "is_company_owned",
            "instantBook": "instant_book",
        }
        vehicle_fields = []
        vehicle_params = []
        for key, column in vehicle_mapping.items():
            if key in payload:
                vehicle_fields.append(f"{column} = %s")
                vehicle_params.append(Json(payload[key]) if key == "features" else payload[key])

        image_urls = _listing_image_urls(payload)
        location_keys = {
            "lat",
            "lng",
            "cityZone",
            "latitude",
            "longitude",
            "pickupAddress",
        }
        has_location_update = any(key in payload for key in location_keys)

        if not vehicle_fields and not has_location_update and not image_urls:
            return {"status": "validation_error", "message": "No fields to update."}

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                listing = self._fetch_listing_ownership(cur, listing_id)
                if not listing or not self._can_manage_listing(actor, listing):
                    return {"status": "not_found", "message": "Listing not found for actor."}

                if vehicle_fields:
                    vehicle_fields.append("updated_at = %s")
                    vehicle_params.append(datetime.utcnow())
                    vehicle_params.append(listing_id)
                    cur.execute(
                        f"""
                        UPDATE vehicle_listing
                        SET {", ".join(vehicle_fields)}
                        WHERE listing_id = %s
                        RETURNING listing_id
                        """,
                        tuple(vehicle_params),
                    )
                    if not cur.fetchone():
                        return {"status": "not_found", "message": "Listing not found for actor."}
                if has_location_update:
                    cur.execute(
                        """
                        SELECT lat, lng, city_zone, pickup_address
                        FROM listing_location
                        WHERE listing_id = %s
                        """,
                        (listing_id,),
                    )
                    current_location = cur.fetchone()
                    lat = payload.get("lat", payload.get("latitude"))
                    lng = payload.get("lng", payload.get("longitude"))
                    city_zone = payload.get("cityZone")
                    pickup_address = payload.get("pickupAddress")

                    if lat is None and current_location:
                        lat = current_location["lat"]
                    if lng is None and current_location:
                        lng = current_location["lng"]
                    if city_zone is None and current_location:
                        city_zone = current_location["city_zone"]
                    if pickup_address is None and current_location:
                        pickup_address = current_location["pickup_address"]

                    if lat is None or lng is None or not city_zone:
                        return {
                            "status": "validation_error",
                            "message": (
                                "lat, lng, and cityZone required when updating listing location."
                            ),
                        }

                    _upsert_listing_location(
                        cur,
                        listing_id,
                        lat=float(lat),
                        lng=float(lng),
                        city_zone=str(city_zone),
                        pickup_address=pickup_address,
                    )
                    cur.execute(
                        "UPDATE vehicle_listing SET updated_at = %s WHERE listing_id = %s",
                        (datetime.utcnow(), listing_id),
                    )

                if image_urls:
                    _associate_listing_image_urls(
                        cur,
                        listing_id,
                        image_urls,
                        listing.get("owner_user_id"),
                    )
                    cur.execute(
                        "UPDATE vehicle_listing SET updated_at = %s WHERE listing_id = %s",
                        (datetime.utcnow(), listing_id),
                    )

                conn.commit()
        return self.get_listing(listing_id)

    def upsert_location(self, actor: dict, listing_id: int, payload: dict) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                listing = self._fetch_listing_ownership(cur, listing_id)
                if not listing or not self._can_manage_listing(actor, listing):
                    return {"status": "not_found", "message": "Listing not found for actor."}
                _upsert_listing_location(
                    cur,
                    listing_id,
                    lat=float(payload["lat"]),
                    lng=float(payload["lng"]),
                    city_zone=str(payload["cityZone"]),
                    pickup_address=payload.get("pickupAddress"),
                )
                cur.execute(
                    "UPDATE vehicle_listing SET updated_at = %s WHERE listing_id = %s",
                    (datetime.utcnow(), listing_id),
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

    def owner_analytics(self, owner_user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                analytics = _fetch_dashboard_analytics(
                    cur,
                    "l.owner_user_id = %s AND l.source_type = 'OWNER'",
                    (owner_user_id,),
                )
        return {"status": "success", "analytics": analytics}


listing_service = ListingService()
