"""Unified destination recommendation pipeline for the chatbot.

Combines the project's existing scoring algorithms into one 0-100 score:

    final_score = content_score + preference_score + context_score
                + collaborative_score + popularity_score

Weights from `RecommendationService._score_destinations` are preserved as the
default base weights (0.35 / 0.20 / 0.20 / 0.15 / 0.10) and are *contextually
boosted* based on the user's current request ("cultural", "monsoon", "budget",
"easy trek", etc.). Scores are normalized to 0-100 for a single comparable scale.
"""

import re
from typing import Dict, List, Optional

from sqlmodel import Session, select

from app.chat.intent import (
    BUDGET,
    RECOMMENDATION,
    TREKKING,
    WEATHER,
    extract_months,
    season_for_month,
)
from app.models import Destination

# Base weights preserved from the existing hybrid recommender.
BASE_WEIGHTS = {
    "content": 0.35,
    "preference": 0.20,
    "context": 0.20,
    "collaborative": 0.15,
    "popularity": 0.10,
}

# Contextual boosts applied on top of the base weights (chat-only).
_INTENT_BOOSTS = {
    BUDGET: {"preference": 0.18, "content": -0.08},
    WEATHER: {"context": 0.25, "content": -0.08, "preference": -0.05},
    TREKKING: {"context": 0.07, "content": 0.10, "preference": 0.05, "popularity": -0.08},
    RECOMMENDATION: {"content": 0.06, "preference": 0.06},
}


class UnifiedRecommender:
    """Run the existing scoring components and rank Nepal destinations."""

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend(
        self,
        intent: str,
        message: str = "",
        trip: Optional[dict] = None,
        user_id: Optional[str] = None,
        limit: int = 6,
        season: Optional[str] = None,
    ) -> List[dict]:
        """Return ranked destination recommendations (score 0-100)."""
        req = build_requirements(intent, message, trip, user_id=user_id, season=season)

        # Component scores from existing algorithms.
        from app.services.content_based import ContentBasedFiltering
        from app.services.contextual import ContextAwareFiltering
        from app.services.popularity import PopularityBased
        from app.services.structured_preferences import StructuredPreferenceMatcher

        content = ContentBasedFiltering(self.session).compute_user_destination_similarity(
            req["user_profile"]
        )
        preferences = StructuredPreferenceMatcher(self.session).compute_all_preference_scores(
            req["user_profile"]
        )
        contextual = ContextAwareFiltering(self.session).compute_all_context_scores(
            req["user_profile"]
        )
        popularity = PopularityBased(self.session)._compute_all_popularity_scores()

        weights = self._weights_for(intent, req)

        results: List[dict] = []
        for dest in self._candidates(req):
            content_score = content.get(str(dest.id), 0.5)
            pref_score = preferences.get(str(dest.id), 0.5)
            context_score = contextual.get(str(dest.id), 0.5)
            pop_score = popularity.get(str(dest.id), 0.5)

            # Direct message-name match: "in Kathmandu" should surface the
            # destinations whose names contain the mentioned place.
            # Content similarity is dampened: without a real interaction history
            # TF-IDF is noisy and would let one long description win everything.
            content_term = max(content.get(str(dest.id), 0.5) * 0.6, self._name_match_bonus(dest, req))

            # Difficulty bonus (mode-aware) for trek-focused questions.
            diff_bonus = self._difficulty_bonus(dest, req)

            score = (
                weights["content"] * max(content_term, 0.0)
                + weights["preference"] * pref_score
                + weights["context"] * context_score
                + weights["popularity"] * pop_score
            ) + diff_bonus

            # Season/monsoon advisory: heavily penalize poor-season picks.
            season_penalty = self._season_penalty(dest, req.get("season"))
            score = (score * season_penalty) * 100.0
            score = max(0.0, min(100.0, round(score, 1)))

            results.append(
                {
                    "destination_id": str(dest.id),
                    "name": dest.name,
                    "category": dest.category.value if hasattr(dest.category, "value") else str(dest.category),
                    "score": score,
                    "reason": self._reason(dest, req),
                    "description": (dest.description or "")[:300],
                }
            )

        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _candidates(self, req: dict) -> List[Destination]:
        """Destination candidates, excluding places already in the trip."""
        dests = self.session.exec(
            select(Destination).order_by(Destination.name.asc())
        ).all()
        exclude = {d.lower() for d in req.get("in_trip", [])}
        if not exclude:
            return dests
        out = []
        for d in dests:
            if d.name.lower() in exclude:
                continue
            out.append(d)
        return out

    @staticmethod
    def _weights_for(intent: str, req: dict) -> dict:
        w = dict(BASE_WEIGHTS)
        for key, delta in _INTENT_BOOSTS.get(intent, {}).items():
            w[key] = max(0.0, min(1.0, w.get(key, 0.0) + delta))

        # Generic "easy / cultural / relaxed" phrasing adjusts preference weight.
        text = req.get("text", "").lower()
        if any(k in text for k in ("easy", "relaxed", "culture", "family", "short")):
            w["preference"] = min(1.0, w["preference"] + 0.08)
        if any(k in text for k in ("adventure", "hard", "challenging", "extreme")):
            w["context"] = min(1.0, w["context"] + 0.08)

        # Re-normalize so the weights still sum to 1.
        total = sum(w.values()) or 1.0
        return {k: v / total for k, v in w.items()}

    @staticmethod
    def _name_match_bonus(dest: Destination, req: dict) -> float:
        dname = dest.name.lower()
        for n in req.get("interests", []):
            n = str(n).lower()
            if n and (n in dname or dname in n or n in dest.description.lower() if dest.description else False):
                return 0.9
        return 0.0

    @staticmethod
    def _difficulty_bonus(dest: Destination, req: dict) -> float:
        want = req.get("difficulty")
        if not want:
            return 0.0
        route_diff = None
        for r in dest.trekking_routes or []:
            route_diff = (r.difficulty.value if hasattr(r.difficulty, "value") else str(r.difficulty)).lower()
            break
        if not route_diff:
            return 0.0
        want = want.lower()
        if want == route_diff:
            return 0.08
        if route_diff == "moderate":
            return 0.03
        return -0.05

    @staticmethod
    def _season_penalty(dest: Destination, season: Optional[str]) -> float:
        if not season:
            return 1.0
        best = [str(b).lower() for b in (dest.best_time or [])]
        if not best:
            return 0.9
        if season in best or any(s in season or season in s for s in best):
            return 1.0
        if season == "summer":
            # Monsoon: rain-shadow / lower altitude areas are still viable.
            text = (dest.description or "").lower()
            altitude = _max_altitude(dest)
            if "rain shadow" in text or "trans-himalayan" in text:
                return 0.95
            if altitude and altitude < 2500:
                return 0.85
            return 0.6
        return 0.7

    @staticmethod
    def _reason(dest: Destination, req: dict) -> str:
        bits = []
        text = req.get("text", "").lower()
        cat = dest.category.value if hasattr(dest.category, "value") else str(dest.category)
        best = [str(b) for b in (dest.best_time or [])]

        if cat == "trek":
            bits.append(f"a {cat} destination")
        else:
            bits.append(f"an {cat} destination")

        if best:
            bits.append(f"best visited in {', '.join(best[:2])}")

        if req.get("season") and req.get("season") in [s.lower() for s in best]:
            bits.append("matches your season")

        altitude = _max_altitude(dest)
        if altitude:
            bits.append(f"max altitude ~{altitude}m")

        return "; ".join(bits) if bits else "Matches your trip preferences"


def _max_altitude(dest: Destination) -> Optional[int]:
    for r in dest.trekking_routes or []:
        if getattr(r, "max_altitude", None):
            return r.max_altitude
    return None


def build_requirements(
    intent: str,
    message: str,
    trip: Optional[dict],
    user_profile: Optional[dict] = None,
    user_id: Optional[str] = None,
    season: Optional[str] = None,
) -> dict:
    """Extract normalized requirements from the message + saved trip.

    `season` is an optional explicit override (e.g. derived from travel dates
    in the Plan a Trip form); when absent it is inferred from the message.
    """
    from app.chat.intent import extract_destination_names

    months = extract_months(message)
    season_value = (season or "").strip() or (season_for_month(months[0]) if months else "")

    budget_level = None
    difficulty = None
    interests: list = []
    activities: list = []
    in_trip: list = []

    # Pull from the saved trip first (source of truth for personalization).
    if trip:
        budget = trip.get("budget") or {}
        budget_level = budget.get("level")
        prefs = trip.get("preferences") or {}
        answers = trip.get("answers") or {}
        in_trip = [d.lower() for d in (trip.get("destinations") or [])]
        interests = list(prefs.get("interests") or [])
        difficulty = answers.get("difficulty") or prefs.get("difficulty")
        pace = answers.get("pace") or prefs.get("pace")
        if pace == "relaxed" and not difficulty:
            difficulty = "easy"

        # User-supplied, validated preferences (from the chat request).
        if user_profile:
            budget_level = user_profile.get("budget", budget_level)
            difficulty = user_profile.get("fitness_level", difficulty)
        # Interpolate answers: chip-style values become interests.
        for key, val in (answers or {}).items():
            if isinstance(val, list):
                interests.extend(str(v) for v in val)
            elif isinstance(val, bool) and val:
                interests.append(key.replace("_", " "))
            elif isinstance(val, str) and val.strip() and len(val) < 40:
                interests.append(val.strip())

    # Message-level signals override trip default.
    if re.search(r"budget|cheap|\bnpr\b|\bus\b|money", message, re.I):
        budget_level = budget_level or "budget"
    if re.search(r"\b(easy|relaxed|beginner)\b", message, re.I):
        difficulty = "easy"
    if re.search(r"\b(hard|challenging|difficult|advanced)\b", message, re.I):
        difficulty = "hard"
    names = extract_destination_names(message)
    if names:
        interests.extend(names)

    if trip:
        activities = list(trip.get("trip_types") or [])

    # Profile for the existing algorithm components (mirrors RecommendationService).
    # Both key conventions are provided: ContentBased reads categories/activities/
    # budget_type/difficulty; StructuredPreference + Contextual read preferred_*.
    user_profile_dict = {
        "user_id": user_id or ((trip or {}).get("user_id")),
        "preferred_categories": list((trip or {}).get("trip_types") or []),
        "categories": list((trip or {}).get("trip_types") or []),
        "preferred_activities": [str(a) for a in activities],
        "activities": [str(a) for a in activities] + [str(i) for i in interests],
        "budget_preference": budget_level,
        "budget_type": budget_level or "",
        "typical_duration": (trip or {}).get("duration_days") or 0,
        "difficulty_preference": difficulty or "moderate",
        "difficulty": difficulty or "moderate",
        "preferred_season": [season_value] if season_value else [],
        "travel_style": (trip or {}).get("preferences", {}).get("pace") or "cultural",
    }

    return {
        "intent": intent,
        "text": message,
        "months": months,
        "season": season_value,
        "budget_level": budget_level,
        "difficulty": difficulty,
        "interests": interests,
        "activities": activities,
        "in_trip": in_trip,
        "user_profile": user_profile_dict,
    }