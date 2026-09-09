"""Informational flight / how-to-reach data for Nepal destinations.

This is curation data (airport, airlines, typical duration/fare, booking portals)
so the app can *guide* users on how to book — it does not perform any booking.
"""
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session

from app.models import Address, Destination

KATHMANDU_OPTIONS = ["https://www.buddhaair.com", "https://www.yetiairlines.com", "https://www.shreeair.com", "https://simrikairlines.com"]

AIRPORTS = [
    {
        "airport_code": "KTM",
        "airport_name": "Tribhuvan International Airport",
        "city": "Kathmandu",
        "is_international": True,
        "domestic_airlines": ["Buddha Air", "Yeti Airlines", "Shree Airlines", "Simrik Air"],
        "booking_urls": KATHMANDU_OPTIONS,
        "note": "Nepal's only international gateway. Most foreign visitors fly into KTM.",
        "keywords": [
            "kathmandu", "bhaktapur", "patan", "lalitpur", "pashupatinath", "boudhanath",
            "swayambhunath", "nagarkot", "chandragiri", "bagmati", "pharping", "kirtipur",
            "dakshinkali", "gosaikunda", "langtang", "syabrubesi", "rasuwa",
        ],
    },
    {
        "airport_code": "PKR",
        "airport_name": "Pokhara International Airport",
        "city": "Pokhara",
        "is_international": False,
        "domestic_airlines": ["Buddha Air", "Yeti Airlines", "Shree Airlines", "Simrik Air"],
        "booking_urls": KATHMANDU_OPTIONS,
        "duration_minutes": 30,
        "approx_fare_npr": "NPR 9,000 - 14,000 one-way",
        "note": "Gateway to the Annapurna & Poon Hill region; ~30 min flight from KTM, then drive to trailheads.",
        "keywords": [
            "pokhara", "kaski", "annapurna", "poon hill", "ghorepani", "bandipur", "tanahun",
            "phewa", "nayapul", "tadapani", "chhomrong", "mustang", "jomsom", "manakamana", "gorkha",
        ],
    },
    {
        "airport_code": "LUA",
        "airport_name": "Tenzing-Hillary Airport (Lukla)",
        "city": "Lukla",
        "is_international": False,
        "domestic_airlines": ["Yeti Airlines", "Summit Air"],
        "booking_urls": ["https://www.yetiairlines.com", "https://www.summitair.com.np"],
        "duration_minutes": 30,
        "approx_fare_npr": "USD 130 - 180 one-way",
        "note": "World-famous short runway; starting point for Everest / EBC treks.",
        "keywords": [
            "lukla", "khumbu", "namche", "everest", "sagarmatha", "ebc", "solukhumbu",
            "gorakshep", "dingboche", "lobuche", "tyangboche", "phakding",
        ],
    },
    {
        "airport_code": "BWA",
        "airport_name": "Gautam Buddha International Airport",
        "city": "Bhairahawa",
        "is_international": False,
        "domestic_airlines": ["Buddha Air", "Yeti Airlines", "Shree Airlines", "Simrik Air"],
        "booking_urls": KATHMANDU_OPTIONS,
        "duration_minutes": 35,
        "approx_fare_npr": "NPR 8,000 - 12,000 one-way",
        "note": "Closest airport to Lumbini (birthplace of Buddha), ~30 min drive.",
        "keywords": ["lumbini", "rupandehi", "bhairahawa"],
    },
    {
        "airport_code": "BHR",
        "airport_name": "Bharatpur Airport",
        "city": "Bharatpur",
        "is_international": False,
        "domestic_airlines": ["Shree Airlines", "Simrik Air"],
        "booking_urls": ["https://www.shreeair.com", "https://simrikairlines.com"],
        "duration_minutes": 25,
        "approx_fare_npr": "NPR 7,000 - 10,000 one-way",
        "note": "Closest airport to Chitwan National Park (Sauraha).",
        "keywords": ["chitwan", "bharatpur", "sauraha"],
    },
    {
        "airport_code": "JKR",
        "airport_name": "Janakpur Airport",
        "city": "Janakpur",
        "is_international": False,
        "domestic_airlines": ["Buddha Air", "Summit Air"],
        "booking_urls": KATHMANDU_OPTIONS,
        "duration_minutes": 30,
        "approx_fare_npr": "NPR 7,500 - 11,000 one-way",
        "note": "Gateway to Janaki Mandir and the Mithila region.",
        "keywords": ["janakpur", "dhanusha", "janaki", "maithili"],
    },
]


def get_flight_options(session: Session, destination_id) -> dict:
    destination = session.get(Destination, UUID(str(destination_id)))
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")

    address: Optional[Address] = None
    if destination.address_id:
        address = session.get(Address, destination.address_id)

    haystack = " ".join(
        filter(
            None,
            [
                destination.name,
                destination.description or "",
                address.province if address else None,
                address.district if address else None,
                address.place if address else None,
            ],
        )
    ).lower()

    ranked = []
    for airport in AIRPORTS:
        hits = sum(1 for kw in airport["keywords"] if kw in haystack)
        if hits:
            ranked.append((hits, airport))
    ranked.sort(key=lambda item: item[0], reverse=True)
    options = [ap for _, ap in ranked]

    how_to_reach = None
    if options:
        primary = options[0]
        if primary["airport_code"] == "KTM":
            how_to_reach = f"{destination.name} is accessible from Kathmandu (KTM): domestic flights, tourist buses or private vehicles for most destinations."
        elif primary["airport_code"] == "PKR":
            how_to_reach = "Fly Kathmandu (KTM) → Pokhara (PKR) (~30 min), then continue by local jeep/bus or taxi to the trailhead."
        elif primary["airport_code"] == "LUA":
            how_to_reach = "Fly Kathmandu (KTM) → Lukla (LUA) (~30 min) to start the trek; weather makes flights schedule-dependent."
        else:
            how_to_reach = f"Fly from Kathmandu (KTM) to {primary['airport_name']} ({primary['airport_code']}), then continue by road to {destination.name}."

    return {
        "destination": destination.name,
        "category": destination.category.value,
        "coordinate_hint": (
            f"{address.latitude:.4f}, {address.longitude:.4f}" if address and address.latitude is not None else None
        ),
        "general_tip": (
            "Prices are indicative, not live. Always confirm fares and schedules on the airline "
            "websites or a travel agency before booking."
        ),
        "options": options,
        "how_to_reach": how_to_reach,
    }