#!/usr/bin/env python3
"""Remove CI/integration-test listings from a dev database."""

from __future__ import annotations

import argparse
import os
import sys

import psycopg2

# ponytail: title patterns from seed_ci_database + integration tests
TEST_TITLE_SQL = """
    title = 'CI Test Listing'
    OR title LIKE 'Search Test %'
    OR title LIKE 'Approval Test %'
    OR title LIKE 'CI Fleet %'
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete test marketplace listings.")
    parser.add_argument(
        "--all-p2p",
        action="store_true",
        help="Delete every P2P host listing (source_type=OWNER, not company-owned).",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete rows (default is dry-run preview only).",
    )
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 1

    where = (
        TEST_TITLE_SQL if not args.all_p2p else "source_type = 'OWNER' AND is_company_owned = FALSE"
    )

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT listing_id, title, source_type, is_company_owned
                FROM vehicle_listing
                WHERE {where}
                ORDER BY listing_id
                """
            )
            rows = cur.fetchall()

            if not rows:
                print("No matching listings.")
                return 0

            print(f"{'DELETE' if args.execute else 'DRY-RUN'}: {len(rows)} listing(s)")
            for listing_id, title, source_type, is_company_owned in rows:
                print(f"  #{listing_id} [{source_type}] company={is_company_owned} — {title}")

            if not args.execute:
                print("\nRe-run with --execute to delete. Add --all-p2p to wipe all host listings.")
                return 0

            listing_ids = [row[0] for row in rows]
            cur.execute(
                "DELETE FROM vehicle_listing WHERE listing_id = ANY(%s)",
                (listing_ids,),
            )
        conn.commit()

    print(f"Deleted {len(rows)} listing(s).")
    print("Note: FLEET rows reappear after 'Sync Fleet Now' unless vehicle_asset rows are removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
