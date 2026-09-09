"""Progressive requirement gathering for trip-planning chat messages.

Prevents the assistant from drafting a full itinerary when the user has not
given enough to plan one ("I have 5 days in Nepal" must prompt for a trip
style instead). Facts are collected from the WHOLE conversation (history +
current message) so something the user already said is never asked again.

This module is deterministic and stateless: no LLM calls, no persisted state —
it only reads the messages that are already in the conversation.
"""

import re

from app.chat.intent import (
    ITINERARY,
    RECOMMENDATION,
    extract_destination_names,
    extract_months,
    season_for_month,
)

# ---------------------------------------------------------------------------
# Trip facts we can collect from free text.
# ---------------------------------------------------------------------------

_SPELLED_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

_WEEK_RE = re.compile(
    r"(?:\b(\d{1,2})|(a|an|one|two|three|four|five))\s*(?:week|weeks)\b", re.I
)
_DAYS_N_RE = re.compile(r"\b(\d{1,2})(?:\s*[-–]\s*|\s+)days?\b", re.I)
_DAYS_D_RE = re.compile(r"\b(\d{1,2})\s*d\b", re.I)
_DAYS_SPELLED_RE = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+days?\b", re.I
)

_PATTERNS = (
    (re.compile(
        r"\b(trek(king|ker|s)?|everest base camp|annapurna base camp|base camp|"
        r"poon hill|\babc\b|\bebc\b|langtang|manaslu|mustang|gorakshep|helambu)\b", re.I),
     "trekking"),
    (re.compile(r"\b(hike(s|r|rs|ing)?|day hike|trails?)\b", re.I), "hiking"),
    (re.compile(
        r"\b(nature|mountains?|lakes?|rivers?|forests?|jungle|wildlife|"
        r"national park|bird(s)?|rhododendron|sunrise)\b", re.I),
     "nature"),
    (re.compile(
        r"\b(cultur(al|e)?|temples?|stupas?|festivals?|heritage|monaster(?:y|ies)|"
        r"durbar|traditional)\b", re.I),
     "culture"),
    (re.compile(
        r"\b(sightsee(ing)?|city tour|monuments?|museums?|architecture|"
        r"old (city|town)|durbar squares)\b", re.I),
     "sightseeing"),
    (re.compile(
        r"\b(adventure|rafting|paraglid(ing|e)?|bungee|zipline|zip lining|"
        r"canyoning|mountain biking)\b", re.I),
     "adventure"),
    (re.compile(r"\b(mix|both|combined|a bit of (every|both|everything)|"
                r"everything)\b", re.I),
     "mix"),
)

_OUTDOOR = {"trekking", "hiking", "nature", "adventure", "mix"}

_PLAN_RE = re.compile(
    r"\b(plan|itinerar(y|ies)|route|day-?by-?day|trip plan|schedule|arrange)\b", re.I
)

_GATHER_SIGNS = (
    "How many days do you have for the trip?",
    "What kind of trip are you after",
    "Which month or season are you travelling",
)


def extract_days(text: str):
    """Best-effort trip-duration extraction ('7 days', 'two weeks', '1d')."""
    if not text:
        return None
    m = _WEEK_RE.search(text)
    if m:
        if m.group(1):
            return int(m.group(1)) * 7
        return (_SPELLED_NUM.get(m.group(2).lower()) or 1) * 7  # "a week" -> 7
    m = _DAYS_N_RE.search(text) or _DAYS_D_RE.search(text)
    if m and m.group(1):
        return int(m.group(1))
    m = _DAYS_SPELLED_RE.search(text)
    if m:
        return _SPELLED_NUM.get(m.group(1).lower())
    return None


def extract_styles(text: str) -> list:
    """Map trip-style words to a small set: trekking/hiking/nature/sightseeing/culture/adventure/mix."""
    if not text:
        return []
    found = []
    for pattern, label in _PATTERNS:
        if pattern.search(text) and label not in found:
            found.append(label)
    return found


def extract_season(text: str) -> str:
    """Season label (spring/summer/autumn/winter) if the text mentions it."""
    if not text:
        return ""
    months = extract_months(text)
    return season_for_month(months[0]) if months else ""


def collect_facts(history: list, current: str = "") -> dict:
    """Gather trip facts from the current message + earlier user turns.

    Newest user text wins, so a later "actually 10 days" overrides an
    earlier "5 days". Only user turns are read (assistant questions contain
    the option words we are matching against and must not count as answers).

    Returns dict with: days, styles (trekking/hiking/nature/sightseeing/culture/adventure/mix),
    season, interests (list of destination names or user-declared interests),
    budget_level, pace, and any other trip details found in the conversation.
    """
    texts = []
    if current:
        texts.append(current)
    for m in reversed(history or []):
        if isinstance(m, dict) and m.get("role") == "user":
            texts.append(m.get("content") or "")

    days = None
    styles = []
    season = ""
    interests = []
    budget_level = None
    pace = None

    for t in texts:
        # Extract days (duration) - first value wins
        if days is None:
            days = extract_days(t)
        # Extract styles
        found_styles = extract_styles(t)
        for s in found_styles:
            if s not in styles:
                styles.append(s)
        # Extract season
        if not season:
            season = extract_season(t)
        # Extract interests/destination names
        extracted_names = extract_destination_names(t)
        for name in extracted_names:
            if name not in interests:
                interests.append(name)
        # Extract budget hints
        if not budget_level and re.search(r"budget|cheap|\bnpr\b|\bus\b|money", t, re.I):
            budget_level = "budget"
        # Extract pace
        if not pace and re.search(r"\b(slow|relaxed|normal|fast)\b", t, re.I):
            pace = "relaxed" if re.search(r"\b(slow|relaxed)\b", t, re.I) else ("normal" if re.search(r"\bnormal\b", t, re.I) else "fast")

    return {
        "days": days,
        "styles": styles,
        "season": season,
        "interests": interests,
        "budget_level": budget_level,
        "pace": pace,
    }


def is_in_gather_flow(history: list) -> bool:
    """Whether the assistant is mid multi-turn planning questions.

    True when the most recent assistant message is one of our clarifying
    follow-up questions — so a terse reply like "trekking" (which classifies
    as TREKKING, not a planning intent) stays in the gathering loop instead
    of jumping straight to recommendations.
    """
    last_assistant = None
    for m in reversed(history or []):
        if isinstance(m, dict) and m.get("role") == "assistant":
            last_assistant = m
            break
    if last_assistant is None:
        return False
    content = last_assistant.get("content") or ""
    return any(sig in content for sig in _GATHER_SIGNS)


def is_planning_request(intent: str, message: str, facts: dict) -> bool:
    """Whether this message is a trip-planning request (vs a direct question).

    Direct questions ("which trek is good in October?", "how many days for
    ABC?") fall through to normal answering; planning requests are gated.
    """
    if intent == RECOMMENDATION:
        return not bool(
            facts.get("days")
            or facts.get("styles")
            or facts.get("season")
            or extract_destination_names(message)
        )
    if intent != ITINERARY:
        return False
    # Planning needs a duration or an explicit request for a plan. "how many
    # days for X" is the user asking US for info — not a plan request.
    return bool(facts.get("days") or _PLAN_RE.search(message))


def follow_up_question(facts: dict):
    """Return the single next question needed, or None when enough is known.

    Priority: duration -> trip style -> travel season (outdoor trips only).
    Only ONE question per reply, so the conversation narrows progressively.
    """
    if not facts.get("days"):
        return "How many days do you have for the trip?"
    if not facts.get("styles"):
        return (
            "What kind of trip are you after — trekking, hiking, nature, "
            "sightseeing, culture, or a mix?"
        )
    if not facts.get("season") and any(s in _OUTDOOR for s in facts["styles"]):
        return (
            "Which month or season are you travelling? "
            "(Nepal's monsoon runs June–August, which changes what's open.)"
        )
    return None