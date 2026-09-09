from typing import Dict, Any, List, Optional
from uuid import UUID
import time

from sqlmodel import select

from app.models import User, Destination, TrekkingRoute, UserPreferences, Address
from app.services.live_data import fetch_weather
from app.core.config import settings


# ---------------------------------------------------------------------------
# Live-weather signal for the contextual recommender.
# Offline safe: any lookup failure disables live lookups for a while and the
# scorer falls back to the static season-based context score (neutral factor).
# ---------------------------------------------------------------------------

_WEATHER_CACHE: Dict[tuple, tuple] = {}
_WEATHER_TTL_SECONDS = 1800  # 30 min
_WEATHER_DISABLE_UNTIL = 0.0
_WEATHER_DISABLE_WINDOW = 300  # 5 min off-window after a failure
WEATHER_NOTES: Dict[str, str] = {}


def reset_weather_state() -> None:
    """Clear cached weather and re-enable live lookups (used by tests)."""
    global _WEATHER_DISABLE_UNTIL
    _WEATHER_CACHE.clear()
    _WEATHER_DISABLE_UNTIL = 0.0
    WEATHER_NOTES.clear()


def _get_live_weather(latitude: float, longitude: float) -> Optional[dict]:
    """Fetch live weather with caching and a circuit breaker for offline use."""
    global _WEATHER_DISABLE_UNTIL
    now = time.time()
    if settings.WEATHER_MODE == "off" or now < _WEATHER_DISABLE_UNTIL:
        return None

    key = (round(latitude, 4), round(longitude, 4))
    if key in _WEATHER_CACHE:
        cached_at, data = _WEATHER_CACHE[key]
        if now - cached_at < _WEATHER_TTL_SECONDS:
            return data

    try:
        data = fetch_weather(latitude, longitude, days=5, timeout=2.0)
    except Exception:
        # Offline or upstream failure: stop trying for a while, stay neutral.
        _WEATHER_DISABLE_UNTIL = now + _WEATHER_DISABLE_WINDOW
        return None

    _WEATHER_CACHE[key] = (time.time(), data)
    return data


def weather_comfort_factor(weather: dict) -> float:
    """Map current temp + 3-day rain probability to a 0..1 comfort factor."""
    factor = 1.0
    current = weather.get("current") or {}
    temp = current.get("temperature_c")
    if temp is not None:
        if temp < 5:
            factor *= 0.85
        elif temp < 10:
            factor *= 0.95
        elif temp <= 28:
            pass
        elif temp <= 35:
            factor *= 0.85
        else:
            factor *= 0.7

    rain = [
        d.get("precipitation_probability") or d.get("precipitation_probability_max")
        for d in weather.get("daily") or []
    ]
    rain = [p for p in rain if p is not None]
    if rain:
        worst = max(rain)
        if worst >= 70:
            factor *= 0.7
        elif worst >= 40:
            factor *= 0.85
        elif worst >= 20:
            factor *= 0.95
    return factor


def weather_note(weather: dict, factor: float) -> str:
    """Human-readable note surfaced in the recommendation explanation."""
    current = weather.get("current") or {}
    temp = current.get("temperature_c")
    condition = current.get("condition")
    rain = [
        d.get("precipitation_probability") or d.get("precipitation_probability_max")
        for d in weather.get("daily") or []
    ]
    rain = [p for p in rain if p is not None]
    worst_rain = max(rain) if rain else 0

    parts = []
    if temp is not None:
        parts.append(f"{temp:.0f}\u00b0C")
    if condition:
        parts.append(condition.lower())
    if worst_rain > 0:
        parts.append(f"{worst_rain:.0f}% rain next 3 days")

    verdict = "ideal time" if factor >= 0.95 else "check conditions before you go"
    return f"Live weather: {', '.join(parts)} \u2014 {verdict}"


class ContextAwareFiltering:
    """Context-aware recommendation filtering for Nepal-specific factors."""

    def __init__(self, session):
        self.session = session
        self._address_cache: Dict[UUID, Optional[Address]] = {}

    def compute_all_context_scores(
        self, user_profile: Dict[str, Any]
    ) -> Dict[str, float]:
        """Compute context scores for all destinations."""
        destinations = self.session.exec(select(Destination)).all()

        # Get selected season from user profile or default
        preferred_season = user_profile.get("preferred_season", [])
        if not preferred_season:
            # Try to get from user preferences
            stmt = select(UserPreferences).where(UserPreferences.user_id == user_profile.get("user_id"))
            prefs = self.session.exec(stmt).first()
            if prefs:
                preferred_season = getattr(prefs, "preferred_season", []) or []

        # Get current/selected season if available
        selected_season = preferred_season

        scored: Dict[str, float] = {}

        for dest in destinations:
            score = self._compute_context_score(dest, selected_season)
            scored[str(dest.id)] = score

        return scored

    def get_context_score(self, dest: Destination, user_profile: Any) -> float:
        """Get context score for a specific destination."""
        # Handle both User object and dict
        if hasattr(user_profile, "id"):  # It is a User object
            user_id = user_profile.id
            # Get preferences from DB
            stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
            prefs = self.session.exec(stmt).first()
            selected_season = getattr(prefs, "preferred_season", []) if prefs else []
        elif isinstance(user_profile, dict):  # It is a dict
            selected_season = user_profile.get("preferred_season", [])
            if not selected_season:
                user_id = user_profile.get("user_id")
                if user_id:
                    stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
                    prefs = self.session.exec(stmt).first()
                    selected_season = getattr(prefs, "preferred_season", []) if prefs else []
        else:
            selected_season = []

        return self._compute_context_score(dest, selected_season)

    def _compute_context_score(
        self, dest: Destination, selected_season: List[str]
    ) -> float:
        """
        Compute context-aware score for a destination.

        Factors:
        - Season suitability
        - Permit requirements
        - Altitude/Difficulty suitability
        - Duration fitting
        """
        score = 1.0  # Start perfect, apply penalties

        # 1. Season matching
        season_score = self._check_season_compatibility(dest, selected_season)
        score *= season_score

        # 2. Permit requirements
        permit_required = getattr(dest, "permit_required", False)
        if permit_required:
            score *= 0.8  # 20% penalty for permit requirements

        # 3. Altitude suitability (for treks)
        routes = self.session.exec(
            select(TrekkingRoute).where(
                TrekkingRoute.destination_id == dest.id
            )
        ).all()
        if routes:
            for route in routes:
                max_altitude = getattr(route, "max_altitude", None)
                if max_altitude and max_altitude > 3000:
                    score *= 0.9

        # 4. Duration fitting
        typical_duration = self._get_typical_duration(dest)
        if typical_score := self._check_duration_fitting(dest, typical_duration):
            score *= typical_score

        # 5. Live-weather comfort (neutral when offline / unavailable)
        weather_factor = self._weather_factor(dest)
        if weather_factor is not None:
            score *= weather_factor

        return min(score, 1.0)

    def _weather_factor(self, dest: Destination) -> Optional[float]:
        """Live-weather multiplier; None means neutral (offline fallback)."""
        address_id = getattr(dest, "address_id", None)
        if address_id is None:
            return None
        addr = self._address_cache.get(address_id)
        if addr is None:
            addr = self.session.get(Address, address_id)
            self._address_cache[address_id] = addr
        if addr is None or addr.latitude is None or addr.longitude is None:
            return None

        weather = _get_live_weather(addr.latitude, addr.longitude)
        if weather is None:
            WEATHER_NOTES.pop(str(dest.id), None)
            return None

        factor = weather_comfort_factor(weather)
        WEATHER_NOTES[str(dest.id)] = weather_note(weather, factor)
        return factor

    def _check_season_compatibility(
        self, dest: Destination, selected_season: List[str]
    ) -> float:
        """Check if destination is suitable for the selected season."""
        if not selected_season:
            return 0.8

        dest_season = getattr(dest, "best_time", []) or []
        if not dest_season:
            return 0.7

        dest_season_lower = [s.lower() for s in dest_season]
        selected_lower = [s.lower() for s in selected_season]

        exact_matches = set(dest_season_lower) & set(selected_lower)
        if exact_matches:
            return min(len(exact_matches) / len(dest_season), 1.0)

        season_keywords = {
            "spring": ["march", "april", "may"],
            "autumn": ["september", "october", "november"],
            "winter": ["december", "january", "february"],
            "summer": ["june", "july", "august"],
        }

        score = 0.0
        for ss in selected_lower:
            for ds in dest_season_lower:
                for kw, kws in season_keywords.items():
                    if kw in ss or kw in ds:
                        score += 0.1

        if score > 0 and not exact_matches:
            return min(score, 0.7)
        elif not exact_matches and score == 0:
            return 0.4

        return min(score, 1.0)

    def _get_typical_duration(self, dest: Destination) -> Optional[int]:
        """Get typical duration for a destination."""
        routes = self.session.exec(
            select(TrekkingRoute).where(
                TrekkingRoute.destination_id == dest.id
            )
        ).all()
        if routes:
            for route in routes:
                rec_days = getattr(route, "recommended_days", None)
                if rec_days and rec_days > 0:
                    return rec_days
        return None

    def _check_duration_fitting(
        self, dest: Destination, typical_duration: Optional[int]
    ) -> float:
        """Check if destination duration fits user's typical trip length."""
        if typical_duration is None or typical_duration <= 0:
            return 0.8

        rec_days = 0
        routes = self.session.exec(
            select(TrekkingRoute).where(
                TrekkingRoute.destination_id == dest.id
            )
        ).all()
        if routes:
            for route in routes:
                rdays = getattr(route, "recommended_days", None)
                if rdays:
                    rec_days = max(rec_days, rdays)

        if rec_days <= 0:
            return 0.8

        ratio = typical_duration / rec_days if rec_days > 0 else 1.0

        if 0.5 <= ratio <= 2.0:
            return 1.0
        elif ratio < 0.5:
            return 0.8
        else:
            return 0.6

    def filter_by_context(
        self, destinations: List[tuple], user: User, selected_season: Optional[List[str]] = None
    ) -> List[tuple]:
        """Filter out destinations that violate hard contextual constraints."""
        filtered = []

        for dest, score in destinations:
            keep, reason = _hard_context_filter(dest, user, selected_season)
            if keep:
                filtered.append((dest, score))

        return filtered


def _hard_context_filter(
    dest: Destination, user: User, selected_season: Optional[List[str]]
) -> tuple:
    """
    Apply hard contextual filters.

    Returns (keep: bool, reason: Optional[str])
    """
    if getattr(dest, "permit_required", False):
        return True, None

    return True, None


class ContextScoreOutput:
    """Output model for context scores."""
    pass
