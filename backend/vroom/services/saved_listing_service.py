from __future__ import annotations

from psycopg2.extras import RealDictCursor

from vroom.core.db import get_connection
from vroom.services.marketplace_common import LISTING_SELECT_SQL, hydrate_listing_rows


class SavedListingService:
    def _fetch_saved_ids(self, cur, user_id: int) -> list[int]:
        cur.execute(
            """
            SELECT sl.listing_id
            FROM saved_listing sl
            JOIN vehicle_listing l ON l.listing_id = sl.listing_id
            WHERE sl.user_id = %s
            ORDER BY sl.created_at DESC
            """,
            (user_id,),
        )
        return [int(row["listing_id"]) for row in cur.fetchall()]

    def list_saved(self, user_id: int) -> dict:
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            saved_ids = self._fetch_saved_ids(cur, user_id)
            if not saved_ids:
                return {"status": "success", "savedListingIds": [], "listings": []}

            cur.execute(
                f"""
                {LISTING_SELECT_SQL}
                WHERE l.listing_id = ANY(%s)
                """,
                (saved_ids,),
            )
            rows = cur.fetchall()
            by_id = {int(row["listing_id"]): row for row in rows}
            ordered_rows = [by_id[listing_id] for listing_id in saved_ids if listing_id in by_id]
            listings = hydrate_listing_rows(cur, ordered_rows)
            return {
                "status": "success",
                "savedListingIds": saved_ids,
                "listings": listings,
            }

    def save_listing(self, user_id: int, listing_id: int) -> dict:
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                """
                SELECT listing_id
                FROM vehicle_listing
                WHERE listing_id = %s
                """,
                (listing_id,),
            )
            if not cur.fetchone():
                return {"status": "not_found", "message": "Listing not found."}

            cur.execute(
                """
                INSERT INTO saved_listing (user_id, listing_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, listing_id) DO NOTHING
                """,
                (user_id, listing_id),
            )
            conn.commit()
            saved_ids = self._fetch_saved_ids(cur, user_id)
            return {
                "status": "success",
                "listingId": listing_id,
                "saved": True,
                "savedListingIds": saved_ids,
            }

    def unsave_listing(self, user_id: int, listing_id: int) -> dict:
        with get_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                """
                DELETE FROM saved_listing
                WHERE user_id = %s AND listing_id = %s
                """,
                (user_id, listing_id),
            )
            conn.commit()
            saved_ids = self._fetch_saved_ids(cur, user_id)
            return {
                "status": "success",
                "listingId": listing_id,
                "saved": False,
                "savedListingIds": saved_ids,
            }


saved_listing_service = SavedListingService()
