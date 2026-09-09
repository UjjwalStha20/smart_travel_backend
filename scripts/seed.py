"""Full database seed: loads catalog data from data/*.csv and adds demo users,
reviews, photos, saved destinations, trips (from user_trip.csv) and itineraries.

Usage:
    uv run python scripts/seed.py
"""
import os
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.db import engine, init_db
from app.core.security import hash_password
from app.models import (
    Accommodation,
    Address,
    Attraction,
    Blog,
    ChatConversation,
    ChatMessage,
    Destination,
    DestinationItinerary,
    EntryFee,
    FoodCost,
    Itinerary,
    Permit,
    Photo,
    RecommendationLog,
    Review,
    RoutePoint,
    SavedDestination,
    TrekkingRoute,
    User,
    UserInteraction,
    UserPreferences,
    UserTrip,
)
from scripts.import_csv import CSV_CONFIG, DATA_DIR, generate_uuid, load_csv, parse_value
from sqlmodel import Session, delete

# Tables sorted so children are removed before their parents.
ALL_TABLES = [
    ChatMessage, ChatConversation, UserInteraction, RecommendationLog,
    DestinationItinerary, Itinerary, UserTrip, SavedDestination,
    Review, Photo, Permit, EntryFee, RoutePoint, TrekkingRoute,
    Attraction, Destination, Address, Accommodation, FoodCost,
    UserPreferences, Blog, User,
]


def clear_all(session: Session):
    for table in ALL_TABLES:
        session.exec(delete(table))
    session.commit()


def main():
    print("Seeding database...")
    init_db()

    key_to_uuid = {}

    with Session(engine) as session:
        clear_all(session)

        # ── Demo users ────────────────────────────────────────────────
        users = [
            User(
                name="Admin User", role="admin",
                email="admin@example.com", password=hash_password("admin123"),
                nationality="Nepal", phone="+977-9800000002",
            ),
            User(
                name="John Doe", role="traveler",
                email="john@example.com", password=hash_password("password123"),
                nationality="USA", phone="+977-9800000001",
            ),
            User(
                name="Ujjwal Shrestha", role="traveler",
                email="ujjwal@gmail.com", password=hash_password("password123"),
                nationality="Nepal", phone="+977-9841000001",
            ),
            User(
                name="Anusha Shrestha", role="admin",
                email="anusha@admin.com", password=hash_password("admin123"),
                nationality="Nepal", phone="+977-9841000002",
            ),
        ]
        session.add_all(users)
        session.flush()
        user_by_email = {u.email: u for u in users}
        print(f"  [OK] users: {len(users)}")

        # ── Catalog data from CSV files ───────────────────────────────
        created: dict[str, list] = {}
        for table_name, config in CSV_CONFIG.items():
            filepath = DATA_DIR / config["file"]
            if not filepath.exists():
                print(f"  [SKIP] {filepath.name} not found")
                continue

            rows = load_csv(str(filepath))
            model = config["model"]
            objects = []
            for row in rows:
                key = row["key"]
                record_key = generate_uuid(key)
                key_to_uuid[key] = record_key

                kwargs = {"id": record_key}
                for field in config["fields"]:
                    kwargs[field] = parse_value(row.get(field, ""), field)

                for csv_col, model_col in config["fk_map"].items():
                    ref_key = row.get(csv_col, "")
                    if ref_key:
                        kwargs[model_col] = key_to_uuid.get(ref_key)
                        if kwargs[model_col] is None:
                            print(
                                f"  [WARN] {table_name}:{key} references unknown "
                                f"{csv_col}={ref_key}"
                            )

                objects.append(model(**kwargs))

            session.add_all(objects)
            session.flush()
            created[table_name] = objects
            print(f"  [OK] {table_name}: {len(objects)} rows")

        # ── Enrich blogs with authors and publish dates ───────────────
        authors = [user_by_email["admin@example.com"], user_by_email["john@example.com"]]
        for i, blog in enumerate(created["blog"]):
            blog.author_id = authors[i % 2].id
            blog.published_at = datetime(2026, 2, 20 + (i % 9), 10, 0, 0)

        # ── User trips + itineraries from user_trip.csv ───────────────
        trip_rows = load_csv(str(DATA_DIR / "user_trip.csv"))
        itinerary_rows = load_csv(str(DATA_DIR / "destination_itinerary.csv"))
        trips = []
        for row in trip_rows:
            user = user_by_email.get(row["user_email"])
            if not user:
                print(f"  [WARN] trip {row['key']}: unknown user {row['user_email']}")
                continue
            trip = UserTrip(
                id=generate_uuid(row["key"]),
                user_id=user.id,
                destination_id=key_to_uuid.get(row["destination_key"]),
                route_id=key_to_uuid.get(row["route_key"] or ""),
                pace_type=row["pace_type"],
                budget_type=row["budget_type"],
                start_date=date.fromisoformat(row["start_date"]) if row.get("start_date") else None,
                end_date=date.fromisoformat(row["end_date"]) if row.get("end_date") else None,
                status=row["status"],
            )
            session.add(trip)
            trips.append((trip, row))
        session.flush()
        print(f"  [OK] user_trips: {len(trips)}")

        for trip, row in trips:
            day_rows = [
                it for it in itinerary_rows
                if it["destination_key"] == row["destination_key"]
            ]
            itineraries = [
                Itinerary(
                    id=generate_uuid(f"{row['key']}_day{it['day_number']}"),
                    trip_id=trip.id,
                    day_number=int(it["day_number"]),
                    start_location=it["start_location"],
                    end_location=it["end_location"],
                    overnight_location=it["overnight_location"] or None,
                    estimated_walking_hours=(
                        Decimal(it["estimated_walking_hours"])
                        if it.get("estimated_walking_hours") else None
                    ),
                    notes=it["notes"] or None,
                )
                for it in day_rows
            ]
            session.add_all(itineraries)
        print(f"  [OK] itineraries generated for {len(trips)} trips")

        # ── Reviews, photos, saved destinations ───────────────────────
        john = user_by_email["john@example.com"]
        admin = user_by_email["anusha@admin.com"]

        reviews = [
            Review(
                id=generate_uuid("rev_pashu_admin"), user_id=admin.id,
                destination_id=key_to_uuid["dest_pashupatinath"], rating=5,
                comment="The evening aarti at the Bagmati ghats is unforgettable.",
            ),
            Review(
                id=generate_uuid("rev_mardi_john"), user_id=john.id,
                destination_id=key_to_uuid["dest_mardi_himal_trek"], rating=5,
                comment="Easily the best quiet trek in the Annapurnas - barely any crowds.",
            ),
            Review(
                id=generate_uuid("rev_rara_admin"), user_id=admin.id,
                destination_id=key_to_uuid["dest_rara"], rating=5,
                comment="Turquoise water and total silence. Worth every hour of travel.",
            ),
        ]
        session.add_all(reviews)

        photos = [
            Photo(
                id=generate_uuid("photo_pashu"), destination_id=key_to_uuid["dest_pashupatinath"],
                uploaded_by=john.id,
                image_url="https://images.example.com/pashupatinath.jpg",
                caption="The ghats of the Bagmati at golden hour",
            ),
            Photo(
                id=generate_uuid("photo_mardi"), destination_id=key_to_uuid["dest_mardi_himal_trek"],
                uploaded_by=admin.id,
                image_url="https://images.example.com/mardi-summit.jpg",
                caption="The ridgeline above Mardi Himal Base Camp",
            ),
            Photo(
                id=generate_uuid("photo_rara"), destination_id=key_to_uuid["dest_rara"],
                uploaded_by=admin.id,
                image_url="https://images.example.com/rara-lake.jpg",
                caption="Rara Lake beneath the forested ridges",
            ),
        ]
        session.add_all(photos)

        saved = [
            SavedDestination(user_id=john.id, destination_id=key_to_uuid["dest_abc_trek"]),
            SavedDestination(user_id=john.id, destination_id=key_to_uuid["dest_rara"]),
            SavedDestination(user_id=admin.id, destination_id=key_to_uuid["dest_pashupatinath"]),
        ]
        session.add_all(saved)

        session.commit()

    print("Done! Seed data inserted:")
    for table_name, objs in created.items():
        print(f"  - {table_name}: {len(objs)} rows")
    print(f"  - users: {len(user_by_email)}")
    print(f"  - user_trips: {len(trips)}")


if __name__ == "__main__":
    main()