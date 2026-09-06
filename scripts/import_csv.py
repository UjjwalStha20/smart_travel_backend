import csv
import json
import os
import sys
import uuid
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
    Permit,
    RoutePoint,
    TrekkingRoute,
)
from sqlmodel import Session, delete

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CSV_CONFIG = {
    "address": {
        "model": Address,
        "file": "address.csv",
        "fields": ["province", "district", "place", "latitude", "longitude", "altitude"],
        "fk_map": {},
    },
    "accommodation": {
        "model": Accommodation,
        "file": "accommodation.csv",
        # ✅ UPDATED: Added name, description, and location
        "fields": ["name", "description", "location", "budget_price", "standard_price", "luxury_price"],
        "fk_map": {},
    },
    "food_cost": {
        "model": FoodCost,
        "file": "food_cost.csv",
        # ✅ UPDATED: Added name and category
        "fields": ["name", "category", "budget_price", "standard_price", "luxury_price"],
        "fk_map": {},
    },
    "destination": {
        "model": Destination,
        "file": "destination.csv",
        "fields": ["name", "category", "description", "best_time", "permit_required", "rating"],
        "fk_map": {"address_key": "address_id"},
    },
    "attraction": {
        "model": Attraction,
        "file": "attraction.csv",
        "fields": ["attraction_types", "opening_hours", "visit_duration_hours"],
        "fk_map": {"destination_key": "destination_id"},
    },
    "entry_fee": {
        "model": EntryFee,
        "file": "entry_fee.csv",
        "fields": ["category", "price"],
        "fk_map": {"attraction_key": "attraction_id"},
    },
    "permit": {
        "model": Permit,
        "file": "permit.csv",
        "fields": ["permit_type","category", "price"],
        "fk_map": {"destination_key": "destination_id"},
    },
    "trekking_routes": {
        "model": TrekkingRoute,
        "file": "trekking_route.csv",
        "fields": ["route_name", "difficulty", "total_distance_km", "recommended_days", "max_altitude", "description"],
        "fk_map": {"destination_key": "destination_id"},
    },
    "blog": {
        "model": Blog,
        "file": "blog.csv",
        "fields": ["title", "slug", "content", "excerpt", "category", "tags", "is_published", "featured_image"],
        "fk_map": {},
    },
    "destination_itinerary": {
        "model": DestinationItinerary,
        "file": "destination_itinerary.csv",
        "fields": ["day_number", "title", "start_location", "end_location", "overnight_location", "estimated_walking_hours", "notes"],
        "fk_map": {"destination_key": "destination_id"},
    },
    "route_points": {
        "model": RoutePoint,
        "file": "route_point.csv",
        "fields": ["sequence_no", "name", "distance_from_previous_km", "walking_hours_from_previous", "overnight_stop", "description"],
        "fk_map": {
            "route_key": "route_id",
            "address_key": "address_id",
            "accommodation_key": "accommodation_id",
            "food_cost_key": "food_cost_id",
        },
    },
}
def clear_all(session: Session):
    tables = [
        Blog, DestinationItinerary, RoutePoint, Permit, EntryFee, TrekkingRoute,
        Attraction, Destination, Address, Accommodation, FoodCost,
    ]
    for table in tables:
        session.exec(delete(table))
    session.commit()


def load_csv(filepath: str):
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def generate_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, key)


SEASON_MONTHS = {
    "spring": ["March", "April", "May"],
    "summer": ["June", "July", "August"],
    "autumn": ["September", "October", "November"],
    "winter": ["December", "January", "February"],
}


def expand_seasons_to_months(values):
    """Expand season keywords (spring/autumn/winter/summer) into month names."""
    if not values:
        return values
    expanded = []
    for v in values:
        key = v.strip().lower()
        expanded.extend(SEASON_MONTHS.get(key, [v]))
    return expanded


def parse_value(value: str, field_name: str):
    if value == "" or value is None:
        return None
    if field_name in ("latitude", "longitude", "altitude"):
        return float(value) if value else None
    if field_name in ("rating", "sequence_no", "recommended_days", "max_altitude", "day_number"):
        return int(value) if value else None
    if field_name in (
        "budget_price", "standard_price", "luxury_price", "price",
        "total_distance_km", "walking_hours_from_previous", "visit_duration_hours",
    ):
        return Decimal(value) if value else None
    if field_name in ("permit_required", "overnight_stop", "is_published"):
        return value.lower() == "true"
    if field_name in ("best_time", "attraction_types", "tags"):
        parsed = json.loads(value) if value else None
        if field_name == "best_time":
            return expand_seasons_to_months(parsed)
        return parsed
    return value


def main():
    print("Importing CSV data into database...")

    init_db()
    key_to_uuid = {}

    with Session(engine) as session:
        clear_all(session)

        for table_name, config in CSV_CONFIG.items():
            filepath = DATA_DIR / config["file"]
            if not filepath.exists():
                print(f"  [SKIP] {filepath} not found")
                continue

            rows = load_csv(str(filepath))
            model = config["model"]
            fields = config["fields"]
            fk_map = config["fk_map"]

            objects = []
            for row in rows:
                key = row["key"]
                record_key = generate_uuid(key)
                key_to_uuid[key] = record_key

                kwargs = {"id": record_key}
                for field in fields:
                    kwargs[field] = parse_value(row.get(field, ""), field)

                for csv_col, model_col in fk_map.items():
                    ref_key = row.get(csv_col, "")
                    if ref_key:
                        kwargs[model_col] = key_to_uuid.get(ref_key)
                        if kwargs[model_col] is None:
                            print(
                                f"  [WARN] {table_name}:{key} references "
                                f"{csv_col}={ref_key} which was not found"
                            )

                obj = model(**kwargs)
                objects.append(obj)

            session.add_all(objects)
            session.commit()
            print(f"  [OK] {table_name}: imported {len(objects)} rows")

    print()
    print("Data import complete!")
    print()
    print("Summary:")
    for table_name, config in CSV_CONFIG.items():
        filepath = DATA_DIR / config["file"]
        if filepath.exists():
            rows = load_csv(str(filepath))
            fk_refs = list(config["fk_map"].values())
            refs_str = f" (FK: {', '.join(fk_refs)})" if fk_refs else ""
            print(f"  {table_name}: {len(rows)} rows{refs_str}")


if __name__ == "__main__":
    main()
