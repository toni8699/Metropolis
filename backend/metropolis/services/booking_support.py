from __future__ import annotations

from datetime import datetime, timezone


def resolve_post_payment_status(source_type: str, instant_book: bool) -> str:
    if source_type == "OWNER" and not instant_book:
        return "PENDING_APPROVAL"
    return "CONFIRMED"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def booking_day_count(start_at: datetime, end_at: datetime) -> int:
    return max(1, (end_at.date() - start_at.date()).days)


def build_price_snapshot(price_per_day: float, start_at: datetime, end_at: datetime) -> dict:
    day_count = booking_day_count(start_at, end_at)
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


def trip_has_started(start_at: datetime, now: datetime | None = None) -> bool:
    now = now or utcnow()
    start = start_at if start_at.tzinfo else start_at.replace(tzinfo=timezone.utc)
    return now >= start


def trip_is_active_window(
    start_at: datetime, end_at: datetime, now: datetime | None = None
) -> bool:
    now = now or utcnow()
    start = start_at if start_at.tzinfo else start_at.replace(tzinfo=timezone.utc)
    end = end_at if end_at.tzinfo else end_at.replace(tzinfo=timezone.utc)
    return start <= now <= end


def renter_can_cancel(status: str, start_at: datetime, now: datetime | None = None) -> bool:
    if status == "PENDING":
        return True
    if status not in {"PENDING_APPROVAL", "CONFIRMED"}:
        return False
    return not trip_has_started(start_at, now)


def host_can_cancel(status: str, start_at: datetime, now: datetime | None = None) -> bool:
    """Host may cancel before trip start (reject handles PENDING_APPROVAL via separate path)."""
    if status == "PENDING":
        return True
    if status not in {"CONFIRMED"}:
        return False
    return not trip_has_started(start_at, now)


def renter_can_confirm_pickup(status: str, start_at: datetime, end_at: datetime) -> bool:
    return status == "CONFIRMED" and trip_is_active_window(start_at, end_at)


def renter_can_complete_trip(status: str) -> bool:
    return status == "IN_PROGRESS"


def auto_complete_expired_bookings(
    cur, *, renter_user_id: int | None = None, booking_id: int | None = None
) -> list[int]:
    from psycopg2.extras import Json

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
    completed = cur.fetchall()
    completed_ids: list[int] = []
    for row in completed:
        bid = row["booking_id"] if isinstance(row, dict) else row[0]
        completed_ids.append(int(bid))
        cur.execute(
            """
            INSERT INTO trip_event (booking_id, event_type, actor_user_id, metadata_json)
            VALUES (%s, 'TRIP_COMPLETED', NULL, %s::jsonb)
            """,
            (bid, Json({"auto": True})),
        )
    return completed_ids


def fetch_trip_events(cur, booking_id: int) -> list[dict]:
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
