from typing import Dict, Any, List, Optional
from uuid import UUID

import numpy as np
from sqlmodel import Session, select
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models import User, Destination, UserInteraction, Review, UserTrip
from app.schemas.recommendations.basics import ComponentScores, SimilarityScore


class ContentBasedFiltering:
    """Content-based filtering using TF-IDF and cosine similarity."""

    def __init__(self, session):
        self.session = session
        self._destination_vectors: Optional[np.ndarray] = None
        self._destination_ids: Optional[List[UUID]] = None
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._is_trained = False

    def _prepare_destination_vectors(self) -> None:
        """Prepare TF-IDF vectors for all destinations."""
        destinations = self.session.exec(select(Destination)).all()

        # Build text corpus from destination features
        corpus = []
        for dest in destinations:
            features = self._extract_destination_text(dest)
            corpus.append(features)

        if not corpus or all(not c.strip() for c in corpus):
            # Fallback: use destination names only
            corpus = [dest.name or "Unnamed destination" for dest in destinations]

        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            lowercase=True,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
        )

        try:
            self._destination_vectors = self._vectorizer.fit_transform(corpus)
            self._destination_ids = [dest.id for dest in destinations]
            self._is_trained = True
        except ValueError:
            # Fallback if TF-IDF fails (e.g., all empty strings)
            self._is_trained = False

    def _extract_destination_text(self, dest: Destination) -> str:
        """Extract textual features from a destination for TF-IDF."""
        parts = [dest.name or ""]

        # Category
        cat = getattr(dest, "category", None)
        if cat:
            parts.append(str(cat))

        # Best time (seasonal info)
        best_time = getattr(dest, "best_time", []) or []
        if best_time:
            parts.append(" ".join(str(b) for b in best_time))

        # Description
        desc = getattr(dest, "description", None)
        if desc:
            parts.append(str(desc)[:500])  # Truncate for efficiency

        # Attraction types if available (via relationship)
        # Note: We avoid heavy joins; use what's directly on Destination

        return " ".join(parts)

    def compute_user_destination_similarity(
        self, user_profile: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Compute content-based similarity between user profile and all destinations.

        Returns dict mapping destination_id -> similarity_score [0, 1]
        """
        if not self._is_trained:
            self._prepare_destination_vectors()

        if not self._is_trained or self._destination_vectors is None:
            # Return uniform scores if cannot compute
            from app.services.recommendation_service import RecommendationService
            svc = RecommendationService.__new__(RecommendationService)
            # Can't easily get session here, so return zeros
            return {}

        # Build user vector from profile
        user_vector = self._build_user_vector(user_profile)

        if user_vector is None or self._destination_vectors is None:
            return {}

        # Compute cosine similarity
        try:
            similarities = cosine_similarity(user_vector, self._destination_vectors).flatten()
        except ValueError:
            return {}

        # Convert to dict
        scores: Dict[str, float] = {}
        for i, dest_id in enumerate(self._destination_ids):
            scores[str(dest_id)] = float(similarities[i])

        # Normalize to [0, 1] using sigmoid if needed
        # Cosine similarity is already [-1, 1], but our vectors should produce [0, 1]
        # Apply min-max normalization for safety
        min_score = min(scores.values()) if scores else 0
        max_score = max(scores.values()) if scores else 1

        if max_score > min_score:
            scores = {
                k: (v - min_score) / (max_score - min_score)
                for k, v in scores.items()
            }
        else:
            # All scores equal, set to midpoint
            scores = {k: 0.5 for k in scores}

        return scores

    def _build_user_vector(self, user_profile: Dict[str, Any]) -> Optional[np.ndarray]:
        """Build a user preference vector from the user profile."""
        if not self._vectorizer or not self._is_trained:
            return None

        # Extract text features from user's interaction history
        features = self._extract_user_features(user_profile)

        if not features or not features.strip():
            # User has no feature text; use default
            features = "travel culture nature adventure"

        try:
            user_vector = self._vectorizer.transform([features])
            return user_vector
        except ValueError:
            return None

    def _extract_user_features(self, user_profile: Dict[str, Any]) -> str:
        """Extract textual features from user profile for vectorization."""
        parts = []

        # Preferred categories
        categories = user_profile.get("categories", [])
        if categories:
            parts.extend(str(c) for c in categories)

        # Preferred activities
        activities = user_profile.get("activities", [])
        if activities:
            parts.extend(str(a) for a in activities)

        # Budget preference
        budget = user_profile.get("budget_type", "")
        if budget:
            parts.append(budget)

        # Typical duration
        duration = user_profile.get("typical_duration", 0)
        if duration and duration > 0:
            parts.append(f"{duration} day trip")

        # Difficulty preference
        difficulty = user_profile.get("difficulty", "moderate")
        parts.append(str(difficulty))

        # Preferred season
        season = user_profile.get("preferred_season", [])
        if season:
            parts.append(" ".join(str(s) for s in season))

        # Travel style
        style = user_profile.get("travel_style", "cultural")
        parts.append(str(style))

        # Rating profile - destinations user rated highly
        rating_profile = user_profile.get("rating_profile", [])
        highly_rated = [
            r.get("destination_name", "") for r in rating_profile if r.get("rating", 0) >= 4
        ]
        if highly_rated:
            parts.append(" ".join(highly_rated))

        return " ".join(parts) if parts else ""


class SimilarityScoreOutput(SimilarityScore):
    """Output model for content similarity scores."""
    pass
