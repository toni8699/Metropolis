from __future__ import annotations

import hashlib
from datetime import datetime

LISTING_SELECT_SQL = """
    SELECT l.*,
           va.vin AS asset_vin,
           va.body_type_id AS asset_body_type_id,
           va.body_type_other AS asset_body_type_other,
           va.is_vin_verified AS asset_is_vin_verified,
           loc.lat,
           loc.lng,
           loc.geohash,
           loc.city_zone,
           loc.pickup_address,
           u.full_name AS owner_name,
           u.profile_photo_url AS owner_profile_photo_url
    FROM vehicle_listing l
    LEFT JOIN vehicle_asset va ON va.vehicle_id = l.vehicle_id
    LEFT JOIN listing_location loc ON loc.listing_id = l.listing_id
    LEFT JOIN app_user u ON u.user_id = l.owner_user_id
"""

LISTING_SEARCH_FROM_SQL = """
    FROM vehicle_listing l
    LEFT JOIN vehicle_asset va ON va.vehicle_id = l.vehicle_id
    LEFT JOIN listing_location loc ON loc.listing_id = l.listing_id
"""

# Admin dashboard: company fleet only (not third-party host listings).
_COMPANY_FLEET_FILTER = "l.is_company_owned = TRUE"
_HOST_LISTING_FILTER = "l.source_type = 'OWNER' AND l.is_company_owned = FALSE"

_BOOKING_SELECT_SQL = """
    SELECT
        b.booking_id,
        b.listing_id,
        b.renter_user_id,
        b.start_at,
        b.end_at,
        b.status,
        b.price_snapshot_json,
        b.created_at,
        b.updated_at,
        l.title AS listing_title_legacy,
        COALESCE(l.listing_title, l.title) AS listing_marketing_title,
        l.source_type,
        l.owner_user_id,
        loc.city_zone,
        u.email AS renter_email
    FROM booking b
    JOIN vehicle_listing l ON l.listing_id = b.listing_id
    LEFT JOIN listing_location loc ON loc.listing_id = l.listing_id
    LEFT JOIN app_user u ON u.user_id = b.renter_user_id
"""

_BOOKING_NEEDS_REVIEW_SQL = """
  (
    b.status = 'COMPLETED'
    AND (NOW() AT TIME ZONE 'UTC') <= b.end_at + INTERVAL '30 days'
    AND NOT EXISTS (
      SELECT 1
      FROM review r
      WHERE r.booking_id = b.booking_id
        AND r.author_user_id = b.renter_user_id
        AND r.target_type = 'LISTING'
    )
  )
"""

_BOOKING_HOLD_STATUSES = ("PENDING", "PENDING_APPROVAL", "CONFIRMED", "IN_PROGRESS")
_BOOKING_BLOCKING_STATUSES = ("CONFIRMED", "IN_PROGRESS")


def listing_available_for_window_sql(statuses: tuple[str, ...]) -> str:
    """SQL fragment: listing has no overlapping holds or blocked availability windows."""
    status_sql = ", ".join(["%s::booking_status"] * len(statuses))
    return f"""
NOT EXISTS (
  SELECT 1
  FROM booking b
  JOIN vehicle_listing vl ON vl.listing_id = b.listing_id
  WHERE b.status IN ({status_sql})
    AND b.start_at < %s
    AND b.end_at > %s
    AND (
      b.listing_id = l.listing_id
      OR (
        l.source_type = 'FLEET'
        AND l.fleet_vehicle_vin IS NOT NULL
        AND vl.fleet_vehicle_vin = l.fleet_vehicle_vin
      )
    )
)
AND NOT EXISTS (
  SELECT 1
  FROM listing_availability la
  WHERE la.listing_id = l.listing_id
    AND la.status = 'BLOCKED'
    AND la.start_at < %s
    AND la.end_at > %s
)
"""


def _resolve_search_window(query: dict) -> tuple[datetime, datetime] | None | dict:
    """Return (start_at, end_at), None when no date filter, or a validation_error dict."""
    start_at = query.get("start_at") or query.get("start")
    end_at = query.get("end_at") or query.get("end")
    if start_at is None and end_at is None:
        return None
    if start_at is None or end_at is None:
        return {
            "status": "validation_error",
            "message": "Both start_at and end_at are required for date-aware search.",
        }
    if end_at <= start_at:
        return {"status": "validation_error", "message": "end_at must be after start_at."}
    return start_at, end_at


def build_listing_search_filters(
    query: dict,
    *,
    booking_hold_statuses: tuple[str, ...],
) -> tuple[list[str], list, dict | None]:
    """Build WHERE clauses for public listing search. Returns (clauses, params, error)."""
    clauses = ["COALESCE(l.status, 'ACTIVE') = 'ACTIVE'"]
    params: list = []

    if query.get("city_zone"):
        clauses.append("loc.city_zone = %s")
        params.append(query["city_zone"])
    if query.get("bbox"):
        min_lng, min_lat, max_lng, max_lat = (float(x) for x in query["bbox"].split(","))
        clauses.extend(["loc.lng BETWEEN %s AND %s", "loc.lat BETWEEN %s AND %s"])
        params.extend([min_lng, max_lng, min_lat, max_lat])

    window = _resolve_search_window(query)
    if isinstance(window, dict):
        return clauses, params, window
    if window is not None:
        start_at, end_at = window
        clauses.append(listing_available_for_window_sql(booking_hold_statuses))
        params.extend([*booking_hold_statuses, end_at, start_at, end_at, start_at])

    min_price = query.get("min_price")
    if min_price is not None:
        clauses.append("l.price_per_day >= %s")
        params.append(float(min_price))
    max_price = query.get("max_price")
    if max_price is not None:
        clauses.append("l.price_per_day <= %s")
        params.append(float(max_price))

    body_type_ids = query.get("body_type_ids")
    if body_type_ids:
        clauses.append("va.body_type_id = ANY(%s)")
        params.append(body_type_ids)

    transmission = query.get("transmission")
    if transmission:
        clauses.append("va.transmission = %s::transmission_type")
        params.append(str(transmission))

    fuel_types = query.get("fuel_types")
    if fuel_types:
        clauses.append("va.fuel_type = ANY(%s::fuel_type_enum[])")
        params.append(fuel_types)

    seats = list(query.get("seats") or [])
    seats_gte = query.get("seats_gte")
    if seats_gte is None and seats and 7 in seats:
        seats_gte = 7
        seats = [value for value in seats if value != 7]
    seat_parts: list[str] = []
    seat_params: list = []
    if seats:
        seat_parts.append("va.seats = ANY(%s)")
        seat_params.append(seats)
    if seats_gte is not None:
        seat_parts.append("va.seats >= %s")
        seat_params.append(int(seats_gte))
    if seat_parts:
        clauses.append(f"({' OR '.join(seat_parts)})")
        params.extend(seat_params)

    feature_ids = query.get("feature_ids")
    if feature_ids:
        clauses.append(
            """
            l.listing_id IN (
                SELECT lf.listing_id
                FROM listing_feature lf
                WHERE lf.feature_id = ANY(%s)
                GROUP BY lf.listing_id
                HAVING COUNT(DISTINCT lf.feature_id) = %s
            )
            """
        )
        params.extend([feature_ids, len(feature_ids)])

    return clauses, params, None


def count_listing_search_matches(cur, clauses: list[str], params: list) -> int:
    where_sql = " AND ".join(clauses)
    cur.execute(
        f"""
        SELECT COUNT(*) AS total_count
        {LISTING_SEARCH_FROM_SQL}
        WHERE {where_sql}
        """,
        tuple(params),
    )
    return int(cur.fetchone()["total_count"] or 0)


def _fetch_dashboard_analytics(cur, listing_where: str, params: tuple = ()) -> dict:
    cur.execute(
        f"""
        SELECT
            COUNT(DISTINCT l.listing_id) AS listing_count,
            COUNT(DISTINCT l.listing_id) FILTER (
              WHERE COALESCE(
                l.status,
                CASE WHEN l.active THEN 'ACTIVE' ELSE 'INACTIVE' END
              ) = 'ACTIVE'
            ) AS active_listings,
            COUNT(DISTINCT b.booking_id) AS booking_count,
            COALESCE(
                SUM((b.price_snapshot_json->>'pricePerDay')::numeric), 0
            ) AS gross_daily_revenue,
            COALESCE(
                SUM(p.amount_cents) FILTER (WHERE p.status = 'succeeded'), 0
            ) AS paid_revenue_cents
        FROM vehicle_listing l
        LEFT JOIN booking b ON b.listing_id = l.listing_id
        LEFT JOIN payment p ON p.booking_id = b.booking_id
        WHERE {listing_where}
        """,
        params,
    )
    row = cur.fetchone()
    return {
        "listingCount": int(row["listing_count"] or 0),
        "activeListings": int(row["active_listings"] or 0),
        "bookingCount": int(row["booking_count"] or 0),
        "grossDailyRevenue": float(row["gross_daily_revenue"] or 0),
        "paidRevenue": round(float(row["paid_revenue_cents"] or 0) / 100.0, 2),
    }


def _resolve_guidelines(payload: dict) -> str | None:
    guidelines = payload.get("guidelines")
    if guidelines is None:
        guidelines = payload.get("rules")
    return guidelines


def _resolve_listing_title(payload: dict) -> str:
    for key in ("listingTitle", "listing_title", "title"):
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    make = payload.get("make") or payload.get("brand")
    model = payload.get("model")
    year = payload.get("year")
    parts = [p for p in [make, model, str(year) if year else None] if p]
    return " ".join(parts) if parts else "User listed car"


def resolve_company_location(cur, payload: dict) -> dict:
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


def sync_listing_cache_from_asset(cur, vehicle_id: int) -> None:
    cur.execute("SELECT sync_listing_cache_from_asset(%s)", (vehicle_id,))


def fetch_listing_features_map(cur, listing_ids: list[int]) -> dict[int, list[dict]]:
    if not listing_ids:
        return {}
    cur.execute(
        """
        SELECT lf.listing_id, rf.feature_id, rf.code, rf.name, rf.icon_key, rf.category
        FROM listing_feature lf
        JOIN ref_feature rf ON rf.feature_id = lf.feature_id
        WHERE lf.listing_id = ANY(%s)
        ORDER BY lf.listing_id, rf.sort_order, rf.name
        """,
        (listing_ids,),
    )
    features_by_listing: dict[int, list[dict]] = {}
    for row in cur.fetchall():
        features_by_listing.setdefault(row["listing_id"], []).append(
            {
                "featureId": row["feature_id"],
                "code": row["code"],
                "name": row["name"],
                "iconKey": row["icon_key"],
                "category": row["category"],
            }
        )
    return features_by_listing


def validate_feature_ids(cur, feature_ids: list[int]) -> dict:
    if not feature_ids:
        return {"status": "success", "features": []}
    cur.execute(
        """
        SELECT feature_id, name
        FROM ref_feature
        WHERE feature_id = ANY(%s) AND is_active = TRUE
        """,
        (feature_ids,),
    )
    rows = cur.fetchall()
    found = {row["feature_id"] for row in rows}
    missing = [fid for fid in feature_ids if fid not in found]
    if missing:
        return {
            "status": "validation_error",
            "message": f"Unknown or inactive feature ids: {missing}",
        }
    return {"status": "success", "features": rows}


def replace_listing_features(cur, listing_id: int, feature_ids: list[int]) -> None:
    cur.execute("DELETE FROM listing_feature WHERE listing_id = %s", (listing_id,))
    if not feature_ids:
        cur.execute(
            "UPDATE vehicle_listing SET features = %s::jsonb WHERE listing_id = %s",
            ("[]", listing_id),
        )
        return
    cur.executemany(
        """
        INSERT INTO listing_feature (listing_id, feature_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """,
        [(listing_id, feature_id) for feature_id in feature_ids],
    )
    cur.execute(
        """
        UPDATE vehicle_listing
        SET features = (
          SELECT COALESCE(jsonb_agg(rf.name ORDER BY rf.sort_order, rf.name), '[]'::jsonb)
          FROM listing_feature lf
          JOIN ref_feature rf ON rf.feature_id = lf.feature_id
          WHERE lf.listing_id = %s
        )
        WHERE listing_id = %s
        """,
        (listing_id, listing_id),
    )


def list_body_types(cur) -> list[dict]:
    cur.execute(
        """
        SELECT body_type_id, code, display_name, sort_order
        FROM ref_body_type
        ORDER BY sort_order, display_name
        """
    )
    return [
        {
            "body_type_id": row["body_type_id"],
            "code": row["code"],
            "display_name": row["display_name"],
            "sort_order": row["sort_order"],
        }
        for row in cur.fetchall()
    ]


def list_features(cur, category: str | None = None) -> list[dict]:
    if category:
        cur.execute(
            """
            SELECT feature_id, code, name, icon_key, category, sort_order
            FROM ref_feature
            WHERE is_active = TRUE AND category = %s
            ORDER BY sort_order, name
            """,
            (category,),
        )
    else:
        cur.execute(
            """
            SELECT feature_id, code, name, icon_key, category, sort_order
            FROM ref_feature
            WHERE is_active = TRUE
            ORDER BY category, sort_order, name
            """
        )
    return [
        {
            "feature_id": row["feature_id"],
            "code": row["code"],
            "name": row["name"],
            "icon_key": row["icon_key"],
            "category": row["category"],
            "sort_order": row["sort_order"],
        }
        for row in cur.fetchall()
    ]


def _listing_image_urls(payload: dict) -> list[str]:
    urls: list[str] = []
    for key in ("images", "photos"):
        values = payload.get(key)
        if not values:
            continue
        if isinstance(values, list):
            urls.extend(str(value).strip() for value in values if str(value).strip())
    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url not in seen:
            seen.add(url)
            deduped.append(url)
    return deduped


def _fetch_listing_ratings_map(cur, listing_ids: list[int]) -> dict[int, dict]:
    if not listing_ids:
        return {}
    cur.execute(
        """
        SELECT
          target_listing_id AS listing_id,
          ROUND(AVG(rating)::numeric, 2) AS average_rating,
          COUNT(*)::int AS review_count
        FROM review
        WHERE target_listing_id = ANY(%s)
          AND target_type = 'LISTING'
        GROUP BY target_listing_id
        """,
        (listing_ids,),
    )
    return {
        row["listing_id"]: {
            "average_rating": float(row["average_rating"])
            if row["average_rating"] is not None
            else None,
            "review_count": int(row["review_count"] or 0),
        }
        for row in cur.fetchall()
    }


def fetch_listing_images_map(cur, listing_ids: list[int]) -> dict[int, list[str]]:
    if not listing_ids:
        return {}
    cur.execute(
        """
        SELECT li.listing_id, fa.file_url
        FROM listing_image li
        JOIN file_asset fa ON fa.file_id = li.file_id
        WHERE li.listing_id = ANY(%s)
        ORDER BY li.listing_id, li.display_order, fa.created_at
        """,
        (listing_ids,),
    )
    images_by_listing: dict[int, list[str]] = {}
    for row in cur.fetchall():
        images_by_listing.setdefault(row["listing_id"], []).append(row["file_url"])
    return images_by_listing


def _associate_listing_image_urls(
    cur,
    listing_id: int,
    urls: list[str],
    owner_user_id: int | None,
) -> None:
    for display_order, url in enumerate(urls):
        cur.execute(
            """
            SELECT file_id
            FROM file_asset
            WHERE listing_id = %s AND file_url = %s
            """,
            (listing_id, url),
        )
        existing = cur.fetchone()
        if existing:
            file_id = existing["file_id"]
        else:
            object_key = f"external/{listing_id}/{hashlib.sha256(url.encode('utf-8')).hexdigest()}"
            cur.execute(
                """
                INSERT INTO file_asset (
                  owner_user_id, listing_id, bucket, object_key, file_url, scope
                )
                VALUES (%s, %s, 'external', %s, %s, 'OWNER_LISTING')
                ON CONFLICT (object_key) DO UPDATE
                SET listing_id = COALESCE(file_asset.listing_id, EXCLUDED.listing_id),
                    file_url = EXCLUDED.file_url
                RETURNING file_id
                """,
                (owner_user_id, listing_id, object_key, url),
            )
            file_id = cur.fetchone()["file_id"]
        cur.execute(
            """
            INSERT INTO listing_image (listing_id, file_id, display_order)
            VALUES (%s, %s, %s)
            ON CONFLICT (listing_id, file_id) DO UPDATE
            SET display_order = EXCLUDED.display_order
            """,
            (listing_id, file_id, display_order),
        )


def _upsert_listing_location(
    cur,
    listing_id: int,
    *,
    lat: float,
    lng: float,
    city_zone: str,
    pickup_address: str | None,
) -> None:
    cur.execute(
        """
        INSERT INTO listing_location (
            listing_id, lat, lng, geohash, city_zone, pickup_address, last_parked_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (listing_id) DO UPDATE
        SET lat = EXCLUDED.lat,
            lng = EXCLUDED.lng,
            geohash = EXCLUDED.geohash,
            city_zone = EXCLUDED.city_zone,
            pickup_address = COALESCE(
                EXCLUDED.pickup_address, listing_location.pickup_address
            ),
            last_parked_at = NOW()
        """,
        (
            listing_id,
            lat,
            lng,
            _simple_geohash(lat, lng),
            city_zone,
            pickup_address,
        ),
    )


def hydrate_listing_rows(cur, rows: list[dict]) -> list[dict]:
    listing_ids = [row["listing_id"] for row in rows]
    images_by_listing = fetch_listing_images_map(cur, listing_ids)
    ratings_by_listing = _fetch_listing_ratings_map(cur, listing_ids)
    features_by_listing = fetch_listing_features_map(cur, listing_ids)
    return [
        _to_listing_row(
            row,
            images_by_listing.get(row["listing_id"], []),
            ratings_by_listing.get(row["listing_id"]),
            features_by_listing.get(row["listing_id"]),
        )
        for row in rows
    ]


def _to_listing_row(
    row: dict,
    image_urls: list[str] | None = None,
    ratings: dict | None = None,
    feature_rows: list[dict] | None = None,
) -> dict:
    urls = image_urls if image_urls is not None else []
    lat = row.get("lat")
    lng = row.get("lng")
    guidelines = row.get("guidelines")
    pickup_address = row.get("pickup_address")
    rating_stats = ratings or {}
    average_rating = rating_stats.get("average_rating")
    if average_rating is None and row.get("average_rating") is not None:
        average_rating = float(row["average_rating"])
    review_count = rating_stats.get("review_count")
    if review_count is None:
        review_count = int(row.get("review_count") or 0)

    listing_title = row.get("listing_title") or row.get("title")
    feature_objs = feature_rows or []
    feature_names = (
        [f["name"] for f in feature_objs] if feature_objs else (row.get("features") or [])
    )
    feature_ids = [f["featureId"] for f in feature_objs] if feature_objs else []

    return {
        "listingId": row["listing_id"],
        "vehicleId": row.get("vehicle_id"),
        "sourceType": row["source_type"],
        "title": listing_title,
        "listingTitle": listing_title,
        "make": row.get("make"),
        "model": row.get("model"),
        "year": row.get("year"),
        "vin": row.get("asset_vin"),
        "isVinVerified": bool(row.get("asset_is_vin_verified")),
        "bodyTypeId": row.get("asset_body_type_id"),
        "bodyTypeOther": row.get("asset_body_type_other"),
        "vehicleClassId": None,
        "description": row.get("description"),
        "guidelines": guidelines,
        "transmission": row.get("transmission"),
        "fuelType": row.get("fuel_type"),
        "seats": row.get("seats"),
        "doors": row.get("doors"),
        "features": feature_names,
        "featureIds": feature_ids,
        "featureDetails": feature_objs,
        "images": urls,
        "pickupNotesTemplate": row.get("pickup_notes_template"),
        "pricePerDay": float(row["price_per_day"]),
        "active": row["active"],
        "status": row.get("status"),
        "ownerUserId": row["owner_user_id"],
        "isCompanyOwned": bool(row.get("is_company_owned")),
        "ownerName": row["owner_name"],
        "ownerProfilePhotoUrl": row.get("owner_profile_photo_url"),
        "fleetVehicleVin": row["fleet_vehicle_vin"],
        "lat": float(lat) if lat is not None else None,
        "lng": float(lng) if lng is not None else None,
        "cityZone": row["city_zone"],
        "geohash": row["geohash"],
        "pickupAddress": pickup_address,
        "locationSourceType": row.get("location_source_type"),
        "branchId": row.get("branch_id"),
        "parkingSpotId": row.get("parking_spot_id"),
        "createdByUserId": row.get("created_by_user_id"),
        "createdAt": row["created_at"].isoformat(),
        "updatedAt": row["updated_at"].isoformat(),
        "averageRating": average_rating,
        "reviewCount": review_count,
        "instantBook": bool(row.get("instant_book", True)),
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
