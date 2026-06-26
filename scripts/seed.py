from datetime import date, datetime, timezone
from decimal import Decimal

from app.core.db import engine, init_db
from app.core.security import hash_password
from app.models import (
    Accommodation,
    Address,
    Attraction,
    Destination,
    EntryFee,
    FoodCost,
    Itinerary,
    Permit,
    Photo,
    Review,
    RoutePoint,
    SavedDestination,
    TrekkingRoute,
    User,
    UserTrip,
)
from sqlmodel import Session, delete, select


def clear_all(session: Session):
    tables = [
        Itinerary, UserTrip, SavedDestination, Review, Photo,
        Permit, EntryFee, RoutePoint, TrekkingRoute,
        Attraction, Destination, Address, Accommodation, FoodCost, User,
    ]
    for table in tables:
        session.exec(delete(table))
    session.commit()


def main():
    print("Seeding database...")

    with Session(engine) as session:
        clear_all(session)

        # ── BASE DATA ──────────────────────────────────────────────

        addr_kathmandu = Address(
            province="Bagmati", district="Kathmandu",
            place="Kathmandu", latitude=27.7172, longitude=85.3240, altitude=1400,
        )
        addr_pokhara = Address(
            province="Gandaki", district="Kaski",
            place="Pokhara", latitude=28.2096, longitude=83.9856, altitude=822,
        )
        addr_nayapul = Address(
            province="Gandaki", district="Kaski",
            place="Nayapul", latitude=28.3167, longitude=83.8167, altitude=1070,
        )
        addr_tikhedhunga = Address(
            province="Gandaki", district="Myagdi",
            place="Tikhedhunga", latitude=28.3667, longitude=83.7833, altitude=1540,
        )
        addr_ghorepani = Address(
            province="Gandaki", district="Myagdi",
            place="Ghorepani", latitude=28.4000, longitude=83.7333, altitude=2874,
        )
        session.add_all([addr_kathmandu, addr_pokhara, addr_nayapul,
                         addr_tikhedhunga, addr_ghorepani])

        accom_budget = Accommodation(budget_price=Decimal("10"),
                                      standard_price=Decimal("30"),
                                      luxury_price=Decimal("100"))
        accom_standard = Accommodation(budget_price=Decimal("20"),
                                        standard_price=Decimal("50"),
                                        luxury_price=Decimal("150"))
        accom_premium = Accommodation(budget_price=Decimal("50"),
                                       standard_price=Decimal("100"),
                                       luxury_price=Decimal("300"))
        session.add_all([accom_budget, accom_standard, accom_premium])

        food_budget = FoodCost(budget_price=Decimal("500"),
                                standard_price=Decimal("1200"),
                                luxury_price=Decimal("2500"))
        food_standard = FoodCost(budget_price=Decimal("100"),
                                  standard_price=Decimal("200"),
                                  luxury_price=Decimal("400"))
        food_premium = FoodCost(budget_price=Decimal("150"),
                                 standard_price=Decimal("350"),
                                 luxury_price=Decimal("600"))
        session.add_all([food_budget, food_standard, food_premium])

        user_john = User(
            name="John Doe", role="traveler",
            email="john@example.com", password=hash_password("password123"),
            nationality="USA", phone="+977-9800000001",
        )
        user_admin = User(
            name="Admin User", role="admin",
            email="admin@example.com", password=hash_password("admin123"),
            nationality="Nepal", phone="+977-9800000002",
        )
        session.add_all([user_john, user_admin])
        session.flush()

        # ── ATTRACTION DESTINATION: Pashupatinath Temple ──────────

        dest_attraction = Destination(
            name="Pashupatinath Temple", category="attraction",
            description=(
                "One of the most sacred Hindu temples dedicated to Lord Shiva, "
                "located on the banks of the Bagmati River. A UNESCO World "
                "Heritage Site and a major pilgrimage destination."
            ),
            best_time=["spring", "autumn"],
            permit_required=False, rating=5,
            address_id=addr_kathmandu.id,
        )
        session.add(dest_attraction)
        session.flush()

        attr_pashu = Attraction(
            destination_id=dest_attraction.id,
            attraction_types=["temple", "heritage"],
            opening_hours="6:00 AM - 8:00 PM",
            visit_duration_hours=Decimal("2.5"),
        )
        session.add(attr_pashu)
        session.flush()

        entry_fees = [
            EntryFee(attraction_id=attr_pashu.id, category="Nepali",
                     price=Decimal("500")),
            EntryFee(attraction_id=attr_pashu.id, category="SAARC",
                     price=Decimal("1000")),
            EntryFee(attraction_id=attr_pashu.id, category="Foreign",
                     price=Decimal("2000")),
            EntryFee(attraction_id=attr_pashu.id, category="Nepali",
                     price=Decimal("250")),
            EntryFee(attraction_id=attr_pashu.id, category="SAARC",
                     price=Decimal("500")),
            EntryFee(attraction_id=attr_pashu.id, category="Foreign",
                     price=Decimal("1000")),
        ]
        session.add_all(entry_fees)

        photo_pashu = Photo(
            destination_id=dest_attraction.id,
            uploaded_by=user_john.id,
            image_url="https://images.example.com/pashupatinath.jpg",
            caption="The majestic Pashupatinath Temple at sunset",
        )
        session.add(photo_pashu)

        review_pashu = Review(
            user_id=user_john.id, destination_id=dest_attraction.id,
            rating=5, comment="Incredible spiritual experience. "
            "The evening aarti ceremony is unforgettable.",
        )
        session.add(review_pashu)

        # ── TREK DESTINATION: Annapurna Base Camp ──────────────────

        dest_trek = Destination(
            name="Annapurna Base Camp Trek", category="trek",
            description=(
                "One of Nepal's most popular trekking routes, taking you "
                "through lush rhododendron forests, traditional Gurung "
                "villages, and up to the heart of the Annapurna Sanctuary "
                "at 4,130m with breathtaking mountain views."
            ),
            best_time=["march", "april", "october", "november"],
            permit_required=True, rating=5,
            address_id=addr_pokhara.id,
        )
        session.add(dest_trek)
        session.flush()

        route_abc = TrekkingRoute(
            destination_id=dest_trek.id,
            route_name="Annapurna Base Camp",
            difficulty="moderate",
            total_distance_km=Decimal("115"),
            recommended_days=8,
            max_altitude=4130,
            description=(
                "Classic trek from Nayapul through Ghorepani and Poon Hill, "
                "ending at the Annapurna Sanctuary."
            ),
        )
        session.add(route_abc)
        session.flush()

        abc_route_points = [
            RoutePoint(
                route_id=route_abc.id, sequence_no=1,
                name="Nayapul", distance_from_previous_km=Decimal("0"),
                walking_hours_from_previous=Decimal("0"),
                overnight_stop=False, description="Trek starting point",
                address_id=addr_nayapul.id,
            ),
            RoutePoint(
                route_id=route_abc.id, sequence_no=2,
                name="Tikhedhunga",
                distance_from_previous_km=Decimal("8"),
                walking_hours_from_previous=Decimal("4"),
                overnight_stop=True,
                description="Small village with teahouses",
                address_id=addr_tikhedhunga.id,
                accommodation_id=accom_budget.id,
                food_cost_id=food_budget.id,
            ),
            RoutePoint(
                route_id=route_abc.id, sequence_no=3,
                name="Ghorepani",
                distance_from_previous_km=Decimal("12"),
                walking_hours_from_previous=Decimal("6"),
                overnight_stop=True,
                description="Popular stop with panoramic views",
                address_id=addr_ghorepani.id,
                accommodation_id=accom_standard.id,
                food_cost_id=food_standard.id,
            ),
            RoutePoint(
                route_id=route_abc.id, sequence_no=4,
                name="Poon Hill Viewpoint",
                distance_from_previous_km=Decimal("5"),
                walking_hours_from_previous=Decimal("2"),
                overnight_stop=False,
                description="Sunrise viewpoint at 3,210m",
                address_id=addr_ghorepani.id,
                accommodation_id=accom_standard.id,
                food_cost_id=food_standard.id,
            ),
            RoutePoint(
                route_id=route_abc.id, sequence_no=5,
                name="Annapurna Base Camp",
                distance_from_previous_km=Decimal("15"),
                walking_hours_from_previous=Decimal("7"),
                overnight_stop=True,
                description="Base camp at 4,130m surrounded by peaks",
                address_id=addr_pokhara.id,
                accommodation_id=accom_premium.id,
                food_cost_id=food_premium.id,
            ),
        ]
        session.add_all(abc_route_points)

        permits = [
            Permit(destination_id=dest_trek.id, category="Nepali",
                   price=Decimal("100")),
            Permit(destination_id=dest_trek.id, category="Foreign",
                   price=Decimal("3000")),
        ]
        session.add_all(permits)

        photo_abc = Photo(
            destination_id=dest_trek.id,
            uploaded_by=user_admin.id,
            image_url="https://images.example.com/abc-sanctuary.jpg",
            caption="Annapurna South from the sanctuary",
        )
        session.add(photo_abc)

        review_abc = Review(
            user_id=user_admin.id, destination_id=dest_trek.id,
            rating=5, comment="Best trek I've ever done. "
            "The views of Annapurna massif are absolutely stunning.",
        )
        session.add(review_abc)

        # ── SOCIAL ─────────────────────────────────────────────────

        saved = [
            SavedDestination(user_id=user_john.id,
                             destination_id=dest_attraction.id),
            SavedDestination(user_id=user_john.id,
                             destination_id=dest_trek.id),
        ]
        session.add_all(saved)

        trip = UserTrip(
            user_id=user_john.id, destination_id=dest_trek.id,
            route_id=route_abc.id, pace_type="normal",
            budget_type="standard",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 8),
            status="planned",
        )
        session.add(trip)
        session.flush()

        itineraries = [
            Itinerary(
                trip_id=trip.id, day_number=1,
                start_location="Nayapul", end_location="Tikhedhunga",
                overnight_location="Tikhedhunga",
                estimated_walking_hours=Decimal("4"),
                notes="Easy start. Stay at teahouse in Tikhedhunga.",
            ),
            Itinerary(
                trip_id=trip.id, day_number=2,
                start_location="Tikhedhunga", end_location="Ghorepani",
                overnight_location="Ghorepani",
                estimated_walking_hours=Decimal("6"),
                notes="Steep climb up stone steps. Rhododendron forest.",
            ),
            Itinerary(
                trip_id=trip.id, day_number=3,
                start_location="Ghorepani", end_location="Poon Hill",
                overnight_location="Ghorepani",
                estimated_walking_hours=Decimal("2"),
                notes="Early morning hike to Poon Hill for sunrise over "
                      "Annapurna and Dhaulagiri ranges.",
            ),
        ]
        session.add_all(itineraries)

        session.commit()

    print("Done! Seed data inserted across all tables.")
    print()
    print("Users:")
    print("  john@example.com / password123  (traveler)")
    print("  admin@example.com / admin123    (admin)")
    print()
    print(f"  Attraction destination: Pashupatinath Temple")
    print(f"  Trek destination:       Annapurna Base Camp Trek")


if __name__ == "__main__":
    main()
