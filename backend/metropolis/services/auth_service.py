from __future__ import annotations

from psycopg2.extras import RealDictCursor
from werkzeug.security import check_password_hash, generate_password_hash

from metropolis.auth import create_access_token
from metropolis.db import get_connection


class AuthService:
    def register(self, email: str, password: str, full_name: str | None, role: str) -> dict:
        normalized_role = role.upper()
        if normalized_role not in {"RENTER", "OWNER", "ADMIN"}:
            normalized_role = "RENTER"

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT user_id FROM app_user WHERE email = %s", (email,))
                if cur.fetchone():
                    return {"status": "validation_error", "message": "Email already registered."}

                cur.execute(
                    """
                    INSERT INTO app_user (email, password_hash, role, full_name)
                    VALUES (%s, %s, %s::user_role, %s)
                    RETURNING user_id, email, role, full_name
                    """,
                    (email, generate_password_hash(password), normalized_role, full_name),
                )
                user = cur.fetchone()

                if normalized_role == "OWNER":
                    cur.execute(
                        """
                        INSERT INTO owner_profile (user_id, verification_status)
                        VALUES (%s, 'PENDING')
                        """,
                        (user["user_id"],),
                    )
                conn.commit()

        token = create_access_token(user["user_id"], user["email"], user["role"])
        return {
            "status": "success",
            "token": token,
            "user": {
                "userId": user["user_id"],
                "email": user["email"],
                "role": user["role"],
                "fullName": user["full_name"],
            },
        }

    def login(self, email: str, password: str) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT user_id, email, role, full_name, password_hash
                    FROM app_user
                    WHERE email = %s
                    """,
                    (email,),
                )
                user = cur.fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            return {"status": "validation_error", "message": "Invalid email or password."}

        token = create_access_token(user["user_id"], user["email"], user["role"])
        return {
            "status": "success",
            "token": token,
            "user": {
                "userId": user["user_id"],
                "email": user["email"],
                "role": user["role"],
                "fullName": user["full_name"],
            },
        }

    def me(self, user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT user_id, email, role, full_name, phone, created_at
                    FROM app_user
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )
                user = cur.fetchone()

        if not user:
            return {"status": "not_found", "message": "User not found."}

        return {
            "status": "success",
            "user": {
                "userId": user["user_id"],
                "email": user["email"],
                "role": user["role"],
                "fullName": user["full_name"],
                "phone": user["phone"],
                "createdAt": user["created_at"].isoformat() if user["created_at"] else None,
            },
        }
