from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlmodel import select

from app.models import User, Destination, TrekkingRoute, UserPreferences, UserInteraction, UserTrip, Review, SavedDestination


class StructuredPreferenceMatcher:
    """Match destinations against structured user preferences."""

    def __init__(self, session):
        self.session = session

    def compute_all_preference_scores(
        self, user_profile: Dict[str, Any]
    ) -> Dict[str, float]:
        """Compute preference matching scores for all destinations."""
        destinations = self.session.exec(select(Destination)).all()
        preferences = self._build_preference_profile(user_profile)
        scored: Dict[str, float] = {}
        for dest in destinations:
            score = self._compute_destination_preference_score(dest, preferences)
            scored[str(dest.id)] = score
        return scored

    def _build_preference_profile(
        self, user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build a preference profile from the user model data."""
        stmt = select(UserPreferences).where(UserPreferences.user_id == user_profile.get("user_id"))
        prefs = self.session.exec(stmt).first()

        profile: Dict[str, Any] = {
            "preferred_categories": getattr(prefs, "preferred_categories", []) or [],
            "preferred_activities": getattr(prefs, "preferred_activities", []) or [],
            "budget_preference": getattr(prefs, "budget_preference", None),
            "typical_duration": getattr(prefs, "typical_duration", 0) or 0,
            "difficulty_preference": getattr(prefs, "difficulty_preference", "moderate") or "moderate",
            "preferred_season": getattr(prefs, "preferred_season", []) or [],
            "travel_style": getattr(prefs, "travel_style", "cultural") or "cultural",
        }

        user_id = user_profile.get("user_id")
        if user_id:
            # From saved destinations
            stmt = select(SavedDestination).where(SavedDestination.user_id == user_id)
            saved = self.session.exec(stmt).all()
            for save in saved:
                dest = self.session.get(Destination, save.destination_id)
                if dest:
                    if dest.category and dest.category.value not in profile["preferred_categories"]:
                        pass

            # From user trips
            stmt = select(UserTrip).where(UserTrip.user_id == user_id)
            trips = self.session.exec(stmt).all()
            for trip in trips:
                dest = self.session.get(Destination, trip.destination_id)
                if dest:
                    bt = getattr(trip, "budget_type", None)
                    if bt:
                        profile["budget_preference"] = bt
                    pt = getattr(trip, "pace_type", None)
                    if pt:
                        profile["difficulty_preference"] = str(pt)
                    if trip.start_date and trip.end_date:
                        from datetime import date
                        try:
                            start = date.fromisoformat(str(trip.start_date))
                            end = date.fromisoformat(str(trip.end_date))
                            duration = (end - start).days
                            if duration > 0:
                                profile["typical_duration"] = max(
                                    profile["typical_duration"], duration
                                )
                        except (ValueError, TypeError):
                            pass
                    bt_dest = getattr(dest, "best_time", []) or []
                    profile["preferred_season"] = list(
                        set(profile["preferred_season"] + bt_dest)
                    )

            # From reviews
            stmt = select(Review).where(Review.user_id == user_id)
            reviews = self.session.exec(stmt).all()
            for review in reviews:
                dest = self.session.get(Destination, review.destination_id)
                if dest:
                    pass

        return profile

    def _compute_destination_preference_score(
        self, dest: Destination, preferences: Dict[str, Any]
    ) -> float:
        """Compute preference matching score for a single destination."""
        scores: List[float] = []

        # Budget matching
        budget_score = self._match_budget(dest, preferences.get("budget_preference"))
        scores.append(budget_score * 0.25)

        # Duration matching
        duration_score = self._match_duration(dest, preferences.get("typical_duration"))
        scores.append(duration_score * 0.20)

        # Difficulty matching
        difficulty_score = self._match_difficulty(dest, preferences.get("difficulty_preference"))
        scores.append(difficulty_score * 0.20)

        # Interests matching
        interest_score = self._match_interests(dest, preferences)
        scores.append(interest_score * 0.25)

        # Season matching
        season_score = self._match_season(dest, preferences.get("preferred_season"))
        scores.append(season_score * 0.10)

        total_score = sum(scores)
        return min(total_score, 1.0)

    def _match_budget(self, dest: Destination, budget_preference: Optional[str]) -> float:
        """Match destination against user's budget preference."""
        if not budget_preference:
            return 0.5
        rating = getattr(dest, "rating", None)
        if rating is None:
            return 0.5
        rating_norm = (rating - 1) / (5 - 1)
        if budget_preference == "budget":
            return min(rating_norm + 0.3, 1.0)
        elif budget_preference == "luxury":
            return min(rating_norm * 1.2, 1.0)
        else:
            return rating_norm

    def _match_duration(
        self, dest: Destination, typical_duration: Optional[int]
    ) -> float:
        """Match destination against user's typical trip duration."""
        if typical_duration is None or typical_duration <= 0:
            return 0.5
        rec_days = 0
        routes = self.session.exec(
            select(TrekkingRoute).where(TrekkingRoute.destination_id == dest.id)
        ).all()
        if routes:
            for route in routes:
                rdays = getattr(route, "recommended_days", None)
                if rdays:
                    rec_days = max(rec_days, rdays)
        if best_time := getattr(dest, "best_time", []):
            rec_days = max(rec_days, len(best_time) * 7 // 3)
        if rec_days <= 0:
            return 0.5
        ratio = typical_duration / rec_days if rec_days > 0 else 1.0
        if 0.5 <= ratio <= 2.0:
            return 1.0
        elif ratio < 0.5:
            return 0.7
        else:
            return max(0.3, 1.0 - 0.2 * (ratio - 2.0))

    def _match_difficulty(
        self, dest: Destination, difficulty_preference: Optional[str]
    ) -> float:
        """Match destination difficulty against user preference."""
        if not difficulty_preference:
            return 0.5
        actual_difficulty = None
        routes = self.session.exec(
            select(TrekkingRoute).where(TrekkingRoute.destination_id == dest.id)
        ).all()
        if routes:
            for route in routes:
                actual_difficulty = getattr(route, "difficulty", None)
                if actual_difficulty:
                    break
        if actual_difficulty is None:
            cat = getattr(dest, "category", None)
            if cat and hasattr(cat, "value"):
                actual_difficulty = cat.value
            else:
                actual_difficulty = str(cat) if cat else "moderate"
        difficulty_map = {"easy": 1, "moderate": 2, "hard": 3}
        pref_norm = difficulty_map.get(str(difficulty_preference).lower(), 2)
        actual_norm = difficulty_map.get(str(actual_difficulty).lower(), 2)
        if pref_norm == actual_norm:
            return 1.0
        elif abs(pref_norm - actual_norm) == 1:
            return 0.7
        else:
            return 0.3

    def _match_interests(self, dest: Destination, preferences: Dict[str, Any]) -> float:
        """Match destination against user's preferred categories and activities."""
        score = 0.0
        count = 0
        preferred_categories = preferences.get("preferred_categories", [])
        dest_category = getattr(dest, "category", None)
        if dest_category:
            dest_cat_str = dest_category.value if hasattr(dest_category, "value") else str(dest_category)
            if dest_cat_str in preferred_categories:
                score += 1.0
            elif any(
                cat in str(dest_cat_str).lower() or str(dest_cat_str).lower() in cat
                for cat in preferred_categories
            ):
                score += 0.5
            count += 1
        preferred_activities = preferences.get("preferred_activities", [])
        dest_desc = (getattr(dest, "description", "") or "").lower()
        if preferred_activities and dest_desc:
            for activity in preferred_activities:
                act_lower = str(activity).lower()
                if act_lower in dest_desc:
                    score += 1.0
                keywords = act_lower.split()
                if any(kw in dest_desc for kw in keywords):
                    score += 0.5
            count += max(1, len(preferred_activities))
        if count > 0:
            return min(score / count, 1.0)
        return 0.5

    def _match_season(self, dest: Destination, preferred_season: Optional[List[str]]) -> float:
        """Match destination's best_time against user's preferred season."""
        if not preferred_season:
            return 0.5
        dest_season = getattr(dest, "best_time", []) or []
        if not dest_season:
            return 0.5
        dest_season_lower = [s.lower() for s in dest_season]
        preferred_lower = [s.lower() for s in preferred_season]
        exact_matches = set(dest_season_lower) & set(preferred_lower)
        if exact_matches:
            return min(len(exact_matches) / len(dest_season), 1.0)
        season_keywords = {
            "spring": ["march", "april", "may"],
            "autumn": ["september", "october", "november"],
            "winter": ["december", "january", "february"],
            "summer": ["june", "july", "august"],
        }
        score = 0.0
        for ps in preferred_lower:
            for ds in dest_season_lower:
                for kw, kws in season_keywords.items():
                    if kw in ps or kw in ds:
                        score += 0.25
        if score > 0 and not exact_matches:
            return min(score, 0.7)
        elif not exact_matches and score == 0:
            return 0.4
        return min(score, 1.0)


class PreferenceScoreOutput:
    """Output model for preference scores."""
    pass
