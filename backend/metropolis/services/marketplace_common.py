from __future__ import annotations

import hashlib
from datetime import datetime

LISTING_SELECT_SQL = """
    SELECT l.*,
           loc.lat,
           loc.lng,
           loc.geohash,
           loc.city_zone,
           loc.pickup_address,
           u.full_name AS owner_name,
           u.profile_photo_url AS owner_profile_photo_url
    FROM vehicle_listing l
    LEFT JOIN listing_location loc ON loc.listing_id = l.listing_id
    LEFT JOIN app_user u ON u.user_id = l.owner_user_id
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
        l.title AS listing_title,
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
    return [
        _to_listing_row(
            row,
            images_by_listing.get(row["listing_id"], []),
            ratings_by_listing.get(row["listing_id"]),
        )
        for row in rows
    ]


def _to_listing_row(
    row: dict,
    image_urls: list[str] | None = None,
    ratings: dict | None = None,
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

    return {
        "listingId": row["listing_id"],
        "vehicleId": row.get("vehicle_id"),
        "sourceType": row["source_type"],
        "title": row["title"],
        "make": row.get("make"),
        "model": row.get("model"),
        "year": row.get("year"),
        "mileage": row.get("mileage"),
        "vehicleClassId": None,
        "description": row.get("description"),
        "guidelines": guidelines,
        "transmission": row.get("transmission"),
        "fuelType": row.get("fuel_type"),
        "seats": row.get("seats"),
        "doors": row.get("doors"),
        "features": row.get("features") or [],
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
