"""Lightweight, deterministic intent classification for the travel chatbot.

This module intentionally does NOT call the LLM. It uses keyword/regex rules
so that simple messages ("hello", "how are you?", "thanks") are classified
instantly and routed to a fast response path instead of a slow model call.

Intent categories (see project spec §6):
    GENERAL_CONVERSATION, NEPAL_GENERAL, DESTINATION, ITINERARY, TREKKING,
    PERMITS, BUDGET, TRANSPORT, ACCOMMODATION, FOOD, CULTURE, RELIGION,
    NATURE, WEATHER, TRIP_MODIFICATION, TRIP_SPECIFIC, RECOMMENDATION, OUT_OF_SCOPE
"""

import re
from typing import Optional

GENERAL_CONVERSATION = "GENERAL_CONVERSATION"
NEPAL_GENERAL = "NEPAL_GENERAL"
DESTINATION = "DESTINATION"
ITINERARY = "ITINERARY"
TREKKING = "TREKKING"
PERMITS = "PERMITS"
BUDGET = "BUDGET"
TRANSPORT = "TRANSPORT"
ACCOMMODATION = "ACCOMMODATION"
FOOD = "FOOD"
CULTURE = "CULTURE"
RELIGION = "RELIGION"
NATURE = "NATURE"
WEATHER = "WEATHER"
TRIP_MODIFICATION = "TRIP_MODIFICATION"
TRIP_SPECIFIC = "TRIP_SPECIFIC"
RECOMMENDATION = "RECOMMENDATION"
OUT_OF_SCOPE = "OUT_OF_SCOPE"

ALL_INTENTS = (
    GENERAL_CONVERSATION,
    NEPAL_GENERAL,
    DESTINATION,
    ITINERARY,
    TREKKING,
    PERMITS,
    BUDGET,
    TRANSPORT,
    ACCOMMODATION,
    FOOD,
    CULTURE,
    RELIGION,
    NATURE,
    WEATHER,
    TRIP_MODIFICATION,
    TRIP_SPECIFIC,
    RECOMMENDATION,
    OUT_OF_SCOPE,
)

# ---------------------------------------------------------------------------
# Regex rules (ordered: most specific first).
# ---------------------------------------------------------------------------

_GREETINGS = re.compile(
    r"^\s*(hi+|hey+|hello+|howdy|namaste|hallo|yo|good (morning|afternoon|evening))\b",
    re.I,
)
_THANKS = re.compile(
    r"^(thanks|thank you|thank you so much|thx|appreciate(d)? (it|that)|cheers|nice)",
    re.I,
)
_SMALLTALK = re.compile(
    r"\b(how are you|how's it (going|hanging)|what'?s up|who are you|what can you do|"
    r"are you (real|human|a bot)|what is your name|nice to meet you|you( are|\'re) (great|awesome|helpful))\b",
    re.I,
)

_OUT_OF_SCOPE = re.compile(
    r"\b(thailand|india(?!n ocean)|bhutan|tibet|china|japan|europe|america|usa|uk\b|england|"
    r"france|germany|italy|spain|australia|canada|switzerland|paris|london|new york|tokyo|"
    r"bali|malaysia|singapore|vietnam|cambodia|laos|maldives|sri lanka|bangladesh|pakistan|"
    r"myanmar|south korea|dubai|qatar|saudi|hollywood|disneyland)\b",
    re.I,
)

_WEATHER = re.compile(
    r"\b(weather|temperature(s)?|cold|hot|rain(y|fall|ing)?|monsoon|snow|forecast|humid|"
    r"season(s)?" + r"|winter|summer|spring|autumn|when to visit|best time|°c|degrees)\b",
    re.I,
)

_TREKKING = re.compile(
    r"\b(trek(s|king|ker|ers)?|hike(s|ing)?|hiking trail(s)?" + r"|annapurna|everest base camp|"
    r"abc\b|poon hill|langtang|manaslu|mustang|khopra|mardi|helambu|gorakshep|nagarkot|acclimat)",
    re.I,
)

_PERMITS = re.compile(
    r"\b(permit(s|ing|ed)?|tims|acap|sagarmatha|mcap|entry fees?|restricted area|"
    r"pass required|customs|visas?)\b",
    re.I,
)

_BUDGET = re.compile(
    r"\b(budget(s|ed|ing)?|cost(s|ing)?|price(s|d)?|cheap(er|est)?|expensive|how much|afford|"
    r"save money|rupee(s)?|npr|usd|fare(s)?|fee(s|x)?|spend(s|ing|t)?)\b",
    re.I,
)

_TRANSPORT = re.compile(
    r"\b(flight(s)?|bus(es)?|taxi(s)?|car(s)?|motorbike(s)?|bike(s)?|train(s)?|ferry|"
    r"ride(s)?|transport(ation)?|how (do|can) i get|how to (get|reach|travel|go)|"
    r"airport(s)?|ticket(s)?|domestic|drive|walk(s|ing)?)\b",
    re.I,
)

_ACCOMMODATION = re.compile(
    r"\b(hotel(s)?|lodge(s)?|stays?|accommodat(ion|ions)?|teahouse(s)?|hostel(s)?|homestay(s)?|"
    r"resort(s)?|room(s)?|guesthouse(s)?|sleep(ing)?)\b",
    re.I,
)

_FOOD = re.compile(
    r"\b(eat(s|ing)?|food(s)?|meal(s)?|dal bhat|momo(s)?|thukpa|curry|restaurant(s)?|diet|"
    r"veg(etarian)?|vegan|breakfast|lunch(es)?|dinner|café(s)?|caffe?(s)?|snack(s)?|"
    r"drink(s|ing)?|taste|cuisine)\b",
    re.I,
)

_CULTURE = re.compile(
    r"\b(culture|cultural|festival(s)?|tradition(s)?|dance(s)?|music|art(s)?|handicraft(s)?|"
    r"new year|losar|dashain|tihar|holi|indrajatra|etiquette)\b",
    re.I,
)

_RELIGION = re.compile(
    r"\b(religious|temple(s)?|stupa(s)?|monaster(y|ies)|gumba(s)?|prayer(s)?|buddhist|hindu|shrine(s)?|"
    r"pilgrimage|mantra(s)?|puja|heritage|boudha|swayambhu|pashupati|lumbini|god(s)?|deit(y|ies))\b",
    re.I,
)

_NATURE = re.compile(
    r"\b(nature|mountain(s)?|lake(s)?|river(s)?|forest(s)?|jungle(s)?|wildlife|national park(s)?|"
    r"bird(s)?|flower(s)?|rhododendron|viewpoint(s)?|sunrise|landscape(s)?|scenic|"
    r"garden(s)?|valley(s)?|peak(s)?)\b",
    re.I,
)

_DESTINATION = re.compile(
    r"\b(visit|see|do|go|places?|destinations?|kathmandu|pokhara|chitwan|bandipur|gorkha|lumbini|"
    r"bhaktapur|patan|janakpur|ilam|rara|jomsom|manang|mustang|tansen|palpa|nagarkot|dhulikhel|"
    r"pharping|panauti|kirtipur)\b",
    re.I,
)

_ITINERARY = re.compile(
    r"\b(itinerary|plan|route|day (by day|plan)|schedule|how (many|long) days|"
    r"day 1|day 2|day 3|learn trip|trip plan|days? (for|in))\b",
    re.I,
)

_TRIP_MODIFICATION = re.compile(
    r"\b(make (it|my|this) (cheaper|easier|shorter|longer|faster|relaxed)|"
    r"change|modify|add (a|the)|remove|swap|replace|update (my|the) trip|"
    r"can (we|you) (add|drop|skip|change)|move (day|the)|reschedule|cheaper|"
    r"add pokhara|add \w+ to (my|the) trip)\b",
    re.I,
)

_RECOMMENDATION = re.compile(
    r"\b(recommend|suggest|best (place|trek|hotel|food|time)|which (one|trek|place)|"
    r"what should i|give me|top|must(-| )visit|worth (visiting|it))\b",
    re.I,
)

_SPECIFIC = re.compile(
    r"\b(my trip|this trip|the trip|our trip|my plan|the plan|our plan|day 3|day 4|"
    r"in the itinerary|my budget|travelers|start date|the itinerary|days_remove)\b",
    re.I,
)

# Known non-Nepal places that should be acknowledged but deflected are handled
# in the knowledge/response layer; intent OUT_OF_SCOPE above uses a curated list.

GENERAL_PATTERNS = (
    (_GREETINGS, GENERAL_CONVERSATION),
    (_THANKS, GENERAL_CONVERSATION),
    (_SMALLTALK, GENERAL_CONVERSATION),
)

TRAVEL_PATTERNS = (
    # Most specific first. PERMITS precedes TREKKING so "which permits for a
    # trek" routes to permit data; cultural/religious intent takes priority
    # over trekking/nature to prevent unrelated recommendations.
    (_PERMITS, PERMITS),
    (_CULTURE, CULTURE),
    (_RELIGION, RELIGION),
    (_TREKKING, TREKKING),
    (_RECOMMENDATION, RECOMMENDATION),
    (_WEATHER, WEATHER),
    (_BUDGET, BUDGET),
    (_TRANSPORT, TRANSPORT),
    (_ACCOMMODATION, ACCOMMODATION),
    (_FOOD, FOOD),
    (_NATURE, NATURE),
    (_DESTINATION, DESTINATION),
    (_ITINERARY, ITINERARY),
    (_TRIP_MODIFICATION, TRIP_MODIFICATION),
)


def classify_intent(message: str) -> str:
    """Classify a user message into one of the intent categories.

    Deterministic, fast, and free — no model call required.
    """
    if not message or not message.strip():
        return GENERAL_CONVERSATION

    msg = message.strip()

    # Out-of-scope (non-Nepal) destinations take priority.
    if _OUT_OF_SCOPE.search(msg):
        return OUT_OF_SCOPE

    # Simple conversational messages are answered directly and instantly.
    for pattern, intent in GENERAL_PATTERNS:
        if pattern.match(msg) or pattern.search(msg):
            return intent

    # A message that refers to the user's own trip/plan.
    if _SPECIFIC.search(msg):
        if _TRIP_MODIFICATION.search(msg):
            return TRIP_MODIFICATION
        return TRIP_SPECIFIC

    # General Nepal knowledge questions ("What is Nepal famous for?").
    if re.search(r"\bnepal\b", msg) and re.search(r"\b(what|famous|about|welcome|flag|culture|know)\b", msg):
        return NEPAL_GENERAL

    # Trip modification beats generic intent (e.g., "make it cheaper").
    if _TRIP_MODIFICATION.search(msg):
        return TRIP_MODIFICATION

    for pattern, intent in TRAVEL_PATTERNS:
        if pattern.search(msg):
            return intent

    # Fallback: conversational / general.
    if re.search(r"\b(hello|hey|hi|thanks|help|ok|okay|yes|no|great|nice|oh|cool)\b", msg, re.I):
        return GENERAL_CONVERSATION

    return NEPAL_GENERAL


def requires_trip_context(intent: str) -> bool:
    """Whether this intent likely needs the user's saved trip plan loaded."""
    return intent in (TRIP_MODIFICATION, TRIP_SPECIFIC)


def requires_recommendations(intent: str) -> bool:
    """Whether this intent likely needs the recommendation/scoring pipeline."""
    return intent in (RECOMMENDATION, DESTINATION, TREKKING, NATURE, ITINERARY)


def extract_destination_names(message: str) -> list:
    """Pull likely Nepal destination names out of a free-text message.

    Used by the recommender + knowledge base to filter relevant data.
    """
    known = {
        "kathmandu", "pokhara", "chitwan", "bandipur", "gorkha", "lumbini",
        "bhaktapur", "patan", "janakpur", "ilam", "rara", "jomsom", "manang",
        "mustang", "tansen", "palpa", "nagarkot", "dhulikhel", "pharping",
        "panauti", "kirtipur", "annapurna", "everest", "langtang", "poon hill",
        "abc", "mustang", "manaslu", "khopra", "mardi", "helambu", "gap",
    }
    text = message.lower()
    found = []
    for name in known:
        if re.search(rf"\b{re.escape(name)}\b", text):
            found.append(name)
    return list(dict.fromkeys(found))  # de-dupe, preserve order


def extract_months(message: str) -> list:
    """Detect season/month references in a message (e.g. 'summer', 'october')."""
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
        "december": 12,
    }
    seasons = {
        "spring": [3, 4, 5],
        "summer": [6, 7, 8],
        "monsoon": [6, 7, 8],
        "autumn": [9, 10, 11],
        "fall": [9, 10, 11],
        "winter": [12, 1, 2],
    }
    text = message.lower()
    found_months = []
    for month, m in months.items():
        if re.search(rf"\b{month}\b", text):
            found_months.append(m)
    for season, ms in seasons.items():
        if re.search(rf"\b{season}\b", text):
            found_months.extend(ms)
    return list(dict.fromkeys(found_months))


def season_for_month(month: Optional[int]) -> str:
    """Map a month number to a Nepal season label ('spring'/'summer'/'autumn'/'winter')."""
    if not month:
        return ""
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"