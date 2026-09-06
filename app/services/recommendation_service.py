from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from sqlmodel import Session, select, func

from app.models import User, Destination, UserPreferences, UserInteraction, Review, UserTrip, SavedDestination, RecommendationLog
from app.services.content_based import ContentBasedFiltering
from app.services.structured_preferences import StructuredPreferenceMatcher
from app.services.contextual import ContextAwareFiltering, WEATHER_NOTES
from app.services.collaborative import CollaborativeFiltering
from app.services.popularity import PopularityBased
from app.schemas.recommendations.basics import (
    SimilarityScore,
    PreferenceMatch,
    ContextMatch,
    ComponentScores,
    RecommendationExplanation,
    RecommendationBase,
    RecommendationCreate,
    RecommendationRead,
    RecommendationSummary,
)


class RecommendationService:
    """Main recommendation service orchestrator."""

    def __init__(self, session: Session):
        self.session = session

    # ---- Public API --------------------------------------------------------

    def get_recommendations(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> List[RecommendationRead]:
        """Get personalized recommendations for a user."""
        # Load user data
        user = self.session.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check for interaction history
        interaction_count = self._get_interaction_count(user_id)

        # Build user profile
        user_profile = self._build_user_profile(user_id, interaction_count)

        # Load candidate destinations
        all_destinations = self._get_all_destinations()

        # Handle cold-start
        if interaction_count == 0:
            return self._cold_start_recommendations(
                user, all_destinations, limit
            )

        # Execute scoring pipeline
        scored = self._score_destinations(
            user_profile, all_destinations, user_id
        )

        # Rank and return top N
        ranked = sorted(scored, key=lambda x: x[0], reverse=True)[:limit]

        return self._to_read_models(ranked, all_destinations, user_id)

    def record_interaction(
        self,
        user_id: UUID,
        destination_id: UUID,
        interaction_type: str,
        rating: Optional[int] = None,
    ) -> UserInteraction:
        """Record a user-interaction for collaborative learning."""
        # Verify user and destination exist
        user = self.session.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        dest = self.session.get(Destination, destination_id)
        if not dest:
            raise ValueError(f"Destination {destination_id} not found")

        # Check for existing interaction
        stmt = (
            select(UserInteraction)
            .where(
                UserInteraction.user_id == user_id,
                UserInteraction.destination_id == destination_id,
                UserInteraction.interaction_type == interaction_type,
            )
        )
        existing = self.session.exec(stmt).first()
        if existing:
            # Update timestamp if needed
            existing.created_at = func.now()
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing

        interaction = UserInteraction(
            user_id=user_id,
            destination_id=destination_id,
            interaction_type=interaction_type,
            rating=rating,
        )
        self.session.add(interaction)
        self.session.commit()
        self.session.refresh(interaction)

        # Log the recommendation if this was a rating
        if interaction_type == "rating":
            self._log_recommendation(user_id, destination_id, rating=rating)

        return interaction

    def log_recommendation(
        self,
        user_id: UUID,
        destination_id: UUID,
        component_scores: Dict[str, float],
        final_score: float,
        algorithm_version: str = "hybrid_v1",
    ) -> RecommendationLog:
        """Log a recommendation for audit and learning."""
        log_entry = RecommendationLog(
            user_id=user_id,
            destination_id=destination_id,
            final_score=final_score,
            component_scores=component_scores,
            algorithm_version=algorithm_version,
        )
        self.session.add(log_entry)
        self.session.commit()
        self.session.refresh(log_entry)
        return log_entry

    # ---- Internal Methods ------------------------------------------------

    def _get_interaction_count(self, user_id: UUID) -> int:
        """Get total interaction count for cold-start detection."""
        stmt = select(func.count(UserInteraction.id)).where(
            UserInteraction.user_id == user_id
        )
        count = self.session.exec(stmt).one()
        return count

    def _build_user_profile(self, user_id: UUID, interaction_count: int) -> Dict[str, Any]:
        """Build comprehensive user profile from all available data."""
        profile: Dict[str, Any] = {
            "user_id": str(user_id),
            "interaction_count": interaction_count,
            "categories": [],  # preferred categories
            "activities": [],  # preferred activities
            "budget_type": None,
            "typical_duration": 0,
            "difficulty": "moderate",  # default
            "preferred_season": [],
            "travel_style": "cultural",  # default
            "rating_profile": [],  # rated destinations
            "saved_destinations": [],
            "tripped_destinations": [],
        }

        # Load user preferences if exists
        stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
        prefs = self.session.exec(stmt).first()
        if prefs:
            profile["categories"] = getattr(prefs, "preferred_categories", []) or []
            profile["activities"] = getattr(prefs, "preferred_activities", []) or []
            profile["budget_type"] = getattr(prefs, "budget_preference", None)
            profile["typical_duration"] = getattr(prefs, "typical_duration", 0) or 0
            profile["difficulty"] = getattr(prefs, "difficulty_preference", "moderate") or "moderate"
            profile["preferred_season"] = getattr(prefs, "preferred_season", []) or []
            profile["travel_style"] = getattr(prefs, "travel_style", "cultural") or "cultural"

        # Load interaction history
        stmt = select(UserInteraction).where(UserInteraction.user_id == user_id)
        interactions = self.session.exec(stmt).all()
        for interaction in interactions:
            itype = interaction.interaction_type
            dest_id = interaction.destination_id

            if itype == "rating" and interaction.rating:
                profile["rating_profile"].append(
                    {"destination_id": str(dest_id), "rating": interaction.rating}
                )
            elif itype == "save":
                profile["saved_destinations"].append(str(dest_id))

        # Load user trips
        stmt = select(UserTrip).where(UserTrip.user_id == user_id)
        trips = self.session.exec(stmt).all()
        for trip in trips:
            dest = self.session.get(Destination, trip.destination_id)
            if dest:
                profile["tripped_destinations"].append(
                    {
                        "id": str(dest.id),
                        "name": dest.name,
                        "category": getattr(dest, "category", None),
                        "best_time": getattr(dest, "best_time", []) or [],
                        "rating": getattr(dest, "rating", None),
                        "difficulty": getattr(trip, "pace_type", None),
                        "budget_type": getattr(trip, "budget_type", None),
                    }
                )

        # Load reviews giving by user
        stmt = select(Review).where(Review.user_id == user_id)
        reviews = self.session.exec(stmt).all()
        for review in reviews:
            dest = self.session.get(Destination, review.destination_id)
            if dest:
                profile["rating_profile"].append(
                    {
                        "destination_id": str(dest.id),
                        "rating": review.rating,
                        "destination_name": dest.name,
                    }
                )

        return profile

    def _get_all_destinations(self) -> List[Destination]:
        """Load all destinations available for recommendation."""
        stmt = select(Destination)
        destinations = self.session.exec(stmt).all()
        return destinations

    def _cold_start_recommendations(
        self,
        user: User,
        all_destinations: List[Destination],
        limit: int,
    ) -> List[RecommendationRead]:
        """Generate recommendations for new users with no interaction history."""
        from .content_based import ContentBasedFiltering
        from .popularity import PopularityBased
        from .contextual import ContextAwareFiltering

        # Use popularity as primary signal for cold-start
        popularity = PopularityBased(self.session)
        popular_dests = popularity.get_popular_destinations(limit=limit * 2)

        # Apply contextual filtering
        contextual = ContextAwareFiltering(self.session)
        filtered = contextual.filter_by_context(popular_dests, user)

        # Build recommendation objects
        results = []
        for rank, (dest, score) in enumerate(filtered[:limit], start=1):
            comp_scores = ComponentScores(
                popularity=min(score, 1.0),
                content=0.0,  # No profile to compute content from
                preference=0.0,
                context=contextual.get_context_score(dest, {"user_id": str(user.id)}),
                collaborative=0.0,
            )

            # Use popularity-based explanation
            reason = f"Popular destination suitable for general travel"
            note = WEATHER_NOTES.get(str(dest.id))
            if note:
                reason = f"{reason}. {note}"
            explanation = RecommendationExplanation(
                reason_summary=reason
            )

            results.append(
                RecommendationRead(
                    destination_id=dest.id,
                    name=dest.name,
                    category=dest.category.value
                    if hasattr(dest.category, "value")
                    else str(dest.category),
                    final_score=round(score, 4),
                    component_scores=comp_scores,
                    explanation=explanation,
                    rank=rank,
                )
            )

        return results

    def _score_destinations(
        self,
        user_profile: Dict[str, Any],
        all_destinations: List[Destination],
        user_id: UUID,
    ) -> List[Tuple[float, Destination]]:
        """Score all destinations using the hybrid formula."""
        from .content_based import ContentBasedFiltering
        from .structured_preferences import StructuredPreferenceMatcher
        from .contextual import ContextAwareFiltering
        from .collaborative import CollaborativeFiltering
        from .popularity import PopularityBased

        # Initialize all sub-modules
        content = ContentBasedFiltering(self.session)
        preferences = StructuredPreferenceMatcher(self.session)
        contextual = ContextAwareFiltering(self.session)
        collaborative = CollaborativeFiltering(self.session)
        popularity = PopularityBased(self.session)

        # Get popularity scores for all destinations
        pop_scores = popularity._compute_all_popularity_scores()

        # Content-based scores
        content_scores = content.compute_user_destination_similarity(user_profile)

        # Structured preference scores
        pref_scores = preferences.compute_all_preference_scores(user_profile)

        # Context-aware scores
        context_scores = contextual.compute_all_context_scores(user_profile)

        # Collaborative filtering scores
        collab_scores = collaborative.compute_all_collab_scores(user_profile, all_destinations)

        # Combine using hybrid weights
        content_weight = 0.35
        pref_weight = 0.20
        context_weight = 0.20
        collab_weight = 0.15
        pop_weight = 0.10

        scored: List[Tuple[float, Destination]] = []

        excluded_ids = self._get_excluded_destination_ids(user_id)

        for dest in all_destinations:
            if dest.id in excluded_ids:
                continue

            # Get component scores (default to 0.5 if not available)
            content_score = content_scores.get(str(dest.id), 0.5)
            pref_score = pref_scores.get(str(dest.id), 0.5)
            context_score = context_scores.get(str(dest.id), 0.5)
            collab_score = collab_scores.get(str(dest.id), 0.5)
            pop_score = pop_scores.get(str(dest.id), 0.5)

            # Compute weighted hybrid score
            final_score = (
                content_weight * content_score
                + pref_weight * pref_score
                + context_weight * context_score
                + collab_weight * collab_score
                + pop_weight * pop_score
            )

            scored.append((final_score, dest))

        return scored

    def _get_excluded_destination_ids(self, user_id: UUID) -> set:
        """Get destination IDs user has already saved or visited."""
        # Saved destinations
        stmt = select(SavedDestination.destination_id).where(
            SavedDestination.user_id == user_id
        )
        saved = set(self.session.exec(stmt).all())

        # User trips destinations
        stmt = select(UserTrip.destination_id).where(UserTrip.user_id == user_id)
        tripped = set(self.session.exec(stmt).all())

        return saved | tripped

    def _to_read_models(
        self,
        scored: List[Tuple[float, Destination]],
        all_destinations: List[Destination],
        user_id: UUID,
    ) -> List[RecommendationRead]:
        """Convert scored tuples to API response models."""
        # Build lookup for component scores and explanations
        component_scores_map: Dict[str, ComponentScores] = {}

        results = []
        for rank, (score, dest) in enumerate(scored, start=1):
            dest_id = dest.id

            # Compute component scores for this destination if not already done
            if dest_id not in component_scores_map:
                from .content_based import ContentBasedFiltering
                from .structured_preferences import StructuredPreferenceMatcher
                from .contextual import ContextAwareFiltering
                from .collaborative import CollaborativeFiltering
                from .popularity import PopularityBased

                content = ContentBasedFiltering(self.session)
                preferences = StructuredPreferenceMatcher(self.session)
                contextual = ContextAwareFiltering(self.session)
                collaborative = CollaborativeFiltering(self.session)
                popularity = PopularityBased(self.session)

                content_score = content.compute_user_destination_similarity(
                    {"user_id": str(user_id)}
                ).get(str(dest_id), 0.5)
                pref_score = preferences.compute_all_preference_scores(
                    {"user_id": str(user_id)}
                ).get(str(dest_id), 0.5)
                context_score = contextual.compute_all_context_scores(
                    {"user_id": str(user_id)}
                ).get(str(dest_id), 0.5)
                collab_score = collaborative.compute_all_collab_scores(
                    {"user_id": str(user_id)}, all_destinations
                ).get(str(dest_id), 0.5)
                pop_score = popularity._compute_all_popularity_scores().get(str(dest_id), 0.5)

                comp = ComponentScores(
                    content=round(content_score, 4),
                    preference=round(pref_score, 4),
                    context=round(context_score, 4),
                    collaborative=round(collab_score, 4),
                    popularity=round(pop_score, 4),
                )
                component_scores_map[dest_id] = comp
            else:
                comp = component_scores_map[dest_id]

            # Build explanation
            reason = self._generate_reason(dest, comp)
            note = WEATHER_NOTES.get(str(dest_id))
            if note:
                reason = f"{reason}. {note}" if reason else note
            explanation = RecommendationExplanation(
                reason_summary=reason
            )

            results.append(
                RecommendationRead(
                    destination_id=dest_id,
                    name=dest.name,
                    category=dest.category.value
                    if hasattr(dest.category, "value")
                    else str(dest.category),
                    final_score=round(score, 4),
                    component_scores=comp,
                    explanation=explanation,
                    rank=rank,
                )
            )

        return results

    def _generate_reason(
        self,
        dest: Destination,
        scores: ComponentScores,
    ) -> Optional[str]:
        """Generate human-readable explanation for recommendation."""
        reasons = []

        if scores.content > 0.3:
            reasons.append("Matches your travel preferences")

        if scores.preference > 0.3:
            budget = "budget-friendly" if scores.preference > 0.5 else ""
            reasons.append(f"Fits your {budget or ""} preferences" if budget else "Fits your preferences")

        if scores.context > 0.3:
            reasons.append("Suitable for current season")

        if scores.collaborative > 0.3:
            reasons.append("Liked by travelers with similar tastes")

        if scores.popularity > 0.3:
            reasons.append("Popular among travelers")

        if not reasons:
            return None

        return "; ".join(reasons)


# Convenience function for FastAPI dependency injection
def get_recommendation_service(session: Session) -> RecommendationService:
    """Dependency injection for recommendation service."""
    return RecommendationService(session)
