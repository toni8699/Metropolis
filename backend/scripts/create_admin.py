#!/usr/bin/env python3
"""Bootstrap an admin user via direct database insert (not public register)."""

from __future__ import annotations

import getpass
import os
import sys

import psycopg2
from werkzeug.security import generate_password_hash


def main() -> int:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 1

    email = input("Admin email: ").strip()
    if not email:
        print("Email is required", file=sys.stderr)
        return 1

    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Confirm password: ")
    if password != password_confirm:
        print("Passwords do not match", file=sys.stderr)
        return 1
    if len(password) < 8:
        print("Password must be at least 8 characters", file=sys.stderr)
        return 1

    full_name = input("Full name (optional): ").strip() or email.split("@", 1)[0]

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM app_user WHERE email = %s", (email,))
            if cur.fetchone():
                print(f"User already exists: {email}", file=sys.stderr)
                return 1
            cur.execute(
                """
                INSERT INTO app_user (email, password_hash, role, full_name, is_admin, is_verified)
                VALUES (%s, %s, 'ADMIN'::user_role, %s, TRUE, TRUE)
                RETURNING user_id
                """,
                (email, generate_password_hash(password), full_name),
            )
            user_id = cur.fetchone()[0]
        conn.commit()

    print(f"Created admin user_id={user_id} email={email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
