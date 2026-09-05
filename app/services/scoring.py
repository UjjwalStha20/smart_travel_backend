from typing import Dict, Any, Optional, Tuple
from uuid import UUID

from sqlmodel import Session, select

from app.models import User, Destination
from app.services.recommendation_service import RecommendationService
from app.services.content_based import ContentBasedFiltering
from app.services.structured_preferences import StructuredPreferenceMatcher
from app.services.contextual import ContextAwareFiltering
from app.services.collaborative import CollaborativeFiltering
from app.services.popularity import PopularityBased
from app.schemas.recommendations.basics import ComponentScores, RecommendationExplanation, PreferenceMatch, ContextMatch


class HybridScorer:
    """Hybrid scoring engine combining multiple recommendation components."""

    # Configurable weights (can be tuned per deployment)
    WEIGHTS = {
        "content": 0.35,
        "preference": 0.20,
        "context": 0.20,
        "collaborative": 0.15,
        "popularity": 0.10,
    }

    def __init__(self, session: Session):
        self.session = session
        self._content: Optional[ContentBasedFiltering] = None
        self._preferences: Optional[StructuredPreferenceMatcher] = None
        self._contextual: Optional[ContextAwareFiltering] = None
        self._collaborative: Optional[CollaborativeFiltering] = None
        self._popularity: Optional[PopularityBased] = None

    @property
    def content(self) -> ContentBasedFiltering:
        if self._content is None:
            self._content = ContentBasedFiltering(self.session)
        return self._content

    @property
    def preferences(self) -> StructuredPreferenceMatcher:
        if self._preferences is None:
            self._preferences = StructuredPreferenceMatcher(self.session)
        return self._preferences

    @property
    def contextual(self) -> ContextAwareFiltering:
        if self._contextual is None:
            self._contextual = ContextAwareFiltering(self.session)
        return self._contextual

    @property
    def collaborative(self) -> CollaborativeFiltering:
        if self._collaborative is None:
            self._collaborative = CollaborativeFiltering(self.session)
        return self._collaborative

    @property
    def popularity(self) -> PopularityBased:
        if self._popularity is None:
            self._popularity = PopularityBased(self.session)
        return self._popularity

    def compute_hybrid_score(
        self,
        user_id: UUID,
        all_destinations: List[Destination],
    ) -> List[Tuple[float, Destination, ComponentScores, RecommendationExplanation]]:
        """
        Compute hybrid recommendation scores for all destinations.

        Returns list of (final_score, destination, component_scores, explanation) tuples.
        """
        # Get user profile
        user_profile = self._build_user_profile(user_id)

        # Edge case: new user with no interaction history
        interaction_count = self._get_interaction_count(user_id)
        if interaction_count == 0:
            return self._cold_start_scores(user_profile, all_destinations)

        # Compute individual component scores
        content_scores = self.content.compute_user_destination_similarity(user_profile)
        pref_scores = self.preferences.compute_all_preference_scores(user_profile)
        context_scores = self.contextual.compute_all_context_scores(user_profile)
        collab_scores = self.collaborative.compute_all_collab_scores(
            user_profile, all_destinations
        )
        pop_scores = self.popularity._compute_all_popularity_scores()

        # Combine using configurable weights
        weights = self.WEIGHTS

        excluded_ids = self._get_excluded_destination_ids(user_id)

        results: List[Tuple[float, Destination, ComponentScores, RecommendationExplanation]] = []

        for dest in all_destinations:
            if dest.id in excluded_ids:
                continue

            # Get component scores (default to 0.5 neutral if missing)
            content_score = content_scores.get(str(dest.id), 0.5)
            pref_score = pref_scores.get(str(dest.id), 0.5)
            context_score = context_scores.get(str(dest.id), 0.5)
            collab_score = collab_scores.get(str(dest.id), 0.5)
            pop_score = pop_scores.get(str(dest.id), 0.5)

            # Compute weighted hybrid score
            final_score = (
                weights["content"] * content_score
                + weights["preference"] * pref_score
                + weights["context"] * context_score
                + weights["collaborative"] * collab_score
                + weights["popularity"] * pop_score
            )

            # Build component scores object
            comp_scores = ComponentScores(
                content=round(content_score, 4),
                preference=round(pref_score, 4),
                context=round(context_score, 4),
                collaborative=round(collab_score, 4),
                popularity=round(pop_score, 4),
            )

            # Generate explanation
            explanation = self._build_explanation(
                dest, content_score, pref_score, context_score, collab_score, pop_score, user_profile
            )

            results.append((final_score, dest, comp_scores, explanation))

        # Sort by final score descending
        results.sort(key=lambda x: x[0], reverse=True)

        return results

    def _build_user_profile(self, user_id: UUID) -> Dict[str, Any]:
        """Build comprehensive user profile for scoring."""
        # Get user preferences
        stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
        prefs = self.session.exec(stmt).first()

        # Get interaction count
        stmt = select(func.count(UserInteraction.id)).where(UserInteraction.user_id == user_id)
        interaction_count = self.session.exec(statement).one()

        # Build profile from preferences and interactions
        profile: Dict[str, Any] = {
            "user_id": str(user_id),
            "interaction_count": interaction_count,
            "categories": getattr(prefs, "preferred_categories", []) or [],
            "activities": getattr(prefs, "preferred_activities", []) or [],
            "budget_preference": getattr(prefs, "budget_preference", None),
            "typical_duration": getattr(prefs, "typical_duration", 0) or 0,
            "difficulty": getattr(prefs, "difficulty_preference", "moderate") or "moderate",
            "preferred_season": getattr(prefs, "preferred_season", []) or [],
            "travel_style": getattr(prefs, "travel_style", "cultural") or "cultural",
            "rating_profile": [],  # Would be populated from reviews
        }

        # Augment from interaction history
        if interaction_count > 0:
            stmt = select(UserInteraction).where(UserInteraction.user_id == user_id)
            interactions = self.session.exec(statement).all()

            for interaction in interactions:
                itype = interaction.interaction_type
                dest_id = interaction.destination_id

                # Track saved destinations
                if itype == "save":
                    profile.setdefault("saved_context", []).append(str(dest_id))

                # Track rated destinations
                if itype == "rating" and interaction.rating:
                    profile.setdefault("rating_history", []).append(
                        {"destination_id": str(dest_id), "rating": interaction.rating}
                    )

            # Get user trips for duration/budget info
            stmt = select(UserTrip).where(UserTrip.user_id == user_id)
            trips = self.session.exec(statement).all()
            for trip in trips:
                dest = self.session.get(Destination, trip.destination_id)
                if dest:
                    profile.setdefault("trip_history", []).append(
                        {
                            "destination_id": str(dest.id),
                            "name": dest.name,
                            "budget_type": getattr(trip, "budget_type", None),
                            "duration": self._calc_trip_duration(trip),
                        }
                    )

        return profile

    def _calc_trip_duration(self, trip: Any) -> int:
        """Calculate trip duration in days."""
        from datetime import date
        try:
            start = trip.start_date if hasattr(trip.start_date, 'isoformat') else date.fromisoformat(str(trip.start_date))
            end = trip.end_date if hasattr(trip.end_date, 'isoformat') else date.fromisoformat(str(trip.end_date))
            return (end - start).days if end and start else 0
        except (ValueError, TypeError, AttributeError):
            return 0

    def _get_interaction_count(self, user_id: UUID) -> int:
        """Get total interaction count for cold-start detection."""
        stmt = select(func.count(UserInteraction.id)).where(UserInteraction.user_id == user_id)
        return self.session.exec(statement).one() or 0

    def _cold_start_scores(
        self, user_profile: Dict[str, Any], all_destinations: List[Destination]
    ) -> List[Tuple[float, Destination, ComponentScores, RecommendationExplanation]]:
        """Generate scores for new users with no interaction history."""
        # Use popularity + content (based on declared preferences) as primary signals
        pop_scores = self.popularity._compute_all_popularity_scores()

        # Apply contextual filtering if we have season info
        preferred_season = user_profile.get("preferred_season", [])
        contextual_scores: Dict[str, float] = {}
        if preferred_season:
            ctx = self.contextual
            for dest in all_destinations:
                contextual_scores[str(dest.id)] = ctx._compute_context_score(dest, preferred_season)
        else:
            # No season info - neutral contextual scores
            contextual_scores = {str(dest.id): 0.8 for dest in all_destinations}

        # Build results
        weights = self.WEIGHTS
        excluded_ids = self._get_excluded_destination_ids_from_profile(user_profile)

        results: List[Tuple[float, Destination, ComponentScores, RecommendationExplanation]] = []

        for dest in all_destinations:
            if dest.id in excluded_ids:
                continue

            content_score = 0.5  # Neutral for new user (no profile)
            pref_score = 0.5  # Neutral for new user
            context_score = contextual_scores.get(str(dest.id), 0.8)
            collab_score = 0.5  # Neutral for new user
            pop_score = pop_scores.get(str(dest.id), 0.5)

            final_score = (
                weights["content"] * content_score
                + weights["preference"] * pref_score
                + weights["context"] * context_score
                + weights["collaborative"] * collab_score
                + weights["popularity"] * pop_score
            )

            comp_scores = ComponentScores(
                content=round(content_score, 4),
                preference=round(pref_score, 4),
                context=round(context_score, 4),
                collaborative=round(collab_score, 4),
                popularity=round(pop_score, 4),
            )

            # Cold-start explanation emphasizing popularity and available preferences
            reason_parts = []
            if pop_score > 0.5:
                reason_parts.append("popular destination")
            if preferred_season:
                # Check if destination matches preferred season
                dest_season = getattr(dest, "best_time", []) or []
                if any(s in preferred_season for s in dest_season):
                    reason_parts.append("matches your preferred season")
            if not reason_parts:
                reason_parts.append("well-rated destination")

            explanation = RecommendationExplanation(
                reason_summary="; ".join(reason_parts)
            )

            results.append((final_score, dest, comp_scores, explanation))

        # Sort by score
        results.sort(key=lambda x: x[0], reverse=True)

        return results

    def _get_excluded_destination_ids(self, user_id: UUID) -> set:
        """Get destination IDs user has already saved or visited."""
        # Saved destinations
        stmt = select(SavedDestination.destination_id).where(
            SavedDestination.user_id == user_id
        )
        saved = set(self.session.exec(statement).all() or [])

        # User trips destinations
        stmt = select(UserTrip.destination_id).where(UserTrip.user_id == user_id)
        tripped = set(self.session.exec(statement).all() or [])

        return saved | tripped

    def _get_excluded_destination_ids_from_profile(self, user_profile: Dict[str, Any]) -> set:
        """Get excluded dest IDs from user profile data."""
        # Simplified: return empty for cold-start without user_id
        # In full implementation, would query saved/tripped from profile
        return set()

    def _build_explanation(
        self,
        dest: Destination,
        content_score: float,
        pref_score: float,
        context_score: float,
        collab_score: float,
        pop_score: float,
        user_profile: Dict[str, Any],
    ) -> RecommendationExplanation:
        """Build human-readable explanation for the recommendation."""
        matched_prefs: List[PreferenceMatch] = []
        contextual_factors: List[ContextMatch] = []

        # Analyze component scores and generate explanations
        reason_parts: List[str] = []

        # Content-based reasons
        if content_score > 0.3:
            # Check what features matched
            cat = getattr(dest, "category", None)
            if cat:
                reason_parts.append(f"matches {cat} interests")
        if content_score > 0.5:
            reason_parts.append("aligns with your travel style")

        # Preference-based reasons
        if pref_score > 0.3:
            budget = user_profile.get("budget_preference")
            if budget:
                reason_parts.append(f"fits your {budget} budget")
            activities = user_profile.get("activities", [])
            if activities:
                reason_parts.append(f"matches your activity preferences")

        if pref_score > 0.5:
            duration = user_profile.get("typical_duration", 0)
            if duration and duration > 0:
                reason_parts.append(f"fits {duration}-day trip length")

        # Contextual reasons
        if context_score > 0.3:
            selected_season = user_profile.get("preferred_season", [])
            if selected_season:
                dest_season = getattr(dest, "best_time", []) or []
                matching = set(s.lower() for s in dest_season) & set(s.lower() for s in selected_season)
                if matching:
                    reason_parts.append(f"suitable for {', '.join(matching)} season")

        # Permit info
        if getattr(dest, "permit_required", False):
            reason_parts.append("permit required (plan ahead)")

        # Collaborative reasons
        if collab_score > 0.3:
            reason_parts.append("travelers with similar tastes recommend this")

        # Popularity reasons
        if pop_score > 0.5:
            reason_parts.append("highly rated by other travelers")

        # Fallback if no specific reasons generated
        if not reason_parts:
            reason_parts.append("recommended for you")

        explanation = RecommendationExplanation(
            reason_summary="; ".join(reason_parts)
            if reason_parts
            else None,
            matched_preferences=matched_prefs,
            contextual_factors=contextual_factors,
        )

        return explanation


class HybridScoreOutput:
    """Output model for hybrid scores."""
    pass
