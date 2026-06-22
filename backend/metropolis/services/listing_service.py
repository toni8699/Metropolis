from __future__ import annotations

from datetime import datetime

from psycopg2.extras import Json, RealDictCursor

from metropolis.core.config import settings
from metropolis.core.db import get_connection
from metropolis.services.marketplace_common import (
    _BOOKING_HOLD_STATUSES,
    LISTING_SELECT_SQL,
    _associate_listing_image_urls,
    _fetch_dashboard_analytics,
    _listing_image_urls,
    _resolve_guidelines,
    _resolve_listing_title,
    _upsert_listing_location,
    build_listing_search_filters,
    count_listing_search_matches,
    hydrate_listing_rows,
    replace_listing_features,
    resolve_company_location,
    sync_listing_cache_from_asset,
    validate_feature_ids,
)
from metropolis.services.vin_decode_service import (
    decode_and_map_for_asset,
    normalize_fuel_type,
    normalize_transmission,
    normalize_vin,
    upsert_vin_metadata,
)

_METAL_PAYLOAD_KEYS = {
    "vin": "vin",
    "make": "make",
    "model": "model",
    "year": "model_year",
    "transmission": "transmission",
    "fuelType": "fuel_type",
    "seats": "seats",
    "bodyTypeId": "body_type_id",
    "bodyTypeOther": "body_type_other",
}


def _normalize_body_type_other(cur, body_type_id: int | None, body_type_other: object) -> dict:
    if body_type_id is None:
        return {"status": "success", "value": None}
    cur.execute(
        "SELECT code FROM ref_body_type WHERE body_type_id = %s",
        (body_type_id,),
    )
    row = cur.fetchone()
    if not row:
        return {"status": "validation_error", "message": "Invalid body type."}
    label = str(body_type_other or "").strip() or None
    if row["code"] == "OTHER":
        if not label:
            return {
                "status": "validation_error",
                "message": "Describe your body type when Other is selected.",
            }
        return {"status": "success", "value": label}
    return {"status": "success", "value": None}


def _management_mode(*, is_company_owned: bool) -> str:
    # ponytail: derived until host opt-in to company-managed hosting exists.
    return "COMPANY_MANAGED" if is_company_owned else "SELF"


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
            SELECT listing_id, owner_user_id, vehicle_id
            FROM vehicle_listing
            WHERE listing_id = %s
            """,
            (listing_id,),
        )
        return cur.fetchone()

    def _extract_feature_ids(self, payload: dict) -> list[int] | None:
        if "featureIds" in payload or "feature_ids" in payload:
            raw = payload.get("featureIds", payload.get("feature_ids"))
            if raw is None:
                return []
            if not isinstance(raw, list):
                return []
            return [int(value) for value in raw]
        if "features" in payload and isinstance(payload.get("features"), list):
            return None
        return None

    def _build_asset_facts(self, cur, payload: dict, *, is_company_owned: bool) -> dict:
        mode = _management_mode(is_company_owned=is_company_owned)
        raw_vin = payload.get("vin")
        normalized_vin = normalize_vin(str(raw_vin)) if raw_vin not in (None, "") else None
        facts = {
            "vin": normalized_vin,
            "make": payload.get("make") or payload.get("brand"),
            "model": payload.get("model"),
            "model_year": payload.get("year"),
            "transmission": payload.get("transmission"),
            "fuel_type": payload.get("fuelType"),
            "seats": payload.get("seats"),
            "body_type_id": payload.get("bodyTypeId") or payload.get("body_type_id"),
            "is_vin_verified": False,
        }
        if normalized_vin:
            decoded = decode_and_map_for_asset(cur, normalized_vin)
            if decoded.get("status") == "validation_error":
                return decoded
            if decoded.get("status") == "error":
                return decoded
            decoded_facts = decoded.get("facts") or {}
            for key, value in decoded_facts.items():
                if value is not None and facts.get(key) in (None, ""):
                    facts[key] = value
            facts["_raw_decode"] = decoded.get("raw")
            facts["is_vin_verified"] = bool(facts.get("make") or facts.get("model"))
        elif mode == "COMPANY_MANAGED":
            return {
                "status": "validation_error",
                "message": "VIN is required for company-managed listings.",
            }
        else:
            if not facts.get("make") or not facts.get("model") or facts.get("model_year") is None:
                return {
                    "status": "validation_error",
                    "message": "make, model, and year are required when VIN is not provided.",
                }
        if facts.get("seats") is not None:
            facts["seats"] = int(facts["seats"])
        if facts.get("body_type_id") is not None:
            facts["body_type_id"] = int(facts["body_type_id"])
        if facts.get("model_year") is not None:
            facts["model_year"] = int(facts["model_year"])
        if facts.get("transmission") is not None:
            facts["transmission"] = normalize_transmission(facts["transmission"])
        if facts.get("fuel_type") is not None:
            facts["fuel_type"] = normalize_fuel_type(facts["fuel_type"])
        other_check = _normalize_body_type_other(
            cur,
            facts.get("body_type_id"),
            payload.get("bodyTypeOther") or payload.get("body_type_other"),
        )
        if other_check.get("status") != "success":
            return other_check
        facts["body_type_other"] = other_check.get("value")
        return {"status": "success", "facts": facts}

    def create_listing(self, actor: dict, payload: dict) -> dict:
        if not actor.get("isAdmin") and not settings.allow_user_listings:
            return {
                "status": "forbidden",
                "message": "User vehicle listings are disabled. Admin fleet only.",
            }
        is_company_owned = bool(payload.get("isCompanyOwned")) and bool(actor.get("isAdmin"))
        owner_user_id = actor["userId"]
        source_type = "OWNER"

        image_urls = _listing_image_urls(payload)
        address = payload.get("pickupAddress")
        latitude = payload.get("latitude")
        longitude = payload.get("longitude")
        guidelines = _resolve_guidelines(payload)
        listing_title = _resolve_listing_title(payload)

        seats = payload.get("seats")
        doors = payload.get("doors")
        if seats is not None:
            seats = int(seats)
        if doors is not None:
            doors = int(doors)
        if latitude is not None:
            latitude = float(latitude)
        if longitude is not None:
            longitude = float(longitude)
        if seats is not None and seats <= 0:
            return {"status": "validation_error", "message": "seats must be > 0."}
        if doors is not None and doors <= 0:
            return {"status": "validation_error", "message": "doors must be > 0."}

        feature_ids = self._extract_feature_ids(payload)

        try:
            with get_connection() as conn:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                asset_build = self._build_asset_facts(
                    cur, payload, is_company_owned=is_company_owned
                )
                if asset_build.get("status") != "success":
                    return asset_build
                facts = asset_build["facts"]

                if is_company_owned:
                    company_source_type = str(payload.get("locationSourceType") or "").upper()
                    if company_source_type in {"BRANCH", "PARKING_SPOT"}:
                        location = resolve_company_location(cur, payload)
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
                    if not facts.get("make") or not facts.get("model"):
                        return {
                            "status": "validation_error",
                            "message": "make and model are required for company-owned listings.",
                        }

                if feature_ids is not None:
                    validated = validate_feature_ids(cur, feature_ids)
                    if validated["status"] != "success":
                        return validated

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
                      vin,
                      vehicle_category,
                      body_type_id,
                      body_type_other,
                      owner_type,
                      owner_party_user_id,
                      owner_party_name,
                      asset_status,
                      make,
                      model,
                      model_year,
                      fuel_type,
                      transmission,
                      seats,
                      is_vin_verified
                    )
                    VALUES (
                      %s,
                      'STANDARD'::vehicle_category,
                      %s,
                      %s,
                      %s::vehicle_owner_type,
                      %s,
                      %s,
                      %s::vehicle_asset_status,
                      %s,
                      %s,
                      %s,
                      %s,
                      %s,
                      %s,
                      %s
                    )
                    RETURNING vehicle_id, make, model, model_year,
                      transmission, fuel_type, seats
                    """,
                    (
                        facts.get("vin"),
                        facts.get("body_type_id"),
                        facts.get("body_type_other"),
                        owner_type,
                        owner_user_id,
                        owner_party_name,
                        asset_status,
                        facts.get("make"),
                        facts.get("model"),
                        facts.get("model_year"),
                        facts.get("fuel_type"),
                        facts.get("transmission"),
                        facts.get("seats"),
                        bool(facts.get("is_vin_verified")),
                    ),
                )
                asset_row = cur.fetchone()
                vehicle_id = asset_row["vehicle_id"]
                if facts.get("vin") and facts.get("_raw_decode"):
                    upsert_vin_metadata(
                        cur,
                        vehicle_id,
                        str(facts["vin"]),
                        facts["_raw_decode"],
                    )

                pickup_address = address or location_address
                cur.execute(
                    """
                    INSERT INTO vehicle_listing
                    (
                      owner_user_id, created_by_user_id, vehicle_id, source_type, title,
                      listing_title, make, model, year,
                      description, guidelines, transmission, fuel_type, seats, doors,
                      features, pickup_notes_template, price_per_day, active, status,
                      is_company_owned, instant_book, location_source_type, branch_id,
                      parking_spot_id
                    )
                    VALUES (
                      %s, %s, %s, %s::listing_source_type, %s,
                      %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s,
                      %s::jsonb,
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
                        listing_title,
                        listing_title,
                        asset_row["make"],
                        asset_row["model"],
                        asset_row["model_year"],
                        payload.get("description"),
                        guidelines,
                        asset_row["transmission"],
                        asset_row["fuel_type"],
                        asset_row["seats"],
                        doors,
                        Json([]),
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
                sync_listing_cache_from_asset(cur, vehicle_id)
                if feature_ids is not None:
                    replace_listing_features(cur, listing_id, feature_ids)
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
        clauses, params, error = build_listing_search_filters(
            query,
            booking_hold_statuses=_BOOKING_HOLD_STATUSES,
        )
        if error:
            return error

        limit = int(query.get("limit") or 24)
        offset = int(query.get("offset") or 0)
        where_sql = " AND ".join(clauses)
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                total_count = count_listing_search_matches(cur, clauses, params)
                cur.execute(
                    f"""
                    {LISTING_SELECT_SQL}
                    WHERE {where_sql}
                    ORDER BY l.updated_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (*params, limit, offset),
                )
                listings = hydrate_listing_rows(cur, cur.fetchall())
        return {
            "status": "success",
            "listings": listings,
            "totalCount": total_count,
            "limit": limit,
            "offset": offset,
        }

    def count_listings(self, query: dict) -> dict:
        clauses, params, error = build_listing_search_filters(
            query,
            booking_hold_statuses=_BOOKING_HOLD_STATUSES,
        )
        if error:
            return error

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                total_count = count_listing_search_matches(cur, clauses, params)
        return {"status": "success", "totalCount": total_count}

    def _update_vehicle_asset(self, cur, vehicle_id: int, payload: dict) -> dict | None:
        fields = []
        params = []
        for payload_key, column in _METAL_PAYLOAD_KEYS.items():
            if payload_key not in payload:
                continue
            value = payload[payload_key]
            if payload_key in {"year", "seats", "bodyTypeId"} and value is not None:
                value = int(value)
            if payload_key == "transmission" and value is not None:
                value = normalize_transmission(value)
            if payload_key == "fuelType" and value is not None:
                value = normalize_fuel_type(value)
            fields.append(f"{column} = %s")
            params.append(value)
        if not fields:
            return None
        fields.append("updated_at = %s")
        params.append(datetime.utcnow())
        params.append(vehicle_id)
        cur.execute(
            f"""
            UPDATE vehicle_asset
            SET {", ".join(fields)}
            WHERE vehicle_id = %s
            RETURNING vehicle_id
            """,
            tuple(params),
        )
        if not cur.fetchone():
            return {"status": "not_found", "message": "Vehicle asset not found."}
        sync_listing_cache_from_asset(cur, vehicle_id)
        return None

    def update_listing(self, actor: dict, listing_id: int, payload: dict) -> dict:
        try:
            payload = self._apply_lifecycle_compat(payload)
        except ValueError as exc:
            return {"status": "validation_error", "message": str(exc)}
        if "rules" in payload and "guidelines" not in payload:
            payload = {**payload, "guidelines": payload["rules"]}
        if "make" not in payload and payload.get("brand") is not None:
            payload = {**payload, "make": payload.get("brand")}
        if "title" in payload and "listingTitle" not in payload:
            payload = {**payload, "listingTitle": payload["title"]}

        listing_mapping = {
            "listingTitle": "listing_title",
            "description": "description",
            "guidelines": "guidelines",
            "doors": "doors",
            "pickupNotesTemplate": "pickup_notes_template",
            "pricePerDay": "price_per_day",
            "active": "active",
            "status": "status",
            "isCompanyOwned": "is_company_owned",
            "instantBook": "instant_book",
        }
        listing_fields = []
        listing_params = []
        for key, column in listing_mapping.items():
            if key in payload:
                listing_fields.append(f"{column} = %s")
                listing_params.append(payload[key])
        if "listingTitle" in payload:
            listing_fields.append("title = %s")
            listing_params.append(payload["listingTitle"])

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
        has_metal_update = any(key in payload for key in _METAL_PAYLOAD_KEYS)
        feature_ids = self._extract_feature_ids(payload)

        if (
            not listing_fields
            and not has_location_update
            and not image_urls
            and not has_metal_update
            and feature_ids is None
        ):
            return {"status": "validation_error", "message": "No fields to update."}

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                listing = self._fetch_listing_ownership(cur, listing_id)
                if not listing or not self._can_manage_listing(actor, listing):
                    return {"status": "not_found", "message": "Listing not found for actor."}

                vehicle_id = listing.get("vehicle_id")
                if has_metal_update:
                    if not vehicle_id:
                        asset_build = self._build_asset_facts(
                            cur,
                            payload,
                            is_company_owned=bool(actor.get("isAdmin")),
                        )
                        if asset_build.get("status") != "success":
                            return asset_build
                        facts = asset_build["facts"]
                        cur.execute(
                            """
                            INSERT INTO vehicle_asset (
                              vin, vehicle_category, body_type_id, body_type_other, owner_type,
                              owner_party_user_id, asset_status, make, model, model_year,
                              fuel_type, transmission, seats, is_vin_verified
                            )
                            VALUES (
                              %s, 'STANDARD'::vehicle_category, %s, %s,
                              'INDEPENDENT_HOST'::vehicle_owner_type, %s,
                              'ACTIVE'::vehicle_asset_status, %s, %s, %s, %s, %s, %s, %s
                            )
                            RETURNING vehicle_id
                            """,
                            (
                                facts.get("vin"),
                                facts.get("body_type_id"),
                                facts.get("body_type_other"),
                                listing["owner_user_id"],
                                facts.get("make"),
                                facts.get("model"),
                                facts.get("model_year"),
                                facts.get("fuel_type"),
                                facts.get("transmission"),
                                facts.get("seats"),
                                bool(facts.get("is_vin_verified")),
                            ),
                        )
                        vehicle_id = cur.fetchone()["vehicle_id"]
                        cur.execute(
                            """
                            UPDATE vehicle_listing
                            SET vehicle_id = %s, updated_at = %s
                            WHERE listing_id = %s
                            """,
                            (vehicle_id, datetime.utcnow(), listing_id),
                        )
                    else:
                        asset_error = self._update_vehicle_asset(cur, vehicle_id, payload)
                        if asset_error:
                            return asset_error

                if feature_ids is not None:
                    validated = validate_feature_ids(cur, feature_ids)
                    if validated["status"] != "success":
                        return validated

                if listing_fields:
                    listing_fields.append("updated_at = %s")
                    listing_params.append(datetime.utcnow())
                    listing_params.append(listing_id)
                    cur.execute(
                        f"""
                        UPDATE vehicle_listing
                        SET {", ".join(listing_fields)}
                        WHERE listing_id = %s
                        RETURNING listing_id
                        """,
                        tuple(listing_params),
                    )
                    if not cur.fetchone():
                        return {"status": "not_found", "message": "Listing not found for actor."}

                if feature_ids is not None:
                    replace_listing_features(cur, listing_id, feature_ids)

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

    def list_listing_availability(self, actor: dict, listing_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                listing = self._fetch_listing_ownership(cur, listing_id)
                if not listing or not self._can_manage_listing(actor, listing):
                    return {"status": "not_found", "message": "Listing not found for actor."}
                cur.execute(
                    """
                    SELECT availability_id, listing_id, start_at, end_at, status
                    FROM listing_availability
                    WHERE listing_id = %s AND status = 'BLOCKED'::availability_status
                    ORDER BY start_at ASC
                    """,
                    (listing_id,),
                )
                rows = cur.fetchall()
        return {
            "status": "success",
            "availability": [
                {
                    "availabilityId": row["availability_id"],
                    "listingId": row["listing_id"],
                    "startAt": row["start_at"].isoformat(),
                    "endAt": row["end_at"].isoformat(),
                    "status": row["status"],
                }
                for row in rows
            ],
        }

    def add_availability(self, actor: dict, listing_id: int, payload: dict) -> dict:
        status = payload.get("status", "BLOCKED")
        if status not in {"BLOCKED", "AVAILABLE"}:
            return {"status": "bad_request", "message": "Invalid availability status."}
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
                        status,
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

    def delete_availability(self, actor: dict, listing_id: int, availability_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                listing = self._fetch_listing_ownership(cur, listing_id)
                if not listing or not self._can_manage_listing(actor, listing):
                    return {"status": "not_found", "message": "Listing not found for actor."}
                cur.execute(
                    """
                    DELETE FROM listing_availability
                    WHERE availability_id = %s AND listing_id = %s
                    RETURNING availability_id
                    """,
                    (availability_id, listing_id),
                )
                deleted = cur.fetchone()
                if not deleted:
                    return {"status": "not_found", "message": "Availability window not found."}
                conn.commit()
        return {"status": "success"}

    def delete_listing(self, actor: dict, listing_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                listing = self._fetch_listing_ownership(cur, listing_id)
                if not listing:
                    return {"status": "not_found", "message": "Listing not found."}
                if not self._can_manage_listing(actor, listing):
                    return {"status": "forbidden", "message": "No listing access."}
                from metropolis.services import uploads_service

                uploads_service.delete_listing_s3_files(listing_id)
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
