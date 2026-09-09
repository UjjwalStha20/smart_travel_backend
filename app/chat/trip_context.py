"""Trip-aware chat context building and intent classification."""

import re
from typing import Dict, List, Optional


INTENTS = (
    "general_question",
    "itinerary_question",
    "modify_itinerary",
    "add_destination",
    "remove_destination",
    "change_budget",
    "find_restaurant",
    "find_hotel",
    "find_activity",
    "transportation_question",
    "weather_question",
    "cultural_question",
    "historical_question",
    "trek_question",
    "hiking_question",
    "recommendation_request",
    "trip_summary",
    "unknown",
)

_INTENT_PATTERNS: List[tuple] = [
    ("weather_question", re.compile(r"weather|temperature|rain|forecast|sunny|monsoon|snow", re.I)),
    ("transportation_question", re.compile(r"bus|flight|car|taxi|transport|how (do|can) (i )?get|reach|driving|ride share", re.I)),
    ("find_restaurant", re.compile(r"restaurant|restaurant|food|eat|dinner|lunch|breakfast|cafe|café|dining|momo|dal bhat", re.I)),
    ("find_hotel", re.compile(r"hotel|lodge|stay|accommodat|teahouse|resort|room|hostel", re.I)),
    ("find_activity", re.compile(r"activity|things to do|things-to-do|attraction|visit|tour|experience|sightseeing", re.I)),
    ("weather_question", re.compile(r"weather", re.I)),
    ("add_destination", re.compile(r"(add|include|also visit|go to|put in|add in)\b.*(destination|place|city|town|heritage|site)", re.I)),
    ("add_destination", re.compile(r"can we (add|include|go to|visit)\b", re.I)),
    ("remove_destination", re.compile(r"remove|drop|take out|skip|don'?t (need|want).*(day|destination|stop)", re.I)),
    ("change_budget", re.compile(r"budget|cheaper|cheap|expensive|cost less|save money|price", re.I)),
    ("trek_question", re.compile(r"trek|trekking|route|choose trip|annapurna|everest|abc|poon hill", re.I)),
    ("hiking_question", re.compile(r"hiking|hike|trail|walking", re.I)),
    ("cultural_question", re.compile(r"culture|cultural|temple|stupa|monastery|heritage|festival", re.I)),
    ("historical_question", re.compile(r"histor|museum|monument|archaeol|palace|medieval", re.I)),
    ("trips_summary_catch", re.compile(r"summary|summar", re.I)),
    ("recommendation_request", re.compile(r"recommend|suggest|best (place|option|spot|restaurant|hotel)|near (our|the) (hotel|stay|accommodation)", re.I)),
]

# order matters: more specific intent for the common "modify" phrases
_MODIFY_PATTERNS = (
    re.compile(r"change|edit|modify|update|adjust", re.I),
    re.compile(r"move|swap|replace", re.I),
    re.compile(r"too (packed|busy|much|tight|relaxed)|less busy|more relaxed|another day|one more day|spend (another|extra) day", re.I),
    re.compile(r"remove .*(day|item|activity)", re.I),
    re.compile(r"don'?t want", re.I),
    re.compile(r"i want more|i want less|make it", re.I),
)


def classify_intent(message: str) -> str:
    """Rule-based intent classification (deterministic; AI can override via plan_change.intent)."""
    msg = message.strip()
    if not msg:
        return "unknown"
    if any(p.search(msg) for p in _MODIFY_PATTERNS):
        if re.search(r"add|include|also visit", msg, re.I):
            return "add_destination"
        return "modify_itinerary"
    for intent, pattern in _INTENT_PATTERNS:
        if pattern.search(msg):
            if intent == "trips_summary_catch":
                return "trip_summary"
            return intent
    if re.search(r"what|how|when|where|tell me|plan|itinerar", msg, re.I):
        return "itinerary_question"
    return "unknown"


def _fmt_days(days: List[dict]) -> str:
    lines = []
    for d in sorted(days, key=lambda x: x.get("day_number", 0)):
        items = d.get("items") or []
        item_str = " → ".join(it.get("title", "") for it in items) if items else "Free time"
        line = f"Day {d.get('day_number')} — {d.get('location') or d.get('title') or ''}: {item_str}"
        if d.get("notes"):
            line += f"  (note: {d['notes']})"
        lines.append(line)
    return "\n".join(lines) if lines else "(no itinerary generated yet)"


def build_trip_context(trip: dict) -> str:
    budget = trip.get("budget") or {}
    travelers = trip.get("travelers") or {}
    prefs = trip.get("preferences") or {}
    budget_str = f"{budget.get('amount', 'n/a')} {budget.get('currency', 'NPR')} ({budget.get('level', 'n/a')})"
    travelers_str = f"{travelers.get('count', 'n/a')} ({travelers.get('type', 'n/a')})"
    return (
        f"## CURRENT TRIP (this is the ONLY trip you are planning for the user)\n"
        f"- Name: {trip.get('name')}\n"
        f"- Status: {trip.get('status')}\n"
        f"- Destinations: {', '.join(trip.get('destinations') or []) or 'n/a'}\n"
        f"- Start location: {trip.get('start_location') or 'n/a'}\n"
        f"- Dates: {trip.get('start_date') or '?'} → {trip.get('end_date') or '?'} "
        f"({trip.get('duration_days') or '?'} days)\n"
        f"- Travelers: {travelers_str}\n"
        f"- Budget: {budget_str}\n"
        f"- Trip types: {', '.join(trip.get('trip_types') or []) or 'n/a'}\n"
        f"- Transportation preference: {', '.join(trip.get('transportation') or []) or 'n/a'}\n"
        f"- Accommodation: {trip.get('accommodation') or 'n/a'}\n"
        f"- Pace: {prefs.get('pace', 'n/a')}\n"
        f"- Interests: {', '.join(prefs.get('interests') or []) or 'n/a'}\n"
        f"- Special requirements: {trip.get('special_requirements') or 'none'}\n"
    )


def build_itinerary_context(trip: dict) -> str:
    return "## CURRENT ITINERARY (day-by-day)\n" + _fmt_days(trip.get("itinerary_days") or [])


def build_history_context(messages: List[dict], max_items: int = 12) -> str:
    if not messages:
        return ""
    lines = []
    for m in messages[-max_items:]:
        role = "User" if m.get("role") == "user" else "Assistant"
        lines.append(f"{role}: {m.get('content')}")
    return "## RECENT CONVERSATION\n" + "\n".join(lines)


TRIP_SYSTEM_PROMPT = """You are the Smart Travel Planner AI, an expert travel planning assistant for Nepal.
You help ONE trip at a time. The trip details (preferences, itinerary, budget) are provided to you in context — NEVER ask the user to repeat information that is already there unless genuine clarification is needed.

Rules:
1. Keep replies conversational and concise. Do not dump entire itineraries every time.
2. When the user suggests a change (move a day, add/remove an activity, change budget, add a destination, etc.), propose the change and then ALWAYS end your reply with a single structured block:
<plan_change>{json}</plan_change>
where json matches exactly:
{"intent": "modify_itinerary", "summary": "short human summary of the change", "trip": { /* only fields that change: budget, pace, trip_types, transportation, accommodation, destinations, preferences */ }, "days": [{"day_number": N, "title": "...", "location": "...", "notes": "...", "items": [{"title": "...", "category": "...", "duration_hours": 0, "notes": "..."}]}], "days_remove": [N]}
Only include the days you modified — leave unchanged days out. Use days_remove to delete a day.
3. For real information (prices, opening hours, permits, weather, transport, restaurants, hotels, activities) call the appropriate TOOL using the exact <tool_call> XML format instructed in your tooling instructions. Never invent prices, hours, or schedules — use tool results.
4. Recommendations should come from real data returned by tools, and must fit the current trip's location, budget and interests.
5. Do not mention or use ANY other trip the user may have. Stay strictly within the context given."""

PLAN_CHANGE_PATTERN = re.compile(r"<plan_change>\s*(.*?)\s*</plan_change>", re.DOTALL)


def parse_plan_change(reply: str) -> Optional[dict]:
    match = PLAN_CHANGE_PATTERN.search(reply)
    if not match:
        return None
    import json as _json
    raw = match.group(1).strip()
    candidates = [raw]
    if raw.startswith("{{"):
        candidates.append(raw.replace("{{", "{").replace("}}", "}"))
    for candidate in candidates:
        try:
            data = _json.loads(candidate)
            if isinstance(data, dict):
                return data
        except _json.JSONDecodeError:
            continue
    return None


def strip_plan_change(reply: str) -> str:
    return PLAN_CHANGE_PATTERN.sub("", reply).strip()