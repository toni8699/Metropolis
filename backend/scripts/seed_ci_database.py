#!/usr/bin/env python3
"""Minimal marketplace rows for CI integration tests."""

from __future__ import annotations

import os
import sys

import psycopg2
from werkzeug.security import generate_password_hash

CI_HOST_EMAIL = "ci-host@metropolis.test"
CI_LISTING_TITLE = "CI Test Listing"


def main() -> int:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 1

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_user (email, password_hash, role, full_name, is_admin)
                VALUES (%s, %s, 'RENTER', 'CI Host', FALSE)
                ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
                RETURNING user_id
                """,
                (CI_HOST_EMAIL, generate_password_hash("unused")),
            )
            user_id = cur.fetchone()[0]

            cur.execute(
                """
                SELECT listing_id
                FROM vehicle_listing
                WHERE title = %s
                LIMIT 1
                """,
                (CI_LISTING_TITLE,),
            )
            existing = cur.fetchone()
            if existing:
                listing_id = existing[0]
            else:
                cur.execute(
                    """
                    INSERT INTO vehicle_listing (
                      owner_user_id, source_type, title, price_per_day, active, is_company_owned
                    )
                    VALUES (%s, 'OWNER', %s, 49.99, TRUE, FALSE)
                    RETURNING listing_id
                    """,
                    (user_id, CI_LISTING_TITLE),
                )
                listing_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO listing_location (listing_id, lat, lng, city_zone)
                VALUES (%s, 45.501700, -73.567300, 'montreal')
                ON CONFLICT (listing_id) DO NOTHING
                """,
                (listing_id,),
            )
        conn.commit()

    print(f"CI seed ready (listing_id={listing_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
