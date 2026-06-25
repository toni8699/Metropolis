from __future__ import annotations

from psycopg2.extras import Json, RealDictCursor

from vroom.core.db import get_connection
from vroom.services.booking_rows import build_host_earnings, to_booking_row
from vroom.services.booking_support import (
    auto_complete_expired_bookings,
    build_price_snapshot,
    fetch_trip_events,
    host_can_cancel,
    renter_can_cancel,
    renter_can_complete_trip,
    renter_can_confirm_pickup,
    trip_has_started,
    trip_is_active_window,
    utcnow,
)
from vroom.services.marketplace_common import (
    _BOOKING_BLOCKING_STATUSES,
    _BOOKING_HOLD_STATUSES,
    _BOOKING_NEEDS_REVIEW_SQL,
    _BOOKING_SELECT_SQL,
    fetch_listing_images_map,
)


class BookingService:
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
              loc.pickup_address,
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

    def get_booking(
        self, booking_id: int, requester_user_id: int, requester_is_admin: bool
    ) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                row = self._fetch_booking_detail_row(cur, booking_id)
                if not row:
                    return {"status": "not_found", "message": "Booking not found."}
                is_renter = row["renter_user_id"] == requester_user_id
                is_owner = row["owner_user_id"] == requester_user_id
                if not (requester_is_admin or is_renter or is_owner):
                    return {"status": "forbidden", "message": "No access to this booking."}
                images_by_listing = fetch_listing_images_map(cur, [row["listing_id"]])
                row["listing_image_urls"] = images_by_listing.get(row["listing_id"], [])
                trip_events = fetch_trip_events(cur, booking_id)
                now = utcnow()
                row["trip_events"] = trip_events
                row["can_cancel"] = is_renter and renter_can_cancel(
                    row["status"], row["start_at"], now
                )
                if is_owner and not row["can_cancel"]:
                    row["can_cancel"] = host_can_cancel(row["status"], row["start_at"], now)
                row["can_confirm_pickup"] = is_renter and renter_can_confirm_pickup(
                    row["status"], row["start_at"], row["end_at"]
                )
                row["can_complete_trip"] = is_renter and renter_can_complete_trip(row["status"])
                from vroom.services.trip_inspection_service import trip_inspection_service

                row["has_inspection_photos"] = (
                    trip_inspection_service.booking_has_inspection_photos(cur, booking_id)
                )
                row["can_upload_check_in"] = trip_inspection_service.renter_can_upload_phase(
                    {**row, "is_renter": is_renter}, "CHECK_IN"
                )
                row["can_upload_check_out"] = trip_inspection_service.renter_can_upload_phase(
                    {**row, "is_renter": is_renter}, "CHECK_OUT"
                )
        booking = to_booking_row(row, include_detail=True)
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
                booking["earnings"] = build_host_earnings(booking["pricing"])
        return {
            "status": "success",
            "booking": booking,
        }

    def list_renter_bookings(self, renter_user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
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
                    ORDER BY b.created_at DESC, b.booking_id DESC
                    LIMIT 200
                    """,
                    (renter_user_id,),
                )
                rows = cur.fetchall()
        now = utcnow()
        for row in rows:
            row["can_cancel"] = renter_can_cancel(row["status"], row["start_at"], now)
        return {
            "status": "success",
            "bookings": [to_booking_row(row) for row in rows],
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
        now = utcnow()
        for row in rows:
            row["can_cancel"] = host_can_cancel(row["status"], row["start_at"], now)
        return {"status": "success", "bookings": [to_booking_row(row) for row in rows]}

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
                            build_price_snapshot(
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
        from vroom.services.booking_notifications import notify_booking_approved

        notify_booking_approved(booking_id)
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
        from vroom.services.booking_notifications import notify_booking_rejected

        notify_booking_rejected(booking_id)
        return self.get_booking(booking_id, owner_user_id, False)

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
                if row["status"] != "PENDING" and trip_has_started(row["start_at"]):
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
        from vroom.services.booking_notifications import notify_booking_cancelled

        notify_booking_cancelled(booking_id)
        return self.get_booking(booking_id, renter_user_id, False)

    def host_cancel_booking(self, booking_id: int, owner_user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT b.booking_id, b.status, b.start_at, l.owner_user_id
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
                        "message": "Only the listing owner can cancel this booking.",
                    }
                if not host_can_cancel(row["status"], row["start_at"]):
                    return {
                        "status": "validation_error",
                        "message": "This booking cannot be cancelled.",
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
                        owner_user_id,
                        Json({"from": row["status"], "to": "CANCELLED", "by": "host"}),
                    ),
                )
                conn.commit()
        from vroom.services.booking_notifications import notify_booking_cancelled

        notify_booking_cancelled(booking_id)
        return self.get_booking(booking_id, owner_user_id, False)

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
                    if is_renter and not trip_is_active_window(row["start_at"], row["end_at"]):
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
                    SET status = %s::booking_status,
                        updated_at = NOW(),
                        completed_at = CASE
                          WHEN %s = 'COMPLETED' THEN COALESCE(completed_at, NOW())
                          ELSE completed_at
                        END
                    WHERE booking_id = %s
                    """,
                    (status, status, booking_id),
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
        if status == "COMPLETED":
            from vroom.services.booking_notifications import notify_trip_completed

            notify_trip_completed(booking_id)
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
                        SELECT b.status, b.start_at, b.renter_user_id, l.owner_user_id
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
            if row["owner_user_id"] == actor_user_id and host_can_cancel(
                row["status"], row["start_at"]
            ):
                return self.host_cancel_booking(booking_id, actor_user_id)
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

    def sweep_expired_bookings(self) -> dict:
        """Mark every past-due CONFIRMED/IN_PROGRESS trip COMPLETED.

        Called by the in-process booking sweep greenlet (see booking_sweep.py), not
        from read endpoints. ponytail: cadence-bound — status may lag until the next
        sweep; use BOOKING_SWEEP_INTERVAL_SEC to tune. Advisory lock skips duplicate
        work when multiple Gunicorn workers are ever enabled.
        """
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT pg_try_advisory_lock(%s) AS acquired", (421_001,))
                if not cur.fetchone()["acquired"]:
                    return {"status": "success", "completed": 0}
                completed_ids: list[int] = []
                try:
                    completed_ids = auto_complete_expired_bookings(cur)
                    conn.commit()
                finally:
                    cur.execute("SELECT pg_advisory_unlock(%s)", (421_001,))
        for booking_id in completed_ids:
            from vroom.services.booking_notifications import notify_trip_completed

            notify_trip_completed(booking_id)
        return {"status": "success", "completed": len(completed_ids)}

    def sweep_trip_reminders(self) -> dict:
        """Email renters ~24h before CONFIRMED trips start. Deduped via trip_event."""
        from psycopg2.extras import Json

        from vroom.services import mail_service

        sent = 0
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT b.booking_id
                    FROM booking b
                    WHERE b.status = 'CONFIRMED'::booking_status
                      AND b.start_at >= NOW() + INTERVAL '23 hours'
                      AND b.start_at <= NOW() + INTERVAL '25 hours'
                      AND NOT EXISTS (
                        SELECT 1 FROM trip_event te
                        WHERE te.booking_id = b.booking_id
                          AND te.event_type = 'EMAIL_SENT'
                          AND te.metadata_json->>'emailType' = 'TRIP_REMINDER'
                      )
                    LIMIT 100
                    """
                )
                rows = cur.fetchall()
                for row in rows:
                    booking_id = row["booking_id"]
                    try:
                        if mail_service.send_trip_reminder(booking_id):
                            cur.execute(
                                """
                                INSERT INTO trip_event (booking_id, event_type, metadata_json)
                                VALUES (%s, 'EMAIL_SENT', %s::jsonb)
                                """,
                                (booking_id, Json({"emailType": "TRIP_REMINDER"})),
                            )
                            sent += 1
                    except Exception:
                        pass
                conn.commit()
        return {"status": "success", "sent": sent}

    def sweep_stale_unpaid_bookings(self) -> dict:
        """Cancel unpaid PENDING bookings past trip start or older than 24h."""
        from psycopg2.extras import Json

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    UPDATE booking b
                    SET status = 'CANCELLED'::booking_status, updated_at = NOW()
                    WHERE b.status = 'PENDING'::booking_status
                      AND NOT EXISTS (
                        SELECT 1 FROM payment p
                        WHERE p.booking_id = b.booking_id
                          AND p.status = 'succeeded'
                      )
                      AND (
                        b.start_at <= NOW()
                        OR b.created_at < NOW() - INTERVAL '24 hours'
                      )
                    RETURNING booking_id
                    """
                )
                rows = cur.fetchall()
                for row in rows:
                    cur.execute(
                        """
                        INSERT INTO trip_event
                         (booking_id, event_type, actor_user_id, metadata_json)
                        VALUES (%s, 'BOOKING_CANCELLED', NULL, %s::jsonb)
                        """,
                        (
                            row["booking_id"],
                            Json({"from": "PENDING", "to": "CANCELLED", "auto": True}),
                        ),
                    )
                conn.commit()
        return {"status": "success", "cancelled": len(rows)}


booking_service = BookingService()
