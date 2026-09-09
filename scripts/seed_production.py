"""Safe, idempotent database seed for production (Render PostgreSQL).

Unlike the original seed.py, this script:
  - NEVER clears or truncates existing data
  - Updates existing rows from CSV (category, highlights, detail data)
  - Uses deterministic UUIDs (uuid5) so it is safe to re-run
  - Uses real Unsplash image URLs for destination photos
  - Flags the first photo of each destination as is_featured

Usage:
    uv run python scripts/seed_production.py
"""
import os
import sys
import uuid
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
    Destination,
    DestinationItinerary,
    EntryFee,
    FoodCost,
    HikeDetails,
    MountainDetails,
    NatureDetails,
    Permit,
    Photo,
    Review,
    RoutePoint,
    TrekDetails,
    TrekkingRoute,
    User,
    UserTrip,
    Itinerary,
)
from scripts.import_csv import CSV_CONFIG, DATA_DIR, generate_uuid, load_csv, parse_value
from sqlmodel import Session, select


# ── Photo URLs (Unsplash source — free, no API key required) ───────────
PHOTO_URLS = {
    "dest_pashupatinath":     "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    "dest_boudhanath":        "https://images.unsplash.com/photo-1562079062-1da4e8a74567?w=800&q=80",
    "dest_swayambhunath":     "https://images.unsplash.com/photo-1585135497273-1a86b09fe70e?w=800&q=80",
    "dest_bhaktapur_durbar":  "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    "dest_patan_durbar":      "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    "dest_lumbini":           "https://images.unsplash.com/photo-1585135497273-1a86b09fe70e?w=800&q=80",
    "dest_janaki_mandir":     "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    "dest_chitwan":           "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    "dest_phewa_lake":        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_nagarkot":          "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_bandipur":          "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    "dest_manakamana":        "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    "dest_chandragiri":       "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_gosaikunda":        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_abc_trek":          "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    "dest_poon_hill_trek":    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_ebc_trek":          "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    "dest_langtang_trek":     "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_rara":              "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_muktinath":         "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    "dest_sarangkot":         "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_dhulikhel":         "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_budhanilkantha":    "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    "dest_garden_of_dreams":  "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    "dest_mountain_museum":   "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_peace_pagoda":      "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_mardi_himal_trek":  "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_manaslu_trek":      "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    "dest_gokyo_trek":        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_annapurna_circuit": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    # ── New destinations ────────────────────────────────────────────────
    "dest_thamel":            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    "dest_kathmandu_durbar":  "https://images.unsplash.com/photo-1585135497273-1a86b09fe70e?w=800&q=80",
    "dest_shivapuri_hike":    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_island_peak":       "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
    "dest_phoksundo":         "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_devis_fall":        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "dest_trishuli_rafting":  "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80",
}

PHOTO_CAPTIONS = {
    "dest_pashupatinath":     "Sacred ghats of Pashupatinath Temple",
    "dest_boudhanath":        "Boudhanath Stupa — UNESCO World Heritage Site",
    "dest_swayambhunath":     "Swayambhunath (Monkey Temple) overlooking Kathmandu",
    "dest_bhaktapur_durbar":  "Bhaktapur Durbar Square — medieval Newari architecture",
    "dest_patan_durbar":      "Patan Durbar Square — Krishna Mandir",
    "dest_lumbini":           "Lumbini Sacred Garden — birthplace of Buddha",
    "dest_janaki_mandir":     "Janaki Mandir — Janakpur",
    "dest_chitwan":           "Chitwan National Park — wildlife safari",
    "dest_phewa_lake":        "Phewa Lake, Pokhara — reflections of Annapurna",
    "dest_nagarkot":          "Nagarkot sunrise view over the Himalayas",
    "dest_bandipur":          "Bandipur hill town — panoramic mountain views",
    "dest_manakamana":        "Manakamana Temple — cable car pilgrimage",
    "dest_chandragiri":       "Chandragiri Hills — panoramic Kathmandu Valley view",
    "dest_gosaikunda":        "Gosaikunda sacred alpine lake at 4,380 m",
    "dest_abc_trek":          "Annapurna Base Camp Trek — the Annapurna Sanctuary",
    "dest_poon_hill_trek":    "Ghorepani Poon Hill — iconic sunrise panorama",
    "dest_ebc_trek":          "Everest Base Camp Trek — the Khumbu",
    "dest_langtang_trek":     "Langtang Valley Trek — Valley of Glaciers",
    "dest_rara":              "Rara Lake — Nepal's largest lake",
    "dest_muktinath":         "Muktinath Temple — sacred to Hindus and Buddhists",
    "dest_sarangkot":         "Sarangkot viewpoint — Annapurna and Machhapuchhre",
    "dest_dhulikhel":         "Dhulikhel — Himalayan panorama from the valley rim",
    "dest_budhanilkantha":    "Budhanilkantha — the Sleeping Vishnu",
    "dest_garden_of_dreams":  "Garden of Dreams — neo-classical garden in Thamel",
    "dest_mountain_museum":   "International Mountain Museum, Pokhara",
    "dest_peace_pagoda":      "World Peace Pagoda, Pokhara",
    "dest_mardi_himal_trek":  "Mardi Himal Trek — hidden gem of the Annapurnas",
    "dest_manaslu_trek":      "Manaslu Circuit — remote wilderness trek",
    "dest_gokyo_trek":        "Gokyo Lakes Trek — turquoise glacial lakes",
    "dest_annapurna_circuit": "Annapurna Circuit — crossing Thorong La pass",
    "dest_thamel":            "Thamel — Kathmandu's vibrant tourist hub",
    "dest_kathmandu_durbar":  "Kathmandu Durbar Square — Hanuman Dhoka palace complex",
    "dest_shivapuri_hike":    "Shivapuri Nagarjun National Park — Kathmandu's green lung",
    "dest_island_peak":       "Island Peak (Imja Tse) — classic Himalayan climbing peak",
    "dest_phoksundo":         "Phoksundo Lake — Nepal's deepest lake in Dolpa",
    "dest_devis_fall":        "Devi's Fall, Pokhara — plunging into an underground gorge",
    "dest_trishuli_rafting":  "White-water rafting on the Trishuli River",
}


def exists(session, model, record_id):
    return session.get(model, record_id) is not None


# Tables whose primary keys may have been generated by the app (admin form)
# rather than by the uuid5 seed scheme. For these we ALSO look the row up by
# its natural/unique key so the seed can reconcile a previously-created row.
def _dest_lookup(row, key_to_uuid, column):
    did = key_to_uuid.get(row.get("destination_key", ""))
    return [column == did] if did else None


def _entry_fee_lookup(row, key_to_uuid):
    aid = key_to_uuid.get(row.get("attraction_key", ""))
    if not aid:
        return None
    return [EntryFee.attraction_id == aid, EntryFee.category == row["category"].lower()]


def _blog_lookup(row, key_to_uuid):
    return [Blog.slug == row["slug"]] if row.get("slug") else None


NATURAL_LOOKUP = {
    "attraction":   lambda row, k: _dest_lookup(row, k, Attraction.destination_id),
    "trek_details": lambda row, k: _dest_lookup(row, k, TrekDetails.destination_id),
    "hike_details": lambda row, k: _dest_lookup(row, k, HikeDetails.destination_id),
    "mountain_details": lambda row, k: _dest_lookup(row, k, MountainDetails.destination_id),
    "nature_details":   lambda row, k: _dest_lookup(row, k, NatureDetails.destination_id),
    "entry_fee":    _entry_fee_lookup,
    "blog":         _blog_lookup,
}


def _normalize(model, field, val):
    """Coerce a raw CSV string into the column's enum member if needed."""
    if val is None:
        return None
    try:
        stype = model.__table__.c[field].type
        enum_class = getattr(stype, "enum_class", None)
        if enum_class is not None and isinstance(val, str):
            return enum_class(val)
    except Exception:
        pass
    return val


def main():
    print("=== Production Seed / Reconcile (idempotent) ===")
    init_db()

    stats = {name: {"inserted": 0, "updated": 0, "skipped": 0} for name in CSV_CONFIG}
    stats["users"]     = {"inserted": 0, "updated": 0, "skipped": 0}
    stats["photos"]    = {"inserted": 0, "updated": 0, "skipped": 0}
    stats["reviews"]   = {"inserted": 0, "updated": 0, "skipped": 0}
    stats["user_trips"]  = {"inserted": 0, "updated": 0, "skipped": 0}
    stats["itineraries"] = {"inserted": 0, "updated": 0, "skipped": 0}

    key_to_uuid: dict[str, uuid.UUID] = {}

    with Session(engine) as session:
        # ── Demo users ────────────────────────────────────────────────
        users_data = [
            {
                "name": "Admin User", "role": "admin",
                "email": "admin@example.com", "password": hash_password("admin123"),
                "nationality": "Nepal", "phone": "+977-9800000002",
            },
            {
                "name": "John Doe", "role": "traveler",
                "email": "john@example.com", "password": hash_password("password123"),
                "nationality": "USA", "phone": "+977-9800000001",
            },
            {
                "name": "Ujjwal Shrestha", "role": "traveler",
                "email": "ujjwal@gmail.com", "password": hash_password("password123"),
                "nationality": "Nepal", "phone": "+977-9841000001",
            },
            {
                "name": "Anusha Shrestha", "role": "admin",
                "email": "anusha@admin.com", "password": hash_password("admin123"),
                "nationality": "Nepal", "phone": "+977-9841000002",
            },
        ]

        user_by_email: dict[str, User] = {}
        for ud in users_data:
            existing = session.exec(select(User).where(User.email == ud["email"])).first()
            if existing:
                user_by_email[ud["email"]] = existing
                stats["users"]["skipped"] += 1
            else:
                user = User(**ud)
                session.add(user)
                session.flush()
                user_by_email[ud["email"]] = user
                stats["users"]["inserted"] += 1

        # ── Catalog data from CSV files (upsert) ─────────────────────
        for table_name, config in CSV_CONFIG.items():
            filepath = DATA_DIR / config["file"]
            if not filepath.exists():
                print(f"  [SKIP] {filepath.name} not found")
                continue

            rows = load_csv(str(filepath))
            model = config["model"]
            fields = config["fields"]
            fk_map = config["fk_map"]

            for row in rows:
                key = row["key"]
                record_key = generate_uuid(key)
                key_to_uuid[key] = record_key

                existing = session.get(model, record_key)
                if existing is None:
                    lookup = NATURAL_LOOKUP.get(table_name)
                    if lookup:
                        conditions = lookup(row, key_to_uuid)
                        if conditions:
                            existing = session.exec(
                                select(model).where(*conditions)
                            ).first()

                if existing:
                    for field in fields:
                        val = _normalize(
                            model, field, parse_value(row.get(field, ""), field)
                        )
                        if val is not None:
                            setattr(existing, field, val)
                    for csv_col, model_col in fk_map.items():
                        ref_key = row.get(csv_col, "")
                        if ref_key:
                            setattr(existing, model_col, key_to_uuid.get(ref_key))
                    stats[table_name]["updated"] += 1
                else:
                    kwargs = {"id": record_key}
                    for field in fields:
                        kwargs[field] = parse_value(row.get(field, ""), field)
                    for csv_col, model_col in fk_map.items():
                        ref_key = row.get(csv_col, "")
                        if ref_key:
                            kwargs[model_col] = key_to_uuid.get(ref_key)
                            if kwargs[model_col] is None:
                                print(
                                    f"  [WARN] {table_name}:{key} references unknown "
                                    f"{csv_col}={ref_key}"
                                )
                    session.add(model(**kwargs))
                    stats[table_name]["inserted"] += 1

            session.flush()
            print(
                f"  [OK] {table_name}: {stats[table_name]['inserted']} inserted, "
                f"{stats[table_name]['updated']} updated, "
                f"{stats[table_name]['skipped']} skipped"
            )

        # ── Enrich blogs with authors and publish dates ───────────────
        if "blog" in stats and stats["blog"]["inserted"] > 0:
            blogs = session.exec(select(Blog)).all()
            authors = [
                user_by_email["admin@example.com"],
                user_by_email["john@example.com"],
            ]
            for i, blog in enumerate(blogs):
                if blog.author_id is None:
                    blog.author_id = authors[i % 2].id
                if blog.published_at is None:
                    blog.published_at = datetime(2026, 2, 20 + (i % 9), 10, 0, 0)
                session.add(blog)
            session.flush()

        # ── User trips + itineraries from user_trip.csv ───────────────
        if (DATA_DIR / "user_trip.csv").exists():
            trip_rows = load_csv(str(DATA_DIR / "user_trip.csv"))
            itinerary_rows = load_csv(str(DATA_DIR / "destination_itinerary.csv"))
            for row in trip_rows:
                trip_key = row["key"]
                trip_uuid = generate_uuid(trip_key)
                if exists(session, UserTrip, trip_uuid):
                    stats["user_trips"]["skipped"] += 1
                    continue

                user = user_by_email.get(row["user_email"])
                if not user:
                    print(f"  [WARN] trip {trip_key}: unknown user {row['user_email']}")
                    continue

                trip = UserTrip(
                    id=trip_uuid,
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
                stats["user_trips"]["inserted"] += 1

                day_rows = [
                    it for it in itinerary_rows
                    if it["destination_key"] == row["destination_key"]
                ]
                for it in day_rows:
                    itin_uuid = generate_uuid(f"{trip_key}_day{it['day_number']}")
                    if exists(session, Itinerary, itin_uuid):
                        stats["itineraries"]["skipped"] += 1
                        continue
                    itinerary = Itinerary(
                        id=itin_uuid,
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
                    session.add(itinerary)
                    stats["itineraries"]["inserted"] += 1

            session.flush()
            print(
                f"  [OK] user_trips: {stats['user_trips']['inserted']} inserted, "
                f"{stats['user_trips']['skipped']} skipped"
            )
            print(
                f"  [OK] itineraries: {stats['itineraries']['inserted']} inserted, "
                f"{stats['itineraries']['skipped']} skipped"
            )

        # ── Photos: upsert one featured photo per destination ─────────
        john = user_by_email.get("john@example.com")
        admin = user_by_email.get("anusha@admin.com")
        uploader = admin or john

        if uploader:
            for dest_key, image_url in PHOTO_URLS.items():
                photo_uuid = generate_uuid(f"photo_{dest_key}")
                dest_uuid = key_to_uuid.get(dest_key)
                if not dest_uuid:
                    continue

                existing = session.get(Photo, photo_uuid)
                if existing:
                    # Ensure the existing photo is flagged as the featured one
                    if not existing.is_featured:
                        existing.is_featured = True
                    if not existing.image_url and image_url:
                        existing.image_url = image_url
                    if not existing.caption:
                        existing.caption = PHOTO_CAPTIONS.get(dest_key)
                    stats["photos"]["skipped"] += 1
                else:
                    photo = Photo(
                        id=photo_uuid,
                        destination_id=dest_uuid,
                        uploaded_by=uploader.id,
                        image_url=image_url,
                        caption=PHOTO_CAPTIONS.get(dest_key),
                        is_featured=True,
                    )
                    session.add(photo)
                    stats["photos"]["inserted"] += 1

            session.flush()
            print(
                f"  [OK] photos: {stats['photos']['inserted']} inserted, "
                f"{stats['photos']['skipped']} existing (featured flagged)"
            )

        # ── Reviews ───────────────────────────────────────────────────
        if john and admin:
            reviews_data = [
                ("rev_pashu_admin", admin.id, "dest_pashupatinath", 5,
                 "The evening aarti at the Bagmati ghats is unforgettable."),
                ("rev_mardi_john", john.id, "dest_mardi_himal_trek", 5,
                 "Easily the best quiet trek in the Annapurnas - barely any crowds."),
                ("rev_rara_admin", admin.id, "dest_rara", 5,
                 "Turquoise water and total silence. Worth every hour of travel."),
            ]
            for rev_key, user_id, dest_key, rating, comment in reviews_data:
                rev_uuid = generate_uuid(rev_key)
                if exists(session, Review, rev_uuid):
                    stats["reviews"]["skipped"] += 1
                    continue
                dest_uuid = key_to_uuid.get(dest_key)
                if not dest_uuid:
                    continue
                review = Review(
                    id=rev_uuid,
                    user_id=user_id,
                    destination_id=dest_uuid,
                    rating=rating,
                    comment=comment,
                )
                session.add(review)
                stats["reviews"]["inserted"] += 1

            session.flush()
            print(
                f"  [OK] reviews: {stats['reviews']['inserted']} inserted, "
                f"{stats['reviews']['skipped']} skipped"
            )

        # ── Final commit ──────────────────────────────────────────────
        session.commit()

    # ── Summary ──────────────────────────────────────────────────────
    print("\n=== Seed Summary ===")
    total_inserted = 0
    total_updated  = 0
    total_skipped  = 0
    for name, s in stats.items():
        if s["inserted"] or s["updated"] or s["skipped"]:
            print(
                f"  {name}: +{s['inserted']} inserted, "
                f"~{s['updated']} updated, "
                f"{s['skipped']} skipped (already existed)"
            )
            total_inserted += s["inserted"]
            total_updated  += s["updated"]
            total_skipped  += s["skipped"]
    print(
        f"\nTotal: {total_inserted} inserted, "
        f"{total_updated} updated from CSV, "
        f"{total_skipped} skipped"
    )
    print("Done!")


if __name__ == "__main__":
    main()
