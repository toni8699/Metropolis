from __future__ import annotations

from psycopg2.extras import RealDictCursor

from metropolis.db import get_connection


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

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                      b.booking_id,
                      b.status,
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
                      comment
                    )
                    VALUES (%s, %s, %s::review_target_type, %s, %s, %s, %s)
                    RETURNING review_id, booking_id, author_user_id, target_type,
                              target_user_id, target_listing_id, rating, comment, created_at
                    """,
                    (
                        booking_id,
                        author_id,
                        normalized_type,
                        target_user_id,
                        target_listing_id,
                        rating_value,
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
