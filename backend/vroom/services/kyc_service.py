from __future__ import annotations

from psycopg2.extras import RealDictCursor

from vroom.core.db import get_connection


class KycService:
    def list_pending(self) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                      op.user_id,
                      u.email,
                      u.full_name,
                      op.verification_status,
                      op.created_at
                    FROM owner_profile op
                    JOIN app_user u ON u.user_id = op.user_id
                    WHERE op.verification_status = 'PENDING'
                    ORDER BY op.created_at ASC
                    """
                )
                rows = cur.fetchall()
        return {
            "status": "success",
            "queue": [
                {
                    "userId": row["user_id"],
                    "email": row["email"],
                    "fullName": row["full_name"],
                    "verificationStatus": row["verification_status"],
                    "submittedAt": row["created_at"].isoformat(),
                }
                for row in rows
            ],
        }

    def set_status(self, user_id: int, status: str) -> dict:
        normalized = status.strip().upper()
        if normalized not in {"VERIFIED", "REJECTED"}:
            return {"status": "validation_error", "message": "Status must be VERIFIED or REJECTED."}
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    UPDATE owner_profile
                    SET verification_status = %s
                    WHERE user_id = %s
                    RETURNING user_id, verification_status
                    """,
                    (normalized, user_id),
                )
                row = cur.fetchone()
                if not row:
                    return {"status": "not_found", "message": "Owner profile not found."}
                conn.commit()
        return {
            "status": "success",
            "userId": row["user_id"],
            "verificationStatus": row["verification_status"],
        }


kyc_service = KycService()
