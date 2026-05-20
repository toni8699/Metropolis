from __future__ import annotations

from psycopg2.extras import RealDictCursor
from werkzeug.security import check_password_hash, generate_password_hash

from metropolis.auth import create_access_token
from metropolis.db import get_connection


def _fetch_has_listings(cur, user_id: int) -> bool:
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM vehicle_listing
            WHERE owner_user_id = %s
        ) AS has_listings
        """,
        (user_id,),
    )
    return bool(cur.fetchone()["has_listings"])


class AuthService:
    def register(self, email: str, password: str, full_name: str | None, role: str | None) -> dict:
        normalized_role = (role or "user").strip().lower()
        is_admin = normalized_role == "admin"

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT user_id FROM app_user WHERE email = %s", (email,))
                if cur.fetchone():
                    return {"status": "validation_error", "message": "Email already registered."}

                cur.execute(
                    """
                    INSERT INTO app_user (email, password_hash, role, full_name, is_admin)
                    VALUES (%s, %s, %s::user_role, %s, %s)
                    RETURNING user_id, email, full_name, is_admin
                    """,
                    (
                        email,
                        generate_password_hash(password),
                        "ADMIN" if is_admin else "RENTER",
                        full_name,
                        is_admin,
                    ),
                )
                user = cur.fetchone()
                has_listings = _fetch_has_listings(cur, user["user_id"])
                conn.commit()

        token = create_access_token(user["user_id"], user["email"], bool(user["is_admin"]))
        return {
            "status": "success",
            "token": token,
            "user": {
                "userId": user["user_id"],
                "email": user["email"],
                "fullName": user["full_name"],
                "role": "admin" if user["is_admin"] else "user",
                "isAdmin": bool(user["is_admin"]),
                "hasListings": has_listings,
            },
        }

    def login(self, email: str, password: str) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT user_id, email, full_name, password_hash, is_admin
                    FROM app_user
                    WHERE email = %s
                    """,
                    (email,),
                )
                user = cur.fetchone()
                has_listings = _fetch_has_listings(cur, user["user_id"]) if user else False

        if not user or not check_password_hash(user["password_hash"], password):
            return {"status": "validation_error", "message": "Invalid email or password."}

        token = create_access_token(user["user_id"], user["email"], bool(user["is_admin"]))
        return {
            "status": "success",
            "token": token,
            "user": {
                "userId": user["user_id"],
                "email": user["email"],
                "fullName": user["full_name"],
                "role": "admin" if user["is_admin"] else "user",
                "isAdmin": bool(user["is_admin"]),
                "hasListings": has_listings,
            },
        }

    def me(self, user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT user_id, email, full_name, phone, created_at, is_admin
                    FROM app_user
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )
                user = cur.fetchone()
                has_listings = _fetch_has_listings(cur, user_id) if user else False

        if not user:
            return {"status": "not_found", "message": "User not found."}

        return {
            "status": "success",
            "user": {
                "userId": user["user_id"],
                "email": user["email"],
                "fullName": user["full_name"],
                "phone": user["phone"],
                "createdAt": user["created_at"].isoformat() if user["created_at"] else None,
                "role": "admin" if user["is_admin"] else "user",
                "isAdmin": bool(user["is_admin"]),
                "hasListings": has_listings,
            },
        }

    def admin_list_users(self) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT user_id, email, full_name, is_admin, created_at
                    FROM app_user
                    ORDER BY created_at DESC
                    LIMIT 200
                    """
                )
                users = [
                    {
                        "userId": row["user_id"],
                        "email": row["email"],
                        "fullName": row["full_name"],
                        "isAdmin": bool(row["is_admin"]),
                        "role": "admin" if row["is_admin"] else "user",
                        "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
                    }
                    for row in cur.fetchall()
                ]
        return {"status": "success", "users": users}
