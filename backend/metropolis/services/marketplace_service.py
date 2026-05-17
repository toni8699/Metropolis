from __future__ import annotations

from datetime import datetime
import hashlib

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
        "description": row["description"],
        "rules": row["rules"],
        "pickupNotesTemplate": row["pickup_notes_template"],
        "pricePerDay": float(row["price_per_day"]),
        "photos": row["photos_json"] or [],
        "active": row["active"],
        "ownerUserId": row["owner_user_id"],
        "ownerName": row["owner_name"],
        "fleetVehicleVin": row["fleet_vehicle_vin"],
        "lat": float(row["lat"]) if row["lat"] is not None else None,
        "lng": float(row["lng"]) if row["lng"] is not None else None,
        "cityZone": row["city_zone"],
        "geohash": row["geohash"],
        "createdAt": row["created_at"].isoformat(),
        "updatedAt": row["updated_at"].isoformat(),
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


class MarketplaceService:
    def create_owner_listing(self, owner_user_id: int, payload: dict) -> dict:
        brand = payload.get("brand")
        make = payload.get("make")
        model = payload.get("model")
        year = payload.get("year")
        title = payload.get("title")
        if not title:
            parts = [p for p in [brand, make, model, str(year) if year else None] if p]
            title = " ".join(parts) if parts else "Owner listed car"
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO vehicle_listing
                    (owner_user_id, source_type, title, brand, make, model, year,
                     description, rules, pickup_notes_template,
                     price_per_day, photos_json, active)
                    VALUES (%s, 'OWNER', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, TRUE)
                    RETURNING listing_id
                    """,
                    (
                        owner_user_id,
                        title,
                        brand,
                        make,
                        model,
                        year,
                        payload.get("description"),
                        payload.get("rules"),
                        payload.get("pickupNotesTemplate"),
                        payload["pricePerDay"],
                        Json(payload.get("photos", [])),
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
                        payload["lat"],
                        payload["lng"],
                        _simple_geohash(payload["lat"], payload["lng"]),
                        payload["cityZone"],
                    ),
                )
                conn.commit()

        return self.get_listing(listing_id)

    def get_listing(self, listing_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT l.*, loc.lat, loc.lng, loc.geohash, loc.city_zone,
                           u.full_name AS owner_name
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

    def owner_listings(self, owner_user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT l.*, loc.lat, loc.lng, loc.geohash, loc.city_zone,
                           u.full_name AS owner_name
                    FROM vehicle_listing l
                    LEFT JOIN listing_location loc ON loc.listing_id = l.listing_id
                    LEFT JOIN app_user u ON u.user_id = l.owner_user_id
                    WHERE l.owner_user_id = %s
                    ORDER BY l.created_at DESC
                    """,
                    (owner_user_id,),
                )
                rows = cur.fetchall()
        return {"status": "success", "listings": [_to_listing_row(row) for row in rows]}

    def search_listings(self, query: dict) -> dict:
        clauses = ["l.active = TRUE"]
        params = []

        if query.get("cityZone"):
            clauses.append("loc.city_zone = %s")
            params.append(query["cityZone"])

        if query.get("bbox"):
            min_lng, min_lat, max_lng, max_lat = [float(x) for x in query["bbox"].split(",")]
            clauses.extend(
                [
                    "loc.lng BETWEEN %s AND %s",
                    "loc.lat BETWEEN %s AND %s",
                ]
            )
            params.extend([min_lng, max_lng, min_lat, max_lat])

        where_sql = " AND ".join(clauses)
        sql = f"""
            SELECT l.*, loc.lat, loc.lng, loc.geohash, loc.city_zone, u.full_name AS owner_name
            FROM vehicle_listing l
            LEFT JOIN listing_location loc ON loc.listing_id = l.listing_id
            LEFT JOIN app_user u ON u.user_id = l.owner_user_id
            WHERE {where_sql}
            ORDER BY l.updated_at DESC
            LIMIT 500
        """

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, tuple(params))
                rows = cur.fetchall()

        return {"status": "success", "listings": [_to_listing_row(row) for row in rows]}

    def update_listing(self, owner_user_id: int, listing_id: int, payload: dict) -> dict:
        fields = []
        params = []
        mapping = {
            "title": "title",
            "brand": "brand",
            "make": "make",
            "model": "model",
            "year": "year",
            "description": "description",
            "rules": "rules",
            "pickupNotesTemplate": "pickup_notes_template",
            "pricePerDay": "price_per_day",
            "photos": "photos_json",
            "active": "active",
        }
        for key, column in mapping.items():
            if key in payload:
                fields.append(f"{column} = %s")
                params.append(Json(payload[key]) if key == "photos" else payload[key])

        if not fields:
            return {"status": "validation_error", "message": "No fields to update."}

        fields.append("updated_at = %s")
        params.append(datetime.utcnow())
        params.extend([listing_id, owner_user_id])

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    UPDATE vehicle_listing
                    SET {", ".join(fields)}
                    WHERE listing_id = %s AND owner_user_id = %s
                    RETURNING listing_id
                    """,
                    tuple(params),
                )
                row = cur.fetchone()
                if not row:
                    return {"status": "not_found", "message": "Listing not found for owner."}
                conn.commit()

        return self.get_listing(listing_id)

    def upsert_location(self, owner_user_id: int, listing_id: int, payload: dict) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT listing_id FROM vehicle_listing WHERE listing_id = %s AND owner_user_id = %s",
                    (listing_id, owner_user_id),
                )
                if not cur.fetchone():
                    return {"status": "not_found", "message": "Listing not found for owner."}

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

    def add_availability(self, owner_user_id: int, listing_id: int, payload: dict) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT listing_id FROM vehicle_listing WHERE listing_id = %s AND owner_user_id = %s",
                    (listing_id, owner_user_id),
                )
                if not cur.fetchone():
                    return {"status": "not_found", "message": "Listing not found for owner."}

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
        return self.get_booking(booking_id, renter_user_id, "RENTER")

    def get_booking(self, booking_id: int, requester_user_id: int, requester_role: str) -> dict:
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

                is_admin = requester_role.upper() == "ADMIN"
                is_renter = row["renter_user_id"] == requester_user_id
                is_owner = row["owner_user_id"] == requester_user_id
                if not (is_admin or is_renter or is_owner):
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
        actor_role: str,
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

                is_admin = actor_role.upper() == "ADMIN"
                is_owner = row["owner_user_id"] == actor_user_id
                is_renter = row["renter_user_id"] == actor_user_id
                if not (is_admin or is_owner or is_renter):
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

        return self.get_booking(booking_id, actor_user_id, actor_role)

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
                        (source_type, fleet_vehicle_vin, title, brand, make, model, year,
                         description, rules, pickup_notes_template,
                         price_per_day, photos_json, active)
                        VALUES ('FLEET', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, TRUE)
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
