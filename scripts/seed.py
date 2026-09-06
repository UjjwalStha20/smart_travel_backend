import os
import sys
from datetime import date, datetime, timezone
from decimal import Decimal

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
        Blog, DestinationItinerary, Itinerary, UserTrip, SavedDestination, Review, Photo,
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

        # ── ACCOMMODATIONS (UPDATED WITH NAME, DESCRIPTION, LOCATION) ──
        accom_budget = Accommodation(
            name="Basic Teahouse",
            description="Simple, clean rooms with shared bathrooms. Great for budget trekkers.",
            location="Tikhedhunga / Lower Ghorepani",
            budget_price=Decimal("10"),
            standard_price=Decimal("30"),
            luxury_price=Decimal("100")
        )
        accom_standard = Accommodation(
            name="Standard Lodge",
            description="Comfortable rooms with attached bathrooms and hot showers.",
            location="Ghorepani / Tadapani",
            budget_price=Decimal("20"),
            standard_price=Decimal("50"),
            luxury_price=Decimal("150")
        )
        accom_premium = Accommodation(
            name="Premium Mountain Lodge",
            description="Best available rooms at high altitude, heated dining room, and reliable hot water.",
            location="Annapurna Base Camp / High Altitude",
            budget_price=Decimal("50"),
            standard_price=Decimal("100"),
            luxury_price=Decimal("300")
        )
        session.add_all([accom_budget, accom_standard, accom_premium])

        # ── FOOD COSTS (UPDATED WITH NAME, CATEGORY) ──────────────────
        food_budget = FoodCost(
            name="Dal Bhat (Basic)",
            category="Main Meal",
            budget_price=Decimal("500"),
            standard_price=Decimal("1200"),
            luxury_price=Decimal("2500")
        )
        food_standard = FoodCost(
            name="Momos / Thukpa",
            category="Snack / Light Meal",
            budget_price=Decimal("100"),
            standard_price=Decimal("200"),
            luxury_price=Decimal("400")
        )
        food_premium = FoodCost(
            name="Hot Drinks / Snacks at High Altitude",
            category="Drink / Snack",
            budget_price=Decimal("150"),
            standard_price=Decimal("350"),
            luxury_price=Decimal("600")
        )
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
            best_time=["March", "April", "October", "November"],
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
            best_time=["March", "April", "October", "November"],
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

        # ── DESTINATION ITINERARIES ────────────────────────────────────────

        dest_itineraries = [
            DestinationItinerary(
                destination_id=dest_attraction.id, day_number=1,
                title="Sacred Temple Tour",
                start_location="Main Entrance", end_location="Bagmati River",
                overnight_location="Kathmandu",
                estimated_walking_hours=Decimal("2.5"),
                notes="Explore the main temple complex, observe evening aarti ceremony.",
            ),
            DestinationItinerary(
                destination_id=dest_trek.id, day_number=1,
                title="Nayapul to Tikhedhunga",
                start_location="Nayapul", end_location="Tikhedhunga",
                overnight_location="Tikhedhunga",
                estimated_walking_hours=Decimal("4"),
                notes="Easy start. Stay at teahouse in Tikhedhunga.",
            ),
            DestinationItinerary(
                destination_id=dest_trek.id, day_number=2,
                title="Tikhedhunga to Ghorepani",
                start_location="Tikhedhunga", end_location="Ghorepani",
                overnight_location="Ghorepani",
                estimated_walking_hours=Decimal("6"),
                notes="Steep climb up stone steps through rhododendron forest.",
            ),
            DestinationItinerary(
                destination_id=dest_trek.id, day_number=3,
                title="Ghorepani to Poon Hill & Tadapani",
                start_location="Ghorepani", end_location="Tadapani",
                overnight_location="Tadapani",
                estimated_walking_hours=Decimal("7"),
                notes="Early sunrise at Poon Hill (3,210m), then trek to Tadapani.",
            ),
            DestinationItinerary(
                destination_id=dest_trek.id, day_number=4,
                title="Tadapani to Machhapuchhre Base Camp",
                start_location="Tadapani", end_location="Machhapuchhre Base Camp",
                overnight_location="Machhapuchhre Base Camp",
                estimated_walking_hours=Decimal("6"),
                notes="Walk through dense forest with views of Machhapuchhre.",
            ),
            DestinationItinerary(
                destination_id=dest_trek.id, day_number=5,
                title="Machhapuchhre Base Camp to Annapurna Base Camp",
                start_location="Machhapuchhre Base Camp", end_location="Annapurna Base Camp",
                overnight_location="Annapurna Base Camp",
                estimated_walking_hours=Decimal("4"),
                notes="Arrive at ABC (4,130m). Surrounded by Annapurna massif.",
            ),
            DestinationItinerary(
                destination_id=dest_trek.id, day_number=6,
                title="Annapurna Base Camp to Bamboo",
                start_location="Annapurna Base Camp", end_location="Bamboo",
                overnight_location="Bamboo",
                estimated_walking_hours=Decimal("6"),
                notes="Descend through rhododendron and bamboo forests.",
            ),
            DestinationItinerary(
                destination_id=dest_trek.id, day_number=7,
                title="Bamboo to Nayapul",
                start_location="Bamboo", end_location="Nayapul",
                overnight_location="Pokhara",
                estimated_walking_hours=Decimal("5"),
                notes="Final descent back to Nayapul. Drive to Pokhara.",
            ),
        ]
        session.add_all(dest_itineraries)

        # ── BLOGS ──────────────────────────────────────────────────────────

        blogs = [
            Blog(
                title="10 Must-Visit Temples in Kathmandu Valley",
                slug="temples-kathmandu-valley",
                content="""<p class="text-lg font-medium text-slate-800 dark:text-slate-200">The Kathmandu Valley is home to some of the most remarkable religious architecture in the world. With seven UNESCO World Heritage Sites within a 15-kilometer radius, it is a paradise for history lovers and spiritual seekers alike.</p>
<p>From ancient stupas that date back over 1,500 years to intricately carved temple squares, each site tells a unique story of Nepal's rich cultural and religious heritage. Whether you are a devout pilgrim or a curious traveler, these sacred spaces offer a profound glimpse into the soul of the nation.</p>
<h2 class="text-xl lg:text-2xl font-bold text-slate-900 dark:text-white pt-4">1. Swayambhunath Stupa (Monkey Temple)</h2>
<p>Perched on a hilltop west of Kathmandu, Swayambhunath is one of the oldest religious sites in Nepal. The massive stupa with its all-seeing eyes of Buddha offers panoramic views of the valley.</p>
<h2 class="text-xl lg:text-2xl font-bold text-slate-900 dark:text-white pt-4">2. Boudhanath Stupa</h2>
<p>One of the largest spherical stupas in the world, Boudhanath is a focal point of Tibetan Buddhism in Nepal. The surrounding area is filled with monasteries and Tibetan craft shops.</p>
<h2 class="text-xl lg:text-2xl font-bold text-slate-900 dark:text-white pt-4">3. Pashupatinath Temple</h2>
<p>Located on the banks of the Bagmati River, Pashupatinath is one of the most sacred Hindu temples dedicated to Lord Shiva. The surrounding complex offers a fascinating glimpse into Hindu rituals.</p>""",
                excerpt="Discover the spiritual heart of Nepal through its most iconic temples and stupas, each with a story spanning centuries.",
                author_id=user_admin.id,
                featured_image="https://images.unsplash.com/photo-1594744803329-e58b31de8bf5?w=600&q=85",
                category="Culture",
                tags=["Temples", "Kathmandu", "Culture", "UNESCO", "Travel Guide"],
                is_published=True,
                published_at=datetime(2026, 3, 15, 10, 0, 0),
            ),
            Blog(
                title="Beginner's Guide to Trekking in Nepal",
                slug="beginners-guide-trekking",
                content="""<p>Nepal offers some of the world's most spectacular trekking routes, from the iconic Everest Base Camp trek to the lush Annapurna Circuit. If you are a first-time trekker, this guide will help you prepare for your adventure.</p>
<h2>Choosing Your Trek</h2>
<p>For beginners, the Poon Hill trek or Ghorepani loop is ideal — short duration, moderate elevation, and breathtaking sunrise views over the Annapurna and Dhaulagiri ranges.</p>
<h2>Permits</h2>
<p>Most treks require a TIMS card and a national park entry permit. Your trekking agency will usually arrange these for you.</p>
<h2>Packing Essentials</h2>
<p>A good pair of hiking boots, warm layers, a waterproof jacket, and a reliable sleeping bag are non-negotiable. Don't forget sunscreen and a first-aid kit.</p>""",
                excerpt="Everything you need to know before hitting the trails — from permits to packing lists and fitness tips.",
                author_id=user_admin.id,
                featured_image="https://images.unsplash.com/photo-1585409677983-0f6c41ca9c3b?w=600&q=85",
                category="Trekking",
                tags=["Trekking", "Beginners", "Nepal", "Hiking", "Adventure"],
                is_published=True,
                published_at=datetime(2026, 3, 10, 10, 0, 0),
            ),
            Blog(
                title="Best Street Food in Pokhara",
                slug="pokhara-street-food",
                content="""<p>Pokhara is not just about paragliding and lake views — it is also a fantastic destination for food lovers. From cozy lakeside cafes to bustling local eateries, here are the must-try foods.</p>
<h2>Dal Bhat</h2>
<p>The quintessential Nepali meal — steamed rice, lentil soup, vegetable curry, and pickles. It is served at nearly every restaurant and is both delicious and filling.</p>
<h2>Momos</h2>
<p>Steamed or fried dumplings stuffed with buffalo, chicken, or vegetables. Dip them in spicy tomato chutney for the full experience.</p>
<h2>Newari Khaja Set</h2>
<p>A traditional platter featuring beaten rice, spiced meat, boiled eggs, and black soybeans. A true taste of local cuisine.</p>""",
                excerpt="A food lover's tour of Pokhara's lakeside eateries, local dal bhat joints, and hidden culinary gems.",
                author_id=user_john.id,
                featured_image="https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=600&q=85",
                category="Food",
                tags=["Pokhara", "Food", "Street Food", "Nepali Cuisine"],
                is_published=True,
                published_at=datetime(2026, 3, 5, 10, 0, 0),
            ),
            Blog(
                title="Sustainable Travel Tips for Nepal",
                slug="sustainable-travel-nepal",
                content="""<p>As tourism in Nepal continues to grow, it is important to travel responsibly. Here are some simple ways to minimize your impact while supporting local communities.</p>
<h2>Choose Eco-Friendly Accommodations</h2>
<p>Many teahouses and hotels in Nepal are adopting sustainable practices—solar power, water purification, and waste management. Look for eco-certified lodgings.</p>
<h2>Reduce Plastic Waste</h2>
<p>Bring a reusable water bottle with a built-in filter. Many trekking areas have refill stations, reducing the need for single-use plastic bottles.</p>
<h2>Support Local Businesses</h2>
<p>Eat at local restaurants, hire local guides, and buy souvenirs from artisan cooperatives rather than mass-produced imports.</p>""",
                excerpt="How to minimize your environmental impact while supporting local communities during your travels.",
                author_id=user_john.id,
                featured_image="https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&q=85",
                category="Travel Tips",
                tags=["Sustainable", "Eco Travel", "Nepal", "Responsible Tourism"],
                is_published=True,
                published_at=datetime(2026, 2, 28, 10, 0, 0),
            ),
            Blog(
                title="Chitwan National Park: A Wildlife Guide",
                slug="chitwan-wildlife-guide",
                content="""<p>Chitwan National Park is a UNESCO World Heritage Site and one of Asia's best wildlife destinations. Located in the subtropical lowlands of southern Nepal, it offers incredible biodiversity.</p>
<h2>What You Will See</h2>
<p>The park is famous for its one-horned rhinoceros, Bengal tigers, and over 500 species of birds. Elephant safaris and jeep tours offer the best chances for wildlife spotting.</p>
<h2>Best Time to Visit</h2>
<p>The dry season from October to March offers the best wildlife viewing, as animals congregate around water sources. The weather is pleasant and leeches are minimal.</p>
<h2>Getting There</h2>
<p>Chitwan is a 5-hour drive from Kathmandu or Pokhara. Regular tourist buses and private transfers are available.</p>""",
                excerpt="Spot rhinos, tigers, and exotic birds in Nepal's most famous national park. Your complete safari guide.",
                author_id=user_admin.id,
                featured_image="https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?w=600&q=85",
                category="Wildlife",
                tags=["Chitwan", "Wildlife", "Safari", "National Park", "Nature"],
                is_published=True,
                published_at=datetime(2026, 2, 20, 10, 0, 0),
            ),
            Blog(
                title="Festivals of Nepal: A Year-Round Calendar",
                slug="nepal-festivals-calendar",
                content="""<p>Nepal is a land of festivals, with celebrations happening almost every month. From the vibrant colors of Holi to the solemn beauty of Tihar, here is a guide to the major festivals.</p>
<h2>Dashain (September-October)</h2>
<p>The biggest and longest festival in Nepal, lasting 15 days. Families reunite, receive blessings from elders, and celebrate with feasts and flying kites.</p>
<h2>Tihar (October-November)</h2>
<p>The festival of lights, dedicated to worshiping crows, dogs, cows, and oxen. Homes are decorated with oil lamps and marigold garlands.</p>
<h2>Holi (March)</h2>
<p>The festival of colors is celebrated with great enthusiasm. People throw colored powder and water at each other, dance in the streets, and share sweets.</p>""",
                excerpt="From Dashain to Holi, plan your trip around Nepal's vibrant festivals and cultural celebrations.",
                author_id=user_admin.id,
                featured_image="https://images.unsplash.com/photo-1587474260584-136574528ed5?w=600&q=85",
                category="Culture",
                tags=["Festivals", "Culture", "Nepal", "Dashain", "Tihar", "Holi"],
                is_published=True,
                published_at=datetime(2026, 2, 14, 10, 0, 0),
            ),
        ]
        session.add_all(blogs)

        session.commit()

    print("Done! Seed data inserted across all tables.")


if __name__ == "__main__":
    main()