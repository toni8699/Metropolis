from __future__ import annotations

from psycopg2.extras import RealDictCursor

from metropolis.db import get_connection
from metropolis.services.marketplace_common import _fetch_listing_images_map


class MessageService:
    def _fetch_booking_participants(self, cur, booking_id: int) -> dict | None:
        cur.execute(
            """
            SELECT
                b.booking_id,
                b.renter_user_id,
                l.owner_user_id
            FROM booking b
            JOIN vehicle_listing l ON l.listing_id = b.listing_id
            WHERE b.booking_id = %s
            """,
            (booking_id,),
        )
        return cur.fetchone()

    def assert_booking_participant(
        self,
        booking_id: int,
        user_id: int,
        is_admin: bool = False,
    ) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                row = self._fetch_booking_participants(cur, booking_id)
        if not row:
            return {"status": "not_found", "message": "Booking not found."}
        is_renter = row["renter_user_id"] == user_id
        is_owner = row["owner_user_id"] == user_id
        if not (is_admin or is_renter or is_owner):
            return {"status": "forbidden", "message": "No access to this booking."}
        return {
            "status": "ok",
            "bookingId": row["booking_id"],
            "renterUserId": row["renter_user_id"],
            "ownerUserId": row["owner_user_id"],
        }

    def _to_message_row(self, row: dict) -> dict:
        return {
            "messageId": row["message_id"],
            "bookingId": row["booking_id"],
            "senderId": row["sender_id"],
            "senderName": row.get("sender_name"),
            "messageText": row["message_text"],
            "createdAt": row["created_at"].isoformat(),
        }

    def _upsert_chat_read_state(
        self,
        cur,
        booking_id: int,
        user_id: int,
        last_message_id: int,
    ) -> None:
        cur.execute(
            """
            INSERT INTO booking_chat_state (booking_id, user_id, last_read_message_id, last_read_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (booking_id, user_id)
            DO UPDATE SET
                last_read_message_id = EXCLUDED.last_read_message_id,
                last_read_at = NOW()
            """,
            (booking_id, user_id, last_message_id),
        )

    def _unread_count_sql(self) -> str:
        return """
            (
              SELECT COUNT(*)::int
              FROM booking_message um
              WHERE um.booking_id = b.booking_id
                AND um.sender_id != %s
                AND (
                  cs.last_read_message_id IS NULL
                  OR um.message_id > cs.last_read_message_id
                )
            )
        """

    def list_booking_messages(
        self,
        booking_id: int,
        requester_user_id: int,
        requester_is_admin: bool,
    ) -> dict:
        """Return the full booking thread ordered by created_at ASC.

        Intentionally unpaginated: marketplace trip chats stay small.
        Uses idx_booking_message_booking_created (booking_id, created_at).
        """
        access = self.assert_booking_participant(booking_id, requester_user_id, requester_is_admin)
        if access["status"] != "ok":
            return access

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        m.message_id,
                        m.booking_id,
                        m.sender_id,
                        m.message_text,
                        m.created_at,
                        u.full_name AS sender_name
                    FROM booking_message m
                    JOIN app_user u ON u.user_id = m.sender_id
                    WHERE m.booking_id = %s
                    ORDER BY m.created_at ASC, m.message_id ASC
                    """,
                    (booking_id,),
                )
                rows = cur.fetchall()

                if rows:
                    self._upsert_chat_read_state(
                        cur,
                        booking_id,
                        requester_user_id,
                        rows[-1]["message_id"],
                    )
                conn.commit()

        return {
            "status": "ok",
            "messages": [self._to_message_row(r) for r in rows],
        }

    def create_booking_message(
        self,
        booking_id: int,
        sender_id: int,
        message_text: str,
        requester_is_admin: bool = False,
    ) -> dict:
        text = (message_text or "").strip()
        if not text:
            return {"status": "validation_error", "message": "Message cannot be empty."}
        if len(text) > 4000:
            return {
                "status": "validation_error",
                "message": "Message is too long (max 4000 characters).",
            }

        access = self.assert_booking_participant(booking_id, sender_id, requester_is_admin)
        if access["status"] != "ok":
            return access

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO booking_message (booking_id, sender_id, message_text)
                    VALUES (%s, %s, %s)
                    RETURNING message_id, booking_id, sender_id, message_text, created_at
                    """,
                    (booking_id, sender_id, text),
                )
                inserted = cur.fetchone()
                cur.execute(
                    """
                    SELECT full_name AS sender_name
                    FROM app_user
                    WHERE user_id = %s
                    """,
                    (sender_id,),
                )
                sender = cur.fetchone()
                conn.commit()

        inserted["sender_name"] = sender["sender_name"] if sender else None
        return {
            "status": "ok",
            "message": self._to_message_row(inserted),
        }

    def _thread_pricing_from_row(self, row: dict) -> dict:
        snapshot = row.get("price_snapshot_json") or {}
        if isinstance(snapshot, str):
            snapshot = {}
        price_per_day = float(snapshot.get("pricePerDay") or row.get("price_per_day") or 0)
        return {
            "pricePerDay": price_per_day,
            "dayCount": snapshot.get("dayCount"),
            "total": float(snapshot.get("total") or 0),
            "currency": snapshot.get("currency") or "CAD",
        }

    def list_message_threads(self, user_id: int) -> dict:
        unread_sql = self._unread_count_sql()
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    SELECT
                      b.booking_id,
                      b.listing_id,
                      b.renter_user_id,
                      b.status,
                      b.start_at,
                      b.end_at,
                      b.price_snapshot_json,
                      b.updated_at AS booking_updated_at,
                      l.title AS listing_title,
                      l.price_per_day,
                      l.owner_user_id,
                      loc.city_zone,
                      host.full_name AS host_name,
                      host.email AS host_email,
                      renter.full_name AS renter_name,
                      renter.email AS renter_email,
                      lm.message_text AS latest_message_text,
                      lm.created_at AS latest_message_at,
                      {unread_sql} AS unread_count
                    FROM booking b
                    JOIN vehicle_listing l ON l.listing_id = b.listing_id
                    LEFT JOIN listing_location loc ON loc.listing_id = l.listing_id
                    LEFT JOIN app_user host ON host.user_id = l.owner_user_id
                    LEFT JOIN app_user renter ON renter.user_id = b.renter_user_id
                    LEFT JOIN booking_chat_state cs
                      ON cs.booking_id = b.booking_id AND cs.user_id = %s
                    INNER JOIN LATERAL (
                      SELECT message_text, created_at
                      FROM booking_message
                      WHERE booking_id = b.booking_id
                      ORDER BY created_at DESC, message_id DESC
                      LIMIT 1
                    ) lm ON TRUE
                    WHERE b.renter_user_id = %s OR l.owner_user_id = %s
                    ORDER BY lm.created_at DESC, b.booking_id DESC
                    """,
                    (user_id, user_id, user_id, user_id),
                )
                rows = cur.fetchall()
                listing_ids = list({row["listing_id"] for row in rows})
                images_by_listing = _fetch_listing_images_map(cur, listing_ids)

        threads = []
        for row in rows:
            is_renter = row["renter_user_id"] == user_id
            if is_renter:
                other_party = {
                    "userId": row["owner_user_id"],
                    "name": row["host_name"],
                    "email": row["host_email"],
                }
                user_role = "renter"
            else:
                other_party = {
                    "userId": row["renter_user_id"],
                    "name": row["renter_name"],
                    "email": row["renter_email"],
                }
                user_role = "host"

            cover_urls = images_by_listing.get(row["listing_id"], [])
            cover_photo = cover_urls[0] if cover_urls else None

            thread = {
                "bookingId": row["booking_id"],
                "listingId": row["listing_id"],
                "status": row["status"],
                "startAt": row["start_at"].isoformat(),
                "endAt": row["end_at"].isoformat(),
                "cityZone": row["city_zone"],
                "userRole": user_role,
                "renterUserId": row["renter_user_id"],
                "ownerUserId": row["owner_user_id"],
                "otherParty": other_party,
                "listing": {
                    "listingId": row["listing_id"],
                    "title": row["listing_title"],
                    "pricePerDay": float(row["price_per_day"] or 0),
                    "coverPhoto": cover_photo,
                },
                "pricing": self._thread_pricing_from_row(row),
            }
            if row["latest_message_at"]:
                thread["latestMessage"] = {
                    "messageText": row["latest_message_text"],
                    "createdAt": row["latest_message_at"].isoformat(),
                }
            else:
                continue
            thread["unreadCount"] = int(row.get("unread_count") or 0)
            threads.append(thread)

        return {"status": "ok", "threads": threads}
