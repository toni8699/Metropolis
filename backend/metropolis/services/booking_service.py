from __future__ import annotations

from datetime import datetime, timezone

from psycopg2.extras import Json, RealDictCursor

from metropolis.db import get_connection
from metropolis.services.marketplace_common import (
    _BOOKING_BLOCKING_STATUSES,
    _BOOKING_HOLD_STATUSES,
    _BOOKING_NEEDS_REVIEW_SQL,
    _BOOKING_SELECT_SQL,
    _fetch_listing_images_map,
)


def _resolve_post_payment_status(source_type: str, instant_book: bool) -> str:
    if source_type == "OWNER" and not instant_book:
        return "PENDING_APPROVAL"
    return "CONFIRMED"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _booking_day_count(start_at: datetime, end_at: datetime) -> int:
    return max(1, (end_at.date() - start_at.date()).days)


def _build_price_snapshot(price_per_day: float, start_at: datetime, end_at: datetime) -> dict:
    day_count = _booking_day_count(start_at, end_at)
    price = float(price_per_day)
    subtotal = round(price * day_count, 2)
    cleaning_fee = 50.0
    service_fee = round(subtotal * 0.1, 2)
    security_deposit = 0.0
    total = round(subtotal + cleaning_fee + service_fee + security_deposit, 2)
    return {
        "pricePerDay": price,
        "dayCount": day_count,
        "subtotal": subtotal,
        "serviceFee": service_fee,
        "cleaningFee": cleaning_fee,
        "securityDeposit": security_deposit,
        "total": total,
        "currency": "CAD",
    }


def _build_price_breakdown(row: dict) -> dict:
    snapshot = row.get("price_snapshot_json") or {}
    if isinstance(snapshot, str):
        snapshot = {}
    start_at = row["start_at"]
    end_at = row["end_at"]
    fallback_price = float(row.get("listing_price_per_day") or 0)
    day_count = int(snapshot.get("dayCount") or _booking_day_count(start_at, end_at))
    price_per_day = float(snapshot.get("pricePerDay") or fallback_price)
    subtotal = float(snapshot.get("subtotal") or round(price_per_day * day_count, 2))
    cleaning_fee = float(snapshot.get("cleaningFee", 50))
    service_fee = float(snapshot.get("serviceFee") or round(subtotal * 0.1, 2))
    security_deposit = float(snapshot.get("securityDeposit", 0))
    total = float(
        snapshot.get("total") or round(subtotal + cleaning_fee + service_fee + security_deposit, 2)
    )
    return {
        "pricePerDay": price_per_day,
        "dayCount": day_count,
        "subtotal": subtotal,
        "serviceFee": service_fee,
        "cleaningFee": cleaning_fee,
        "securityDeposit": security_deposit,
        "total": total,
        "currency": snapshot.get("currency") or "CAD",
    }


def _build_host_earnings(pricing: dict) -> dict:
    subtotal = float(pricing.get("subtotal") or 0)
    cleaning_fee = float(pricing.get("cleaningFee") or 0)
    return {
        "pricePerDay": pricing.get("pricePerDay"),
        "dayCount": pricing.get("dayCount"),
        "subtotal": subtotal,
        "cleaningFee": cleaning_fee,
        "grossPayout": round(subtotal + cleaning_fee, 2),
        "currency": pricing.get("currency") or "CAD",
    }


def _host_is_verified(verification_status: str | None) -> bool:
    return str(verification_status or "").upper() == "VERIFIED"


def _listing_photo_from_row(row: dict) -> str | None:
    urls = row.get("listing_image_urls") or []
    if isinstance(urls, list) and urls:
        first = urls[0]
        return str(first) if first else None
    return None


def _trip_has_started(start_at: datetime, now: datetime | None = None) -> bool:
    now = now or _utcnow()
    start = start_at if start_at.tzinfo else start_at.replace(tzinfo=timezone.utc)
    return now >= start


def _trip_is_active_window(
    start_at: datetime, end_at: datetime, now: datetime | None = None
) -> bool:
    now = now or _utcnow()
    start = start_at if start_at.tzinfo else start_at.replace(tzinfo=timezone.utc)
    end = end_at if end_at.tzinfo else end_at.replace(tzinfo=timezone.utc)
    return start <= now <= end


def _renter_can_cancel(status: str, start_at: datetime, now: datetime | None = None) -> bool:
    if status not in {"PENDING_APPROVAL", "CONFIRMED"}:
        return False
    return not _trip_has_started(start_at, now)


def _renter_can_confirm_pickup(status: str, start_at: datetime, end_at: datetime) -> bool:
    return status == "CONFIRMED" and _trip_is_active_window(start_at, end_at)


def _renter_can_complete_trip(status: str) -> bool:
    return status == "IN_PROGRESS"


def _auto_complete_expired_bookings(
    cur, *, renter_user_id: int | None = None, booking_id: int | None = None
) -> None:
    filters = [
        "status IN ('CONFIRMED'::booking_status, 'IN_PROGRESS'::booking_status)",
        "end_at < NOW()",
    ]
    params: list = []
    if renter_user_id is not None:
        filters.append("renter_user_id = %s")
        params.append(renter_user_id)
    if booking_id is not None:
        filters.append("booking_id = %s")
        params.append(booking_id)
    where_sql = " AND ".join(filters)
    cur.execute(
        f"""
        UPDATE booking
        SET status = 'COMPLETED'::booking_status, updated_at = NOW()
        WHERE {where_sql}
        RETURNING booking_id
        """,
        tuple(params),
    )
    for row in cur.fetchall():
        cur.execute(
            """
            INSERT INTO trip_event (booking_id, event_type, actor_user_id, metadata_json)
            VALUES (%s, 'TRIP_COMPLETED', NULL, %s::jsonb)
            """,
            (row["booking_id"], Json({"auto": True})),
        )


def _fetch_trip_events(cur, booking_id: int) -> list[dict]:
    cur.execute(
        """
        SELECT event_id, event_type, actor_user_id, event_at, metadata_json
        FROM trip_event
        WHERE booking_id = %s
        ORDER BY event_at ASC
        """,
        (booking_id,),
    )
    return [
        {
            "eventId": row["event_id"],
            "eventType": row["event_type"],
            "actorUserId": row["actor_user_id"],
            "eventAt": row["event_at"].isoformat(),
            "metadata": row["metadata_json"] or {},
        }
        for row in cur.fetchall()
    ]


def _to_booking_row(row: dict, *, include_detail: bool = False) -> dict:
    payload = {
        "bookingId": row["booking_id"],
        "listingId": row["listing_id"],
        "listingTitle": row["listing_title"],
        "sourceType": row["source_type"],
        "ownerUserId": row["owner_user_id"],
        "renterUserId": row["renter_user_id"],
        "renterEmail": row.get("renter_email"),
        "cityZone": row.get("city_zone"),
        "startAt": row["start_at"].isoformat(),
        "endAt": row["end_at"].isoformat(),
        "status": row["status"],
        "priceSnapshot": row["price_snapshot_json"],
        "createdAt": row["created_at"].isoformat(),
        "updatedAt": row["updated_at"].isoformat(),
        "needsReview": bool(row.get("needs_review")),
    }
    if not include_detail:
        return payload

    lat = row.get("lat")
    lng = row.get("lng")
    payload.update(
        {
            "listingPhoto": _listing_photo_from_row(row),
            "pickupNotes": row.get("pickup_notes_template"),
            "listingLocation": {
                "lat": float(lat) if lat is not None else None,
                "lng": float(lng) if lng is not None else None,
                "cityZone": row.get("city_zone"),
                "address": row.get("raw_address"),
                "geohash": row.get("geohash"),
            },
            "host": {
                "userId": row.get("host_user_id") or row.get("owner_user_id"),
                "name": row.get("host_name") or row.get("owner_name"),
                "email": row.get("host_email"),
                "verified": _host_is_verified(row.get("host_verification_status")),
            },
            "pricing": _build_price_breakdown(row),
            "tripEvents": row.get("trip_events") or [],
            "canCancel": bool(row.get("can_cancel")),
            "canConfirmPickup": bool(row.get("can_confirm_pickup")),
            "canCompleteTrip": bool(row.get("can_complete_trip")),
        }
    )
    return payload


class BookingService:
    def _has_active_booking_conflict(
        self,
        cur,
        *,
        listing_id: int,
        source_type: str,
        fleet_vehicle_vin: str | None,
        start_at,
        end_at,
        statuses: tuple[str, ...] = _BOOKING_HOLD_STATUSES,
        exclude_booking_id: int | None = None,
    ) -> bool:
        status_sql = ", ".join(["%s::booking_status"] * len(statuses))
        cur.execute(
            f"""
            SELECT 1
            FROM booking b
            JOIN vehicle_listing vl ON vl.listing_id = b.listing_id
            WHERE b.status IN ({status_sql})
              AND b.start_at < %s
              AND b.end_at > %s
              AND (%s IS NULL OR b.booking_id <> %s)
              AND (
                b.listing_id = %s
                OR (
                  %s = 'FLEET'
                  AND %s IS NOT NULL
                  AND vl.fleet_vehicle_vin = %s
                )
              )
            LIMIT 1
            """,
            (
                *statuses,
                end_at,
                start_at,
                exclude_booking_id,
                exclude_booking_id,
                listing_id,
                source_type,
                fleet_vehicle_vin,
                fleet_vehicle_vin,
            ),
        )
        return cur.fetchone() is not None

    def create_booking(self, renter_user_id: int, payload: dict) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT listing_id, title, owner_user_id, source_type, fleet_vehicle_vin,
                           price_per_day, active, instant_book
                    FROM vehicle_listing
                    WHERE listing_id = %s
                    FOR UPDATE
                    """,
                    (payload["listingId"],),
                )
                listing = cur.fetchone()
                if not listing or not listing["active"]:
                    return {"status": "not_found", "message": "Listing not found or inactive."}
                initial_status = "PENDING"
                if self._has_active_booking_conflict(
                    cur,
                    listing_id=listing["listing_id"],
                    source_type=listing["source_type"],
                    fleet_vehicle_vin=listing.get("fleet_vehicle_vin"),
                    start_at=payload["startAt"],
                    end_at=payload["endAt"],
                ):
                    return {
                        "status": "validation_error",
                        "message": "Listing unavailable for selected window.",
                    }
                cur.execute(
                    """
                    INSERT INTO booking (
                        listing_id, renter_user_id, start_at, end_at, status,
                        price_snapshot_json
                    )
                    VALUES (%s, %s, %s, %s, %s::booking_status, %s::jsonb)
                    RETURNING booking_id
                    """,
                    (
                        payload["listingId"],
                        renter_user_id,
                        payload["startAt"],
                        payload["endAt"],
                        initial_status,
                        Json(
                            _build_price_snapshot(
                                float(listing["price_per_day"]),
                                payload["startAt"],
                                payload["endAt"],
                            )
                        ),
                    ),
                )
                booking_id = cur.fetchone()["booking_id"]
                cur.execute(
                    """
                    INSERT INTO trip_event (booking_id, event_type, actor_user_id, metadata_json)
                    VALUES (%s, 'BOOKING_CREATED', %s, %s::jsonb)
                    """,
                    (
                        booking_id,
                        renter_user_id,
                        Json(
                            {
                                "source": listing["source_type"],
                                "instantBook": bool(listing.get("instant_book", True)),
                                "status": initial_status,
                            }
                        ),
                    ),
                )
                conn.commit()
        return self.get_booking(booking_id, renter_user_id, False)

    def approve_booking(self, booking_id: int, owner_user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                      b.booking_id,
                      b.listing_id,
                      b.start_at,
                      b.end_at,
                      b.status,
                      l.owner_user_id,
                      l.source_type,
                      l.fleet_vehicle_vin
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
                if row["owner_user_id"] != owner_user_id:
                    return {
                        "status": "forbidden",
                        "message": "Only the listing owner can approve this booking.",
                    }
                if row["status"] != "PENDING_APPROVAL":
                    return {
                        "status": "validation_error",
                        "message": "Only pending approval bookings can be approved.",
                    }
                if self._has_active_booking_conflict(
                    cur,
                    listing_id=row["listing_id"],
                    source_type=row["source_type"],
                    fleet_vehicle_vin=row.get("fleet_vehicle_vin"),
                    start_at=row["start_at"],
                    end_at=row["end_at"],
                    statuses=_BOOKING_BLOCKING_STATUSES,
                    exclude_booking_id=booking_id,
                ):
                    return {
                        "status": "validation_error",
                        "message": (
                            "Cannot approve: another confirmed booking overlaps these dates."
                        ),
                    }
                cur.execute(
                    """
                    UPDATE booking
                    SET status = 'CONFIRMED'::booking_status, updated_at = NOW()
                    WHERE booking_id = %s
                    """,
                    (booking_id,),
                )
                cur.execute(
                    """
                    INSERT INTO trip_event (booking_id, event_type, actor_user_id, metadata_json)
                    VALUES (%s, 'BOOKING_APPROVED', %s, %s::jsonb)
                    """,
                    (
                        booking_id,
                        owner_user_id,
                        Json({"from": row["status"], "to": "CONFIRMED"}),
                    ),
                )
                conn.commit()
        return self.get_booking(booking_id, owner_user_id, False)

    def reject_booking(self, booking_id: int, owner_user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT b.booking_id, b.status, l.owner_user_id
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
                if row["owner_user_id"] != owner_user_id:
                    return {
                        "status": "forbidden",
                        "message": "Only the listing owner can reject this booking.",
                    }
                if row["status"] != "PENDING_APPROVAL":
                    return {
                        "status": "validation_error",
                        "message": "Only pending approval bookings can be rejected.",
                    }
                cur.execute(
                    """
                    UPDATE booking
                    SET status = 'CANCELLED'::booking_status, updated_at = NOW()
                    WHERE booking_id = %s
                    """,
                    (booking_id,),
                )
                cur.execute(
                    """
                    INSERT INTO trip_event (booking_id, event_type, actor_user_id, metadata_json)
                    VALUES (%s, 'BOOKING_REJECTED', %s, %s::jsonb)
                    """,
                    (
                        booking_id,
                        owner_user_id,
                        Json({"from": row["status"], "to": "CANCELLED"}),
                    ),
                )
                conn.commit()
        return self.get_booking(booking_id, owner_user_id, False)

    def get_booking(
        self, booking_id: int, requester_user_id: int, requester_is_admin: bool
    ) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                _auto_complete_expired_bookings(cur, booking_id=booking_id)
                row = self._fetch_booking_detail_row(cur, booking_id)
                if not row:
                    return {"status": "not_found", "message": "Booking not found."}
                is_renter = row["renter_user_id"] == requester_user_id
                is_owner = row["owner_user_id"] == requester_user_id
                if not (requester_is_admin or is_renter or is_owner):
                    return {"status": "forbidden", "message": "No access to this booking."}
                images_by_listing = _fetch_listing_images_map(cur, [row["listing_id"]])
                row["listing_image_urls"] = images_by_listing.get(row["listing_id"], [])
                trip_events = _fetch_trip_events(cur, booking_id)
                now = _utcnow()
                row["trip_events"] = trip_events
                row["can_cancel"] = is_renter and _renter_can_cancel(
                    row["status"], row["start_at"], now
                )
                row["can_confirm_pickup"] = is_renter and _renter_can_confirm_pickup(
                    row["status"], row["start_at"], row["end_at"]
                )
                row["can_complete_trip"] = is_renter and _renter_can_complete_trip(row["status"])
                conn.commit()
        booking = _to_booking_row(row, include_detail=True)
        if is_renter:
            booking["userRole"] = "renter"
        elif is_owner:
            booking["userRole"] = "host"
        elif requester_is_admin:
            booking["userRole"] = "admin"
        booking["renter"] = {
            "userId": row["renter_user_id"],
            "name": row.get("renter_name"),
            "email": row.get("renter_email"),
        }
        if is_owner:
            status = row["status"]
            booking["canApprove"] = status == "PENDING_APPROVAL"
            booking["canReject"] = status == "PENDING_APPROVAL"
            if booking.get("pricing"):
                booking["earnings"] = _build_host_earnings(booking["pricing"])
        return {
            "status": "success",
            "booking": booking,
        }

    def cancel_booking(self, booking_id: int, renter_user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT booking_id, renter_user_id, status, start_at
                    FROM booking
                    WHERE booking_id = %s
                    FOR UPDATE
                    """,
                    (booking_id,),
                )
                row = cur.fetchone()
                if not row:
                    return {"status": "not_found", "message": "Booking not found."}
                if row["renter_user_id"] != renter_user_id:
                    return {
                        "status": "forbidden",
                        "message": "Only the renter can cancel this booking.",
                    }
                if row["status"] not in {"PENDING", "PENDING_APPROVAL", "CONFIRMED"}:
                    return {
                        "status": "validation_error",
                        "message": "This booking cannot be cancelled.",
                    }
                if _trip_has_started(row["start_at"]):
                    return {
                        "status": "validation_error",
                        "message": "Cannot cancel after the trip has started.",
                    }
                cur.execute(
                    """
                    UPDATE booking
                    SET status = 'CANCELLED'::booking_status, updated_at = NOW()
                    WHERE booking_id = %s
                    """,
                    (booking_id,),
                )
                cur.execute(
                    """
                    INSERT INTO trip_event (booking_id, event_type, actor_user_id, metadata_json)
                    VALUES (%s, 'BOOKING_CANCELLED', %s, %s::jsonb)
                    """,
                    (
                        booking_id,
                        renter_user_id,
                        Json({"from": row["status"], "to": "CANCELLED"}),
                    ),
                )
                conn.commit()
        return self.get_booking(booking_id, renter_user_id, False)

    def _fetch_booking_detail_row(self, cur, booking_id: int) -> dict | None:
        cur.execute(
            f"""
            SELECT
              b.*,
              l.title AS listing_title,
              l.owner_user_id,
              l.source_type,
              l.price_per_day AS listing_price_per_day,
              l.pickup_notes_template,
              loc.lat,
              loc.lng,
              loc.city_zone,
              loc.raw_address,
              loc.geohash,
              host.user_id AS host_user_id,
              host.full_name AS host_name,
              host.email AS host_email,
              op.verification_status AS host_verification_status,
              u.email AS renter_email,
              u.full_name AS renter_name,
              {_BOOKING_NEEDS_REVIEW_SQL} AS needs_review
            FROM booking b
            JOIN vehicle_listing l ON l.listing_id = b.listing_id
            LEFT JOIN listing_location loc ON loc.listing_id = l.listing_id
            LEFT JOIN app_user host ON host.user_id = l.owner_user_id
            LEFT JOIN owner_profile op ON op.user_id = l.owner_user_id
            LEFT JOIN app_user u ON u.user_id = b.renter_user_id
            WHERE b.booking_id = %s
            """,
            (booking_id,),
        )
        return cur.fetchone()

    def list_renter_bookings(self, renter_user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                _auto_complete_expired_bookings(cur, renter_user_id=renter_user_id)
                conn.commit()
                cur.execute(
                    f"""
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
                        u.email AS renter_email,
                        {_BOOKING_NEEDS_REVIEW_SQL} AS needs_review
                    FROM booking b
                    JOIN vehicle_listing l ON l.listing_id = b.listing_id
                    LEFT JOIN listing_location loc ON loc.listing_id = l.listing_id
                    LEFT JOIN app_user u ON u.user_id = b.renter_user_id
                    WHERE b.renter_user_id = %s
                    ORDER BY b.end_at DESC
                    LIMIT 200
                    """,
                    (renter_user_id,),
                )
                rows = cur.fetchall()
        return {
            "status": "success",
            "bookings": [_to_booking_row(row) for row in rows],
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
            return {
                "status": "validation_error",
                "message": "Unsupported booking status transition.",
            }
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT b.booking_id, b.status, b.start_at, b.end_at,
                           b.renter_user_id, l.owner_user_id
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
                if status == "IN_PROGRESS":
                    if row["status"] != "CONFIRMED":
                        return {
                            "status": "validation_error",
                            "message": "Only confirmed bookings can be picked up.",
                        }
                    if is_renter and not _trip_is_active_window(row["start_at"], row["end_at"]):
                        return {
                            "status": "validation_error",
                            "message": "Pickup is only available during the trip window.",
                        }
                elif status == "COMPLETED":
                    if row["status"] != "IN_PROGRESS":
                        return {
                            "status": "validation_error",
                            "message": "Only in-progress trips can be completed.",
                        }
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
                    (
                        booking_id,
                        f"STATUS_{status}",
                        actor_user_id,
                        Json({"from": row["status"], "to": status}),
                    ),
                )
                conn.commit()
        return self.get_booking(booking_id, actor_user_id, actor_is_admin)

    def patch_booking(
        self,
        booking_id: int,
        actor_user_id: int,
        actor_is_admin: bool,
        payload: dict,
    ) -> dict:
        status = (payload.get("status") or "").strip().upper()

        if not status:
            return {
                "status": "validation_error",
                "message": "Provide status to update booking.",
            }

        if status == "CONFIRMED":
            return self.approve_booking(booking_id, actor_user_id)

        if status == "CANCELLED":
            with get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT b.status, b.renter_user_id, l.owner_user_id
                        FROM booking b
                        JOIN vehicle_listing l ON l.listing_id = b.listing_id
                        WHERE b.booking_id = %s
                        """,
                        (booking_id,),
                    )
                    row = cur.fetchone()
            if not row:
                return {"status": "not_found", "message": "Booking not found."}
            if row["owner_user_id"] == actor_user_id and row["status"] == "PENDING_APPROVAL":
                return self.reject_booking(booking_id, actor_user_id)
            if row["renter_user_id"] == actor_user_id:
                return self.cancel_booking(booking_id, actor_user_id)
            return {
                "status": "forbidden",
                "message": "You cannot cancel this booking.",
            }

        if status in {"IN_PROGRESS", "COMPLETED"}:
            return self.transition_booking_status(
                booking_id,
                actor_user_id,
                actor_is_admin,
                status,
            )

        return {
            "status": "validation_error",
            "message": f"Unsupported booking status: {status}.",
        }

    def owner_bookings(self, owner_user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    {_BOOKING_SELECT_SQL}
                    WHERE l.owner_user_id = %s
                      AND l.source_type = 'OWNER'
                    ORDER BY b.created_at DESC
                    LIMIT 200
                    """,
                    (owner_user_id,),
                )
                rows = cur.fetchall()
        return {"status": "success", "bookings": [_to_booking_row(row) for row in rows]}


booking_service = BookingService()
