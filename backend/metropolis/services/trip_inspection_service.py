from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from psycopg2.extras import RealDictCursor

from metropolis.core.config import settings
from metropolis.core.db import get_connection
from metropolis.services.booking_support import trip_is_active_window, utcnow
from metropolis.trip_inspection_angles import (
    ANGLE_MANIFEST,
    MAX_EXTRA_PHOTOS_PER_PHASE,
    RECOMMENDED_ANGLE_COUNT,
    STANDARD_ANGLE_COUNT,
)


class TripInspectionService:
    def _booking_access(self, cur, booking_id: int, user_id: int, is_admin: bool) -> dict | None:
        cur.execute(
            """
            SELECT b.booking_id, b.renter_user_id, b.status, b.start_at, b.end_at,
                   b.completed_at, l.owner_user_id
            FROM booking b
            JOIN vehicle_listing l ON l.listing_id = b.listing_id
            WHERE b.booking_id = %s
            """,
            (booking_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"status": "not_found", "message": "Booking not found."}
        is_renter = row["renter_user_id"] == user_id
        is_host = row["owner_user_id"] == user_id
        if not (is_admin or is_renter or is_host):
            return {"status": "forbidden", "message": "No access to this booking."}
        row["is_renter"] = is_renter
        row["is_host"] = is_host
        return row

    def renter_can_upload_phase(self, booking: dict, phase: str) -> bool:
        if not booking.get("is_renter"):
            return False
        status = str(booking["status"]).upper()
        phase_upper = phase.upper()
        if phase_upper == "CHECK_IN":
            return status == "CONFIRMED" and trip_is_active_window(
                booking["start_at"], booking["end_at"]
            )
        if phase_upper == "CHECK_OUT":
            return status == "IN_PROGRESS"
        return False

    def assert_renter_upload_access(
        self, cur, booking_id: int, user_id: int, phase: str, is_extra: bool
    ) -> dict | None:
        booking = self._booking_access(cur, booking_id, user_id, False)
        if isinstance(booking, dict) and booking.get("status") == "forbidden":
            return booking
        if isinstance(booking, dict) and booking.get("status") == "not_found":
            return booking
        if not booking.get("is_renter"):
            return {
                "status": "forbidden",
                "message": "Only the renter can upload inspection photos.",
            }
        if not self.renter_can_upload_phase(booking, phase):
            return {
                "status": "validation_error",
                "message": "Inspection uploads are not available for this trip phase.",
            }
        if is_extra:
            cur.execute(
                """
                SELECT COUNT(*) AS extra_count
                FROM booking_inspection_photo
                WHERE booking_id = %s
                  AND phase = %s::trip_inspection_phase
                  AND is_extra = TRUE
                """,
                (booking_id, phase.upper()),
            )
            extra_count = int(cur.fetchone()["extra_count"])
            if extra_count >= MAX_EXTRA_PHOTOS_PER_PHASE:
                return {
                    "status": "validation_error",
                    "message": f"Maximum {MAX_EXTRA_PHOTOS_PER_PHASE} extra photos per phase.",
                }
        return None

    def booking_has_inspection_photos(self, cur, booking_id: int) -> bool:
        cur.execute(
            """
            SELECT EXISTS (
              SELECT 1 FROM booking_inspection_photo WHERE booking_id = %s
            ) AS has_photos
            """,
            (booking_id,),
        )
        return bool(cur.fetchone()["has_photos"])

    def _expires_at(self, completed_at: datetime | None) -> str | None:
        if completed_at is None:
            return None
        expires = completed_at + timedelta(days=settings.trip_inspection_retention_days)
        return expires.astimezone(UTC).isoformat()

    def _is_purged(self, booking: dict, has_rows: bool) -> bool:
        if has_rows:
            return False
        completed_at = booking.get("completed_at")
        if completed_at is None:
            return False
        cutoff = utcnow() - timedelta(days=settings.trip_inspection_retention_days)
        completed = completed_at
        if completed.tzinfo is None:
            completed = completed.replace(tzinfo=UTC)
        return completed < cutoff

    def _phase_payload(self, cur, booking: dict, phase: str) -> dict:
        phase_upper = phase.upper()
        cur.execute(
            """
            SELECT bip.angle_key, bip.is_extra, bip.photo_id, fa.file_url
            FROM booking_inspection_photo bip
            JOIN file_asset fa ON fa.file_id = bip.file_id
            WHERE bip.booking_id = %s AND bip.phase = %s::trip_inspection_phase
            ORDER BY bip.is_extra ASC, bip.created_at ASC
            """,
            (booking["booking_id"], phase_upper),
        )
        rows = cur.fetchall()
        by_key: dict[str, dict] = {}
        extras: list[dict] = []
        for row in rows:
            item = {
                "photoId": row["photo_id"],
                "angleKey": row["angle_key"],
                "fileUrl": row["file_url"],
                "isExtra": bool(row["is_extra"]),
            }
            if row["is_extra"]:
                extras.append(item)
            else:
                by_key[row["angle_key"]] = item

        slots = []
        for entry in ANGLE_MANIFEST:
            filled = by_key.get(entry["key"])
            slots.append(
                {
                    "angleKey": entry["key"],
                    "group": entry["group"],
                    "title": entry["title"],
                    "instruction": entry["instruction"],
                    "icon": entry.get("icon", "Camera"),
                    "recommendedFirst": bool(entry.get("recommendedFirst")),
                    "photo": filled,
                }
            )
        for extra in extras:
            slots.append(
                {
                    "angleKey": extra["angleKey"],
                    "title": "Existing damage",
                    "instruction": "Close-up of scratch, dent, or crack.",
                    "icon": "Plus",
                    "recommendedFirst": False,
                    "photo": extra,
                    "isExtra": True,
                }
            )

        standard_uploaded = sum(1 for entry in ANGLE_MANIFEST if by_key.get(entry["key"]))
        return {
            "slots": slots,
            "uploaded": standard_uploaded + len(extras),
            "standardUploaded": standard_uploaded,
            "recommended": RECOMMENDED_ANGLE_COUNT,
            "standardTotal": STANDARD_ANGLE_COUNT,
            "canUpload": self.renter_can_upload_phase(booking, phase_upper),
        }

    def get_inspection(self, booking_id: int, user_id: int, is_admin: bool) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                booking = self._booking_access(cur, booking_id, user_id, is_admin)
                if booking.get("status") in {"not_found", "forbidden"}:
                    return booking
                has_rows = self.booking_has_inspection_photos(cur, booking_id)
                purged = self._is_purged(booking, has_rows)
                return {
                    "status": "success",
                    "checkIn": self._phase_payload(cur, booking, "CHECK_IN"),
                    "checkOut": self._phase_payload(cur, booking, "CHECK_OUT"),
                    "expiresAt": self._expires_at(booking.get("completed_at")),
                    "purged": purged,
                }

    def link_photo(
        self,
        cur,
        *,
        booking_id: int,
        file_id: int,
        phase: str,
        angle_key: str,
        is_extra: bool,
        user_id: int,
    ) -> None:
        phase_upper = phase.upper()
        if not is_extra:
            cur.execute(
                """
                SELECT photo_id, file_id
                FROM booking_inspection_photo
                WHERE booking_id = %s
                  AND phase = %s::trip_inspection_phase
                  AND angle_key = %s
                  AND is_extra = FALSE
                """,
                (booking_id, phase_upper, angle_key),
            )
            existing = cur.fetchone()
            if existing:
                old_file_id = int(existing["file_id"])
                cur.execute(
                    """
                    UPDATE booking_inspection_photo
                    SET file_id = %s,
                        uploaded_by_user_id = %s,
                        created_at = NOW()
                    WHERE photo_id = %s
                    """,
                    (file_id, user_id, existing["photo_id"]),
                )
                if old_file_id != file_id:
                    cur.execute("DELETE FROM file_asset WHERE file_id = %s", (old_file_id,))
                return

        if is_extra and not angle_key:
            angle_key = f"extra_{uuid4().hex[:12]}"

        cur.execute(
            """
            INSERT INTO booking_inspection_photo (
              booking_id, file_id, phase, angle_key, is_extra, uploaded_by_user_id
            )
            VALUES (%s, %s, %s::trip_inspection_phase, %s, %s, %s)
            """,
            (booking_id, file_id, phase_upper, angle_key, is_extra, user_id),
        )

    def sweep_expired_trip_inspection_photos(self) -> dict:
        days = settings.trip_inspection_retention_days
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT fa.file_id
                    FROM file_asset fa
                    JOIN booking_inspection_photo bip ON bip.file_id = fa.file_id
                    JOIN booking b ON b.booking_id = bip.booking_id
                    WHERE b.status = 'COMPLETED'
                      AND b.completed_at IS NOT NULL
                      AND b.completed_at < NOW() - make_interval(days => %s)
                    """,
                    (days,),
                )
                file_ids = [int(row[0]) for row in cur.fetchall()]
                if not file_ids:
                    return {"status": "success", "deleted": 0}
                cur.execute(
                    "DELETE FROM file_asset WHERE file_id = ANY(%s)",
                    (file_ids,),
                )
                deleted = cur.rowcount
                conn.commit()
        return {"status": "success", "deleted": deleted}

    def delete_inspection_photo(
        self, booking_id: int, photo_id: int, user_id: int, is_admin: bool
    ) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                booking = self._booking_access(cur, booking_id, user_id, is_admin)
                if booking.get("status") in {"not_found", "forbidden"}:
                    return booking
                if not booking.get("is_renter"):
                    return {
                        "status": "forbidden",
                        "message": "Only the renter can delete inspection photos.",
                    }
                cur.execute(
                    """
                    SELECT bip.photo_id, bip.file_id, bip.phase, bip.booking_id
                    FROM booking_inspection_photo bip
                    WHERE bip.photo_id = %s AND bip.booking_id = %s
                    """,
                    (photo_id, booking_id),
                )
                row = cur.fetchone()
                if not row:
                    return {"status": "not_found", "message": "Inspection photo not found."}
                phase = str(row["phase"]).upper()
                if not self.renter_can_upload_phase(booking, phase):
                    return {
                        "status": "validation_error",
                        "message": "Inspection deletes are not available for this trip phase.",
                    }
                cur.execute(
                    "DELETE FROM file_asset WHERE file_id = %s",
                    (int(row["file_id"]),),
                )
                conn.commit()
        return {"status": "success"}


trip_inspection_service = TripInspectionService()
