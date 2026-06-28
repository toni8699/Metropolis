#!/usr/bin/env python3
"""Populate the marketplace with realistic mock data using Faker + factory-boy.

All seeded users share the ``@seed.vroom.test`` email domain so the data is easy
to find and remove again (``--reset``). Run against a dev/staging database only.

Examples:
    DATABASE_URL=... python scripts/seed_marketplace.py
    DATABASE_URL=... python scripts/seed_marketplace.py --owners 12 --renters 25
    DATABASE_URL=... python scripts/seed_marketplace.py --reset
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from datetime import datetime, timedelta, timezone

import factory
import psycopg2
from faker import Faker
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash

# ponytail: shared marker so seeded rows are findable + removable without a tag column.
SEED_EMAIL_DOMAIN = "seed.vroom.test"
SEED_PASSWORD = "Password123!"

fake = Faker()

# City zones mirror vroom.services.marketplace_common.CITY_COORDS (kept local so the
# script has no app-import dependency / DB pool side effects).
CITY_COORDS = {
    "montreal": (45.5017, -73.5673),
    "toronto": (43.6532, -79.3832),
    "vancouver": (49.2827, -123.1207),
    "calgary": (51.0447, -114.0719),
    "ottawa": (45.4215, -75.6972),
}

# make, model, ref_body_type.code, vehicle_category, fuel_type, seats
CAR_CATALOG = [
    ("Toyota", "Corolla", "SEDAN", "STANDARD", "Gasoline", 5),
    ("Honda", "Civic", "SEDAN", "STANDARD", "Gasoline", 5),
    ("Mazda", "3", "SEDAN", "STANDARD", "Gasoline", 5),
    ("Toyota", "RAV4", "SUV", "STANDARD", "Hybrid", 5),
    ("Honda", "CR-V", "SUV", "STANDARD", "Gasoline", 5),
    ("Subaru", "Outback", "WAGON", "STANDARD", "Gasoline", 5),
    ("Ford", "F-150", "TRUCK", "TRUCK", "Gasoline", 5),
    ("Ram", "1500", "TRUCK", "TRUCK", "Diesel", 5),
    ("Tesla", "Model 3", "EV", "EV", "Electric", 5),
    ("Tesla", "Model Y", "EV", "EV", "Electric", 5),
    ("Chevrolet", "Bolt", "EV", "EV", "Electric", 5),
    ("Hyundai", "Ioniq 5", "EV", "EV", "Electric", 5),
    ("BMW", "3 Series", "SEDAN", "LUXURY", "Gasoline", 5),
    ("Mercedes-Benz", "C-Class", "SEDAN", "LUXURY", "Gasoline", 5),
    ("Audi", "A4", "SEDAN", "LUXURY", "Gasoline", 5),
    ("Porsche", "911", "COUPE", "LUXURY", "Gasoline", 4),
    ("Chrysler", "Pacifica", "MINIVAN", "STANDARD", "Hybrid", 7),
    ("Dodge", "Grand Caravan", "MINIVAN", "STANDARD", "Gasoline", 7),
]

FEATURE_CODES = [
    "APPLE_CARPLAY",
    "ANDROID_AUTO",
    "BLUETOOTH",
    "SUNROOF",
    "HEATED_SEATS",
    "AWD",
    "BACKUP_CAMERA",
    "BLIND_SPOT_WARNING",
    "KEYLESS_ENTRY",
]


def _vin() -> str:
    # 17-char VIN-ish string (no I/O/Q like real VINs); unique per process run.
    return fake.unique.bothify("?#?#?#?#?#?#?#?#?", letters="ABCDEFGHJKLMNPRSTUVWXYZ")


class UserFactory(factory.DictFactory):
    full_name = factory.Faker("name")
    email = factory.LazyAttribute(lambda o: f"{fake.unique.user_name()}@{SEED_EMAIL_DOMAIN}")
    phone = factory.Faker("numerify", text="+1##########")
    about = factory.Faker("sentence", nb_words=14)
    languages = factory.LazyFunction(
        lambda: ", ".join(random.sample(["English", "French", "Spanish", "Mandarin"], 2))
    )
    lives = factory.Faker("city")
    work = factory.Faker("job")
    profile_photo_url = factory.LazyAttribute(lambda o: f"https://i.pravatar.cc/300?u={o.email}")


class VehicleFactory(factory.DictFactory):
    spec = factory.LazyFunction(lambda: random.choice(CAR_CATALOG))
    make = factory.LazyAttribute(lambda o: o.spec[0])
    model = factory.LazyAttribute(lambda o: o.spec[1])
    body_code = factory.LazyAttribute(lambda o: o.spec[2])
    category = factory.LazyAttribute(lambda o: o.spec[3])
    fuel_type = factory.LazyAttribute(lambda o: o.spec[4])
    seats = factory.LazyAttribute(lambda o: o.spec[5])
    model_year = factory.LazyFunction(lambda: random.randint(2016, 2025))
    transmission = factory.LazyAttribute(
        lambda o: (
            "AUTOMATIC"
            if o.fuel_type == "Electric"
            else random.choice(["AUTOMATIC", "AUTOMATIC", "MANUAL"])
        )
    )
    vin = factory.LazyFunction(_vin)
    estimated_value = factory.LazyFunction(lambda: round(random.uniform(18000, 95000), 2))

    class Meta:
        exclude = ("spec",)


class ListingFactory(factory.DictFactory):
    city_zone = factory.LazyFunction(lambda: random.choice(list(CITY_COORDS)))
    price_per_day = factory.LazyFunction(lambda: round(random.uniform(35, 220), 2))
    doors = factory.LazyFunction(lambda: random.choice([2, 4, 4, 4]))
    instant_book = factory.LazyFunction(lambda: random.random() < 0.7)
    guidelines = factory.Faker("sentence", nb_words=12)
    pickup_notes_template = factory.Faker("sentence", nb_words=10)


def _jitter_coords(city_zone: str) -> tuple[float, float]:
    base_lat, base_lng = CITY_COORDS[city_zone]
    return (
        round(base_lat + random.uniform(-0.06, 0.06), 6),
        round(base_lng + random.uniform(-0.06, 0.06), 6),
    )


def _description(v: dict) -> str:
    return (
        f"{v['model_year']} {v['make']} {v['model']} — "
        f"{fake.sentence(nb_words=18)} Perfect for {fake.word()} trips around town."
    )


def _ref_lookup(cur, table: str, key: str = "code") -> dict[str, int]:
    id_col = {"ref_body_type": "body_type_id", "ref_feature": "feature_id"}[table]
    cur.execute(f"SELECT {key}, {id_col} FROM {table}")
    return {row[key]: row[id_col] for row in cur.fetchall()}


def seed(cur, *, owners: int, renters: int, max_listings: int, bookings: int) -> dict:
    body_types = _ref_lookup(cur, "ref_body_type")
    features = _ref_lookup(cur, "ref_feature")
    if not body_types or not features:
        raise RuntimeError("Reference data missing — run `alembic upgrade head` first.")

    pw_hash = generate_password_hash(SEED_PASSWORD)
    owner_ids: list[int] = []
    renter_ids: list[int] = []
    listing_ids: list[int] = []

    # --- Owners (+ owner_profile) and their vehicles/listings ---------------
    for _ in range(owners):
        u = UserFactory()
        cur.execute(
            """
            INSERT INTO app_user
              (email, password_hash, role, full_name, phone, profile_photo_url,
               lives, about, languages, work, is_verified)
            VALUES (%s, %s, 'OWNER', %s, %s, %s, %s, %s, %s, %s, TRUE)
            RETURNING user_id
            """,
            (
                u["email"],
                pw_hash,
                u["full_name"],
                u["phone"],
                u["profile_photo_url"],
                u["lives"],
                u["about"],
                u["languages"],
                u["work"],
            ),
        )
        owner_id = cur.fetchone()["user_id"]
        owner_ids.append(owner_id)
        cur.execute(
            "INSERT INTO owner_profile (user_id, verification_status) VALUES (%s, 'VERIFIED')",
            (owner_id,),
        )

        for _ in range(random.randint(1, max_listings)):
            v = VehicleFactory()
            cur.execute(
                """
                INSERT INTO vehicle_asset
                  (vin, vehicle_category, body_type_id, owner_type, owner_party_user_id,
                   asset_status, make, model, model_year, fuel_type, transmission, seats,
                   estimated_value, is_vin_verified)
                VALUES (%s, %s::vehicle_category, %s, 'INDEPENDENT_HOST', %s,
                        'ACTIVE', %s, %s, %s, %s::fuel_type_enum,
                        %s::transmission_type, %s, %s, TRUE)
                RETURNING vehicle_id
                """,
                (
                    v["vin"],
                    v["category"],
                    body_types[v["body_code"]],
                    owner_id,
                    v["make"],
                    v["model"],
                    v["model_year"],
                    v["fuel_type"],
                    v["transmission"],
                    v["seats"],
                    v["estimated_value"],
                ),
            )
            vehicle_id = cur.fetchone()["vehicle_id"]

            li = ListingFactory()
            title = f"{v['model_year']} {v['make']} {v['model']}"
            cur.execute(
                """
                INSERT INTO vehicle_listing
                  (owner_user_id, created_by_user_id, vehicle_id, source_type, title,
                   listing_title, make, model, year, description, guidelines,
                   transmission, fuel_type, seats, doors, pickup_notes_template,
                   price_per_day, active, status, instant_book)
                VALUES (%s, %s, %s, 'OWNER', %s, %s, %s, %s, %s, %s, %s,
                        %s::transmission_type, %s::fuel_type_enum, %s, %s, %s,
                        %s, TRUE, 'ACTIVE', %s)
                RETURNING listing_id
                """,
                (
                    owner_id,
                    owner_id,
                    vehicle_id,
                    title,
                    title,
                    v["make"],
                    v["model"],
                    v["model_year"],
                    _description(v),
                    li["guidelines"],
                    v["transmission"],
                    v["fuel_type"],
                    v["seats"],
                    li["doors"],
                    li["pickup_notes_template"],
                    li["price_per_day"],
                    li["instant_book"],
                ),
            )
            listing_id = cur.fetchone()["listing_id"]
            listing_ids.append(listing_id)

            lat, lng = _jitter_coords(li["city_zone"])
            cur.execute(
                """
                INSERT INTO listing_location
                  (listing_id, lat, lng, geohash, city_zone, pickup_address)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    listing_id,
                    lat,
                    lng,
                    f"{round(lat, 2)}:{round(lng, 2)}",
                    li["city_zone"],
                    fake.street_address(),
                ),
            )

            for code in random.sample(FEATURE_CODES, random.randint(3, 6)):
                cur.execute(
                    "INSERT INTO listing_feature (listing_id, feature_id) VALUES (%s, %s)",
                    (listing_id, features[code]),
                )

            cur.execute(
                """
                INSERT INTO listing_availability (listing_id, start_at, end_at, status)
                VALUES (%s, NOW(), NOW() + INTERVAL '180 days', 'AVAILABLE')
                """,
                (listing_id,),
            )

            for order in range(random.randint(2, 4)):
                seed_no = random.randint(1, 9999)
                key = f"seed/{listing_id}/{order}-{seed_no}.jpg"
                url = f"https://picsum.photos/seed/{listing_id}-{order}/1024/768"
                cur.execute(
                    """
                    INSERT INTO file_asset
                      (owner_user_id, listing_id, bucket, object_key, file_url,
                       content_type, scope)
                    VALUES (%s, %s, 'seed', %s, %s, 'image/jpeg', 'OWNER_LISTING')
                    RETURNING file_id
                    """,
                    (owner_id, listing_id, key, url),
                )
                file_id = cur.fetchone()["file_id"]
                cur.execute(
                    "INSERT INTO listing_image (listing_id, file_id, display_order) "
                    "VALUES (%s, %s, %s)",
                    (listing_id, file_id, order),
                )

    # --- Renters ------------------------------------------------------------
    for _ in range(renters):
        u = UserFactory()
        cur.execute(
            """
            INSERT INTO app_user
              (email, password_hash, role, full_name, phone, profile_photo_url,
               about, is_verified, is_approved_to_drive)
            VALUES (%s, %s, 'RENTER', %s, %s, %s, %s, TRUE, TRUE)
            RETURNING user_id
            """,
            (u["email"], pw_hash, u["full_name"], u["phone"], u["profile_photo_url"], u["about"]),
        )
        renter_ids.append(cur.fetchone()["user_id"])

    # --- Completed bookings + reviews (so cards show ratings) ---------------
    review_count = 0
    if bookings and listing_ids and renter_ids:
        for _ in range(bookings):
            listing_id = random.choice(listing_ids)
            renter_id = random.choice(renter_ids)
            cur.execute(
                "SELECT owner_user_id, price_per_day FROM vehicle_listing WHERE listing_id = %s",
                (listing_id,),
            )
            row = cur.fetchone()
            owner_id, price = row["owner_user_id"], float(row["price_per_day"])

            days = random.randint(1, 6)
            start = datetime.now(timezone.utc) - timedelta(days=random.randint(10, 120))
            end = start + timedelta(days=days)
            total_cents = int(round(price * days * 100))
            cur.execute(
                """
                INSERT INTO booking
                  (listing_id, renter_user_id, start_at, end_at, status,
                   price_snapshot_json, completed_at)
                VALUES (%s, %s, %s, %s, 'COMPLETED', %s::jsonb, %s)
                RETURNING booking_id
                """,
                (
                    listing_id,
                    renter_id,
                    start,
                    end,
                    f'{{"pricePerDay": {price}, "days": {days}, "totalCents": {total_cents}}}',
                    end,
                ),
            )
            booking_id = cur.fetchone()["booking_id"]
            cur.execute(
                """
                INSERT INTO payment (booking_id, amount_cents, currency, status)
                VALUES (%s, %s, 'cad', 'succeeded')
                """,
                (booking_id, total_cents),
            )
            # Renter reviews the listing.
            cur.execute(
                """
                INSERT INTO review
                  (booking_id, author_user_id, target_type, target_listing_id,
                   rating, cleanliness, accuracy, communication, comment)
                VALUES (%s, %s, 'LISTING', %s, %s, %s, %s, %s, %s)
                """,
                (
                    booking_id,
                    renter_id,
                    listing_id,
                    random.randint(3, 5),
                    random.randint(3, 5),
                    random.randint(3, 5),
                    random.randint(3, 5),
                    fake.sentence(nb_words=16),
                ),
            )
            # Owner reviews the renter.
            cur.execute(
                """
                INSERT INTO review
                  (booking_id, author_user_id, target_type, target_user_id, rating, comment)
                VALUES (%s, %s, 'RENTER', %s, %s, %s)
                """,
                (booking_id, owner_id, renter_id, random.randint(4, 5), fake.sentence(nb_words=12)),
            )
            review_count += 2

    return {
        "owners": len(owner_ids),
        "renters": len(renter_ids),
        "listings": len(listing_ids),
        "bookings": bookings if (listing_ids and renter_ids) else 0,
        "reviews": review_count,
    }


def reset(cur) -> dict:
    """Delete everything tied to seeded users (FK order matters)."""
    cur.execute(
        "SELECT user_id FROM app_user WHERE email LIKE %s",
        (f"%@{SEED_EMAIL_DOMAIN}",),
    )
    user_ids = [r["user_id"] for r in cur.fetchall()]
    if not user_ids:
        return {"users": 0, "listings": 0}

    cur.execute(
        "SELECT listing_id FROM vehicle_listing WHERE owner_user_id = ANY(%s)",
        (user_ids,),
    )
    listing_ids = [r["listing_id"] for r in cur.fetchall()]

    # bookings reference listings with ON DELETE RESTRICT -> remove them first.
    cur.execute(
        "DELETE FROM booking WHERE renter_user_id = ANY(%s) OR listing_id = ANY(%s)",
        (user_ids, listing_ids or [-1]),
    )
    # listings cascade to location/feature/availability/image/file_asset.
    cur.execute("DELETE FROM vehicle_listing WHERE owner_user_id = ANY(%s)", (user_ids,))
    cur.execute("DELETE FROM vehicle_asset WHERE owner_party_user_id = ANY(%s)", (user_ids,))
    cur.execute("DELETE FROM app_user WHERE user_id = ANY(%s)", (user_ids,))
    return {"users": len(user_ids), "listings": len(listing_ids)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owners", type=int, default=8)
    parser.add_argument("--renters", type=int, default=15)
    parser.add_argument("--max-listings", type=int, default=3, help="max listings per owner")
    parser.add_argument("--bookings", type=int, default=20, help="completed bookings + reviews")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for reproducibility")
    parser.add_argument("--reset", action="store_true", help="delete seeded data and exit")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        try:
            from dotenv import load_dotenv

            load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
            database_url = os.environ.get("DATABASE_URL", "").strip()
        except ImportError:
            pass
    if not database_url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 1

    if args.seed is not None:
        random.seed(args.seed)
        Faker.seed(args.seed)

    with psycopg2.connect(database_url, cursor_factory=RealDictCursor) as conn:
        with conn.cursor() as cur:
            if args.reset:
                stats = reset(cur)
                conn.commit()
                print(f"Reset: removed {stats['users']} users, {stats['listings']} listings")
                return 0
            stats = seed(
                cur,
                owners=args.owners,
                renters=args.renters,
                max_listings=args.max_listings,
                bookings=args.bookings,
            )
        conn.commit()

    print(
        "Seeded marketplace: "
        + ", ".join(f"{v} {k}" for k, v in stats.items())
        + f"\nLogin with any @{SEED_EMAIL_DOMAIN} email / password: {SEED_PASSWORD}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
