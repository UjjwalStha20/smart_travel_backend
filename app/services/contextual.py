from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlmodel import select

from app.models import User, Destination, UserPreferences


class ContextAwareFiltering:
    """Context-aware recommendation filtering for Nepal-specific factors."""

    def __init__(self, session):
        self.session = session

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
            select(Destination.trekking_routes).where(
                Destination.id == dest.id
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

        return min(score, 1.0)

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
            select(Destination.trekking_routes).where(
                Destination.id == dest.id
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
            select(Destination.trekking_routes).where(
                Destination.id == dest.id
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
