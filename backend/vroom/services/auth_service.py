from __future__ import annotations

import json
import os
import secrets
import urllib.parse
import urllib.request

from psycopg2.extras import RealDictCursor
from werkzeug.security import check_password_hash, generate_password_hash

from vroom.core.config import settings
from vroom.core.db import get_connection
from vroom.dependencies.auth import create_access_token
from vroom.text_sanitize import sanitize_display_text


def _verify_google_id_token(id_token: str) -> dict | None:
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    if not client_id:
        return None
    query = urllib.parse.urlencode({"id_token": id_token})
    url = f"https://oauth2.googleapis.com/tokeninfo?{query}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
    if payload.get("aud") != client_id:
        return None
    if str(payload.get("email_verified", "")).lower() not in {"true", "1"}:
        return None
    email = payload.get("email")
    if not email:
        return None
    return payload


def _fetch_has_listings(cur, user_id: int) -> bool:
    # Sticky host flag: true if the user currently owns a listing OR has ever
    # become a host (owner_profile is created on first publish and never deleted).
    # This keeps host dashboard access after a host removes all their listings.
    cur.execute(
        """
        SELECT (
            EXISTS (SELECT 1 FROM vehicle_listing WHERE owner_user_id = %s)
            OR EXISTS (SELECT 1 FROM owner_profile WHERE user_id = %s)
        ) AS has_listings
        """,
        (user_id, user_id),
    )
    return bool(cur.fetchone()["has_listings"])


def _fetch_trips_count(cur, user_id: int) -> int:
    cur.execute(
        """
        SELECT COUNT(*) AS trips_count
        FROM booking
        WHERE renter_user_id = %s
          AND status = 'COMPLETED'
        """,
        (user_id,),
    )
    return int(cur.fetchone()["trips_count"])


def _fetch_average_rating(cur, user_id: int) -> float | None:
    cur.execute(
        """
        SELECT AVG(rating)::float AS average_rating
        FROM review
        WHERE target_user_id = %s
        """,
        (user_id,),
    )
    value = cur.fetchone()["average_rating"]
    return float(value) if value is not None else None


def _joined_label(created_at) -> str | None:
    if not created_at:
        return None
    return created_at.strftime("Joined %B %Y")


def _normalize_profile_photo_url(value: str | None) -> str | None | bool:
    if value is None:
        return None
    if not isinstance(value, str):
        return False
    url = value.strip()
    if not url:
        return None
    bucket = settings.s3_bucket_name
    region = settings.aws_region
    if bucket and region:
        prefix = f"https://{bucket}.s3.{region}.amazonaws.com/user/"
        if not url.startswith(prefix) or "/avatar/" not in url:
            return False
    elif not (
        url.startswith("https://")
        and ".s3." in url
        and ".amazonaws.com/user/" in url
        and "/avatar/" in url
    ):
        return False
    if len(url) > 2048:
        return False
    return url


class AuthService:
    def _format_user_summary(self, user: dict, has_listings: bool) -> dict:
        return {
            "userId": user["user_id"],
            "email": user["email"],
            "fullName": user.get("full_name"),
            "role": "admin" if user["is_admin"] else "user",
            "isAdmin": bool(user["is_admin"]),
            "hasListings": has_listings,
            "isVerified": bool(user.get("is_verified")),
        }

    def _format_me_user(
        self,
        user: dict,
        has_listings: bool,
        *,
        trips_count: int = 0,
        average_rating: float | None = None,
    ) -> dict:
        phone = user.get("phone")
        return {
            "userId": user["user_id"],
            "email": user["email"],
            "fullName": user["full_name"],
            "phone": phone,
            "profilePhotoUrl": user.get("profile_photo_url"),
            "createdAt": user["created_at"].isoformat() if user["created_at"] else None,
            "joinedLabel": _joined_label(user.get("created_at")),
            "lives": user.get("lives"),
            "about": user.get("about"),
            "languages": user.get("languages"),
            "work": user.get("work"),
            "isApprovedToDrive": bool(user.get("is_approved_to_drive")),
            "hasEmail": bool(user.get("email")),
            "hasPhone": bool(phone and str(phone).strip()),
            "tripsCount": trips_count,
            "averageRating": average_rating,
            "role": "admin" if user["is_admin"] else "user",
            "isAdmin": bool(user["is_admin"]),
            "hasListings": has_listings,
            "isVerified": bool(user.get("is_verified")),
        }

    def _format_public_user(
        self,
        user: dict,
        *,
        has_listings: bool,
        trips_count: int,
        average_rating: float | None,
    ) -> dict:
        # Public-facing subset: never expose email, phone, admin flag, or tokens.
        return {
            "userId": user["user_id"],
            "fullName": user.get("full_name"),
            "profilePhotoUrl": user.get("profile_photo_url"),
            "createdAt": user["created_at"].isoformat() if user["created_at"] else None,
            "joinedLabel": _joined_label(user.get("created_at")),
            "lives": user.get("lives"),
            "about": user.get("about"),
            "languages": user.get("languages"),
            "work": user.get("work"),
            "tripsCount": trips_count,
            "averageRating": average_rating,
            "isVerified": bool(user.get("is_verified")),
            "isHost": has_listings,
        }

    def register(self, email: str, password: str, full_name: str) -> dict:
        verification_token = secrets.token_urlsafe(32)

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT user_id FROM app_user WHERE email = %s", (email,))
                if cur.fetchone():
                    return {"status": "validation_error", "message": "Email already registered."}

                cur.execute(
                    """
                    INSERT INTO app_user (
                        email, password_hash, role, full_name, is_admin,
                        is_verified, verification_token, verification_token_expires_at
                    )
                    VALUES (
                        %s, %s, 'RENTER'::user_role, %s, FALSE, FALSE, %s,
                        NOW() + INTERVAL '24 hours'
                    )
                    RETURNING user_id, email, full_name, is_admin, is_verified
                    """,
                    (
                        email,
                        generate_password_hash(password),
                        full_name,
                        verification_token,
                    ),
                )
                user = cur.fetchone()
                has_listings = _fetch_has_listings(cur, user["user_id"])
                conn.commit()

        token = create_access_token(
            user["user_id"],
            user["email"],
            bool(user["is_admin"]),
            has_listings=has_listings,
        )
        return {
            "status": "success",
            "message": "Check your email to verify your account.",
            "token": token,
            "user": self._format_user_summary(user, has_listings),
            "verification_token": verification_token,
        }

    def resend_verification(self, user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT user_id, email, is_verified
                    FROM app_user
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )
                user = cur.fetchone()
                if not user:
                    return {"status": "not_found", "message": "User not found."}
                if user.get("is_verified"):
                    return {"status": "success", "message": "Email already verified."}

                verification_token = secrets.token_urlsafe(32)
                cur.execute(
                    """
                    UPDATE app_user
                    SET verification_token = %s,
                        verification_token_expires_at = NOW() + INTERVAL '24 hours'
                    WHERE user_id = %s
                    """,
                    (verification_token, user_id),
                )
                conn.commit()

        return {
            "status": "success",
            "message": "Verification email sent.",
            "email": user["email"],
            "verification_token": verification_token,
        }

    def verify_email(self, token: str) -> dict:
        normalized = (token or "").strip()
        if not normalized:
            return {"status": "validation_error", "message": "Verification token is required."}

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT user_id, is_verified,
                           (verification_token_expires_at IS NOT NULL
                            AND verification_token_expires_at < NOW()) AS is_expired
                    FROM app_user
                    WHERE verification_token = %s
                    """,
                    (normalized,),
                )
                user = cur.fetchone()
                if not user:
                    return {
                        "status": "validation_error",
                        "message": "Invalid or expired verification link.",
                    }

                if user.get("is_verified"):
                    return {
                        "status": "success",
                        "message": "Email already verified.",
                    }

                if user.get("is_expired"):
                    return {
                        "status": "validation_error",
                        "message": "Invalid or expired verification link.",
                    }

                # Keep verification_token so re-verifying with the same link stays
                # idempotent; the token is inert once is_verified is TRUE.
                cur.execute(
                    """
                    UPDATE app_user
                    SET is_verified = TRUE
                    WHERE user_id = %s
                    """,
                    (user["user_id"],),
                )
                conn.commit()

        return {
            "status": "success",
            "message": "Your email has been verified.",
        }

    def login(self, email: str, password: str) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT user_id, email, full_name, password_hash, is_admin, is_verified
                    FROM app_user
                    WHERE email = %s
                    """,
                    (email,),
                )
                user = cur.fetchone()
                has_listings = _fetch_has_listings(cur, user["user_id"]) if user else False

        if not user or not check_password_hash(user["password_hash"], password):
            return {"status": "validation_error", "message": "Invalid email or password."}

        token = create_access_token(
            user["user_id"],
            user["email"],
            bool(user["is_admin"]),
            has_listings=has_listings,
        )
        return {
            "status": "success",
            "token": token,
            "user": self._format_user_summary(user, has_listings),
        }

    def me(self, user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT user_id, email, full_name, phone, profile_photo_url,
                           lives, about, languages, work, is_approved_to_drive,
                           created_at, is_admin, is_verified
                    FROM app_user
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )
                user = cur.fetchone()
                has_listings = _fetch_has_listings(cur, user_id) if user else False
                trips_count = _fetch_trips_count(cur, user_id) if user else 0
                average_rating = _fetch_average_rating(cur, user_id) if user else None

        if not user:
            return {"status": "not_found", "message": "User not found."}

        return {
            "status": "success",
            "user": self._format_me_user(
                user,
                has_listings,
                trips_count=trips_count,
                average_rating=average_rating,
            ),
        }

    def public_profile(self, user_id: int) -> dict:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT user_id, full_name, profile_photo_url,
                           lives, about, languages, work, created_at, is_verified
                    FROM app_user
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )
                user = cur.fetchone()
                if not user:
                    return {"status": "not_found", "message": "User not found."}
                has_listings = _fetch_has_listings(cur, user_id)
                trips_count = _fetch_trips_count(cur, user_id)
                average_rating = _fetch_average_rating(cur, user_id)

        return {
            "status": "success",
            "user": self._format_public_user(
                user,
                has_listings=has_listings,
                trips_count=trips_count,
                average_rating=average_rating,
            ),
        }

    def update_me(self, user_id: int, payload: dict) -> dict:
        set_clauses: list[str] = []
        params: list[object] = []

        if "fullName" in payload:
            full_name = payload.get("fullName")
            normalized_full_name = full_name.strip() if isinstance(full_name, str) else full_name
            if isinstance(normalized_full_name, str):
                normalized_full_name = sanitize_display_text(normalized_full_name, max_length=150)
            if normalized_full_name == "":
                normalized_full_name = None
            if normalized_full_name is not None and len(normalized_full_name) > 150:
                return {
                    "status": "validation_error",
                    "message": "Full name must be 150 characters or less.",
                }
            set_clauses.append("full_name = %s")
            params.append(normalized_full_name)

        if "phone" in payload:
            phone = payload.get("phone")
            normalized_phone = phone.strip() if isinstance(phone, str) else phone
            if normalized_phone == "":
                normalized_phone = None
            if normalized_phone is not None and len(normalized_phone) > 32:
                return {
                    "status": "validation_error",
                    "message": "Phone must be 32 characters or less.",
                }
            set_clauses.append("phone = %s")
            params.append(normalized_phone)

        if "lives" in payload:
            lives = payload.get("lives")
            normalized_lives = lives.strip() if isinstance(lives, str) else lives
            if isinstance(normalized_lives, str):
                normalized_lives = sanitize_display_text(normalized_lives, max_length=100)
            if normalized_lives == "":
                normalized_lives = None
            if normalized_lives is not None and len(normalized_lives) > 100:
                return {
                    "status": "validation_error",
                    "message": "Lives must be 100 characters or less.",
                }
            set_clauses.append("lives = %s")
            params.append(normalized_lives)

        if "about" in payload:
            about = payload.get("about")
            normalized_about = about.strip() if isinstance(about, str) else about
            if isinstance(normalized_about, str):
                normalized_about = sanitize_display_text(normalized_about, max_length=2000)
            if normalized_about == "":
                normalized_about = None
            if normalized_about is not None and len(normalized_about) > 2000:
                return {
                    "status": "validation_error",
                    "message": "About must be 2000 characters or less.",
                }
            set_clauses.append("about = %s")
            params.append(normalized_about)

        if "languages" in payload:
            languages = payload.get("languages")
            normalized_languages = languages.strip() if isinstance(languages, str) else languages
            if isinstance(normalized_languages, str):
                normalized_languages = sanitize_display_text(normalized_languages, max_length=150)
            if normalized_languages == "":
                normalized_languages = None
            if normalized_languages is not None and len(normalized_languages) > 150:
                return {
                    "status": "validation_error",
                    "message": "Languages must be 150 characters or less.",
                }
            set_clauses.append("languages = %s")
            params.append(normalized_languages)

        if "work" in payload:
            work = payload.get("work")
            normalized_work = work.strip() if isinstance(work, str) else work
            if isinstance(normalized_work, str):
                normalized_work = sanitize_display_text(normalized_work, max_length=100)
            if normalized_work == "":
                normalized_work = None
            if normalized_work is not None and len(normalized_work) > 100:
                return {
                    "status": "validation_error",
                    "message": "Work must be 100 characters or less.",
                }
            set_clauses.append("work = %s")
            params.append(normalized_work)

        new_photo_url: str | None = None
        if "profilePhotoUrl" in payload:
            normalized_url = _normalize_profile_photo_url(payload.get("profilePhotoUrl"))
            if normalized_url is False:
                return {
                    "status": "validation_error",
                    "message": "Invalid profile photo URL.",
                }
            new_photo_url = normalized_url
            set_clauses.append("profile_photo_url = %s")
            params.append(normalized_url)

        if not set_clauses:
            return {"status": "validation_error", "message": "No profile fields to update."}

        params.append(user_id)
        old_photo_url: str | None = None

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if "profilePhotoUrl" in payload:
                    cur.execute(
                        "SELECT profile_photo_url FROM app_user WHERE user_id = %s",
                        (user_id,),
                    )
                    existing = cur.fetchone()
                    if existing:
                        old_photo_url = existing.get("profile_photo_url")

                cur.execute(
                    f"""
                    UPDATE app_user
                    SET {", ".join(set_clauses)}
                    WHERE user_id = %s
                    RETURNING user_id, email, full_name, phone, profile_photo_url,
                              lives, about, languages, work, is_approved_to_drive,
                              created_at, is_admin, is_verified
                    """,
                    tuple(params),
                )
                user = cur.fetchone()
                has_listings = _fetch_has_listings(cur, user_id) if user else False
                trips_count = _fetch_trips_count(cur, user_id) if user else 0
                average_rating = _fetch_average_rating(cur, user_id) if user else None
                conn.commit()

        if not user:
            return {"status": "not_found", "message": "User not found."}

        if "profilePhotoUrl" in payload and old_photo_url and old_photo_url != new_photo_url:
            from vroom.services import uploads_service

            uploads_service.delete_user_avatar_file(user_id, old_photo_url)

        return {
            "status": "success",
            "user": self._format_me_user(
                user,
                has_listings,
                trips_count=trips_count,
                average_rating=average_rating,
            ),
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

    def google_login(self, id_token: str) -> dict:
        profile = _verify_google_id_token(id_token)
        if not profile:
            return {"status": "validation_error", "message": "Invalid Google token."}

        email = profile["email"]
        full_name = profile.get("name")

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT user_id, email, full_name, is_admin, is_verified
                    FROM app_user
                    WHERE email = %s
                    """,
                    (email,),
                )
                user = cur.fetchone()
                if not user:
                    cur.execute(
                        """
                        INSERT INTO app_user (
                            email, password_hash, role, full_name, is_admin,
                            is_verified, verification_token
                        )
                        VALUES (%s, %s, 'RENTER'::user_role, %s, FALSE, TRUE, NULL)
                        RETURNING user_id, email, full_name, is_admin, is_verified
                        """,
                        (email, generate_password_hash(secrets.token_urlsafe(32)), full_name),
                    )
                    user = cur.fetchone()
                elif full_name and not (user.get("full_name") or "").strip():
                    # Backfill name for accounts created before Google name capture
                    # (otherwise their listings show the "Individual host" fallback).
                    cur.execute(
                        """
                        UPDATE app_user SET full_name = %s WHERE user_id = %s
                        RETURNING user_id, email, full_name, is_admin, is_verified
                        """,
                        (full_name, user["user_id"]),
                    )
                    user = cur.fetchone()
                has_listings = _fetch_has_listings(cur, user["user_id"])
                conn.commit()

        token = create_access_token(
            user["user_id"],
            user["email"],
            bool(user["is_admin"]),
            has_listings=has_listings,
        )
        return {
            "status": "success",
            "token": token,
            "user": self._format_user_summary(user, has_listings),
        }
