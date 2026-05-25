from __future__ import annotations

from datetime import datetime, timedelta, timezone

from psycopg2.extras import RealDictCursor

from metropolis.db import get_connection

REVIEW_WINDOW_DAYS = 30


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _review_window_expired(end_at: datetime) -> bool:
    end_utc = _as_utc(end_at)
    return datetime.now(timezone.utc) > end_utc + timedelta(days=REVIEW_WINDOW_DAYS)


def _parse_optional_sub_rating(value, field_name: str) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be an integer from 1 to 5.") from None
    if parsed < 1 or parsed > 5:
        raise ValueError(f"{field_name} must be between 1 and 5.")
    return parsed


def _to_review_row(row: dict) -> dict:
    return {
        "reviewId": row["review_id"],
        "bookingId": row["booking_id"],
        "authorUserId": row["author_user_id"],
        "authorName": row.get("author_name"),
        "targetType": row["target_type"],
        "targetUserId": row.get("target_user_id"),
        "targetListingId": row.get("target_listing_id"),
        "rating": int(row["rating"]),
        "cleanliness": int(row["cleanliness"]) if row.get("cleanliness") is not None else None,
        "accuracy": int(row["accuracy"]) if row.get("accuracy") is not None else None,
        "communication": int(row["communication"]) if row.get("communication") is not None else None,
        "comment": row.get("comment"),
        "createdAt": row["created_at"].isoformat(),
    }


class ReviewService:
    def submit_review(
        self,
        booking_id: int,
        author_id: int,
        target_type: str,
        rating: int,
        comment: str | None,
        cleanliness: int | None = None,
        accuracy: int | None = None,
        communication: int | None = None,
    ) -> dict:
        normalized_type = str(target_type or "").upper()
        if normalized_type not in {"LISTING", "RENTER"}:
            return {
                "status": "validation_error",
                "message": "targetType must be LISTING or RENTER.",
            }

        try:
            rating_value = int(rating)
        except (TypeError, ValueError):
            return {"status": "validation_error", "message": "rating must be an integer from 1 to 5."}
        if rating_value < 1 or rating_value > 5:
            return {"status": "validation_error", "message": "rating must be between 1 and 5."}

        trimmed_comment = (comment or "").strip() or None

        try:
            cleanliness_value = _parse_optional_sub_rating(cleanliness, "cleanliness")
            accuracy_value = _parse_optional_sub_rating(accuracy, "accuracy")
            communication_value = _parse_optional_sub_rating(communication, "communication")
        except ValueError as exc:
            return {"status": "validation_error", "message": str(exc)}

        if normalized_type == "RENTER":
            if accuracy_value is not None:
                return {
                    "status": "validation_error",
                    "message": "accuracy is not applicable when reviewing a renter.",
                }
            accuracy_value = None

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                      b.booking_id,
                      b.status,
                      b.end_at,
                      b.renter_user_id,
                      b.listing_id,
                      l.owner_user_id,
                      l.created_by_user_id
                    FROM booking b
                    JOIN vehicle_listing l ON l.listing_id = b.listing_id
                    WHERE b.booking_id = %s
                    """,
                    (booking_id,),
                )
                booking = cur.fetchone()
                if not booking:
                    return {"status": "not_found", "message": "Booking not found."}
                if booking["status"] != "COMPLETED":
                    return {
                        "status": "validation_error",
                        "message": "Reviews are allowed only after the booking is COMPLETED.",
                    }
                if _review_window_expired(booking["end_at"]):
                    raise ValueError("The 30-day review window for this trip has expired.")

                is_renter = booking["renter_user_id"] == author_id
                is_host = author_id in {
                    booking["owner_user_id"],
                    booking.get("created_by_user_id"),
                }
                if normalized_type == "LISTING":
                    if not is_renter:
                        return {
                            "status": "forbidden",
                            "message": "Only the renter can review the listing.",
                        }
                    target_listing_id = booking["listing_id"]
                    target_user_id = booking["owner_user_id"]
                else:
                    if not is_host:
                        return {
                            "status": "forbidden",
                            "message": "Only the host can review the renter.",
                        }
                    target_listing_id = booking["listing_id"]
                    target_user_id = booking["renter_user_id"]

                cur.execute(
                    """
                    SELECT review_id
                    FROM review
                    WHERE booking_id = %s
                      AND author_user_id = %s
                      AND target_type = %s::review_target_type
                    """,
                    (booking_id, author_id, normalized_type),
                )
                if cur.fetchone():
                    return {
                        "status": "validation_error",
                        "message": "You already submitted this review for the booking.",
                    }

                cur.execute(
                    """
                    INSERT INTO review (
                      booking_id,
                      author_user_id,
                      target_type,
                      target_user_id,
                      target_listing_id,
                      rating,
                      cleanliness,
                      accuracy,
                      communication,
                      comment
                    )
                    VALUES (%s, %s, %s::review_target_type, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING review_id, booking_id, author_user_id, target_type,
                              target_user_id, target_listing_id, rating,
                              cleanliness, accuracy, communication,
                              comment, created_at
                    """,
                    (
                        booking_id,
                        author_id,
                        normalized_type,
                        target_user_id,
                        target_listing_id,
                        rating_value,
                        cleanliness_value,
                        accuracy_value,
                        communication_value,
                        trimmed_comment,
                    ),
                )
                row = cur.fetchone()
                cur.execute(
                    "SELECT full_name AS author_name FROM app_user WHERE user_id = %s",
                    (author_id,),
                )
                author = cur.fetchone()
                if author:
                    row["author_name"] = author["author_name"]
                conn.commit()

        return {"status": "success", "review": _to_review_row(row)}

    def list_listing_reviews(self, listing_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT listing_id FROM vehicle_listing WHERE listing_id = %s",
                    (listing_id,),
                )
                if not cur.fetchone():
                    return {"status": "not_found", "message": "Listing not found."}

                cur.execute(
                    """
                    SELECT
                      r.review_id,
                      r.booking_id,
                      r.author_user_id,
                      u.full_name AS author_name,
                      r.target_type,
                      r.target_user_id,
                      r.target_listing_id,
                      r.rating,
                      r.cleanliness,
                      r.accuracy,
                      r.communication,
                      r.comment,
                      r.created_at
                    FROM review r
                    JOIN app_user u ON u.user_id = r.author_user_id
                    WHERE r.target_listing_id = %s
                      AND r.target_type = 'LISTING'
                    ORDER BY r.created_at DESC
                    """,
                    (listing_id,),
                )
                rows = cur.fetchall()

        return {
            "status": "success",
            "reviews": [_to_review_row(row) for row in rows],
        }
