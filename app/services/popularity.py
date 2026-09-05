from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlmodel import select, func

from app.models import User, Destination, UserInteraction, Review


class PopularityBased:
    """Popularity-based recommendation component."""

    def __init__(self, session):
        self.session = session

    def get_popular_destinations(self, limit: int = 10) -> List[tuple]:
        """
        Get most popular destinations based on interaction signals.

        Returns list of (destination, score) tuples sorted by popularity.
        """
        # Compute popularity scores for all destinations
        pop_scores = self._compute_all_popularity_scores()

        # Sort by score descending and return top N
        sorted_dests = sorted(pop_scores.items(), key=lambda x: x[1], reverse=True)
        result = []
        for dest_id, score in sorted_dests[:limit]:
            # dest_id is already a string (converted in _compute_all_popularity_scores)
            dest = self.session.get(Destination, UUID(dest_id))
            if dest:
                result.append((dest, round(score, 4)))

        return result

    def _compute_all_popularity_scores(self) -> Dict[str, float]:
        """Compute popularity scores for all destinations."""
        # Gather multiple popularity signals
        signals = self._gather_popularity_signals()

        # Combine signals into final popularity score
        popularity: Dict[str, float] = {}

        # Get all destination IDs as strings
        stmt = select(Destination.id)
        all_dest = self.session.exec(stmt).all()
        # Convert to strings
        all_dest_str = [str(d) for d in all_dest]

        for dest_id in all_dest_str:
            # Start with base score
            base_score = 0.0

            # Add contributions from each signal
            for signal_type, signal_data in signals.items():
                if dest_id in signal_data:
                    base_score += signal_data[dest_id]

            # Normalize: divide by number of signals
            num_signals = len(signals)
            if num_signals > 0:
                popularity[dest_id] = min(base_score / num_signals, 1.0)
            else:
                popularity[dest_id] = 0.0

        return popularity

    def _gather_popularity_signals(self) -> Dict[str, Dict[str, float]]:
        """Gather all popularity signals from interaction data."""
        signals: Dict[str, Dict[str, float]] = {}

        # Signal 1: Save count (weight 3)
        stmt = (
            select(UserInteraction.destination_id, func.count(UserInteraction.id).label("cnt"))
            .where(UserInteraction.interaction_type == "save")
            .group_by(UserInteraction.destination_id)
        )
        saves = self.session.exec(stmt).all()
        if "save" not in signals:
            signals["save"] = {}
        for dest_id, count in saves:
            signals["save"][str(dest_id)] = min(float(count) / 10.0, 1.0)

        # Signal 2: Rating average (weight 4)
        stmt = (
            select(UserInteraction.destination_id, func.avg(UserInteraction.rating).label("avg_rating"))
            .where(UserInteraction.interaction_type == "rating")
            .group_by(UserInteraction.destination_id)
        )
        ratings = self.session.exec(stmt).all()
        if "rating" not in signals:
            signals["rating"] = {}
        for dest_id, avg_rating in ratings:
            if avg_rating is not None:
                normalized = (float(avg_rating) - 1) / 4.0  # 1-5 -> 0-1
                signals["rating"][str(dest_id)] = min(normalized, 1.0)

        # Signal 3: Itinerary creation (weight 5)
        stmt = (
            select(UserInteraction.destination_id, func.count(UserInteraction.id).label("cnt"))
            .where(UserInteraction.interaction_type == "itinerary")
            .group_by(UserInteraction.destination_id)
        )
        itineraries = self.session.exec(stmt).all()
        if "itinerary" not in signals:
            signals["itinerary"] = {}
        for dest_id, count in itineraries:
            signals["itinerary"][str(dest_id)] = min(float(count) / 5.0, 1.0)

        # Signal 4: View count (weight 1)
        stmt = (
            select(UserInteraction.destination_id, func.count(UserInteraction.id).label("cnt"))
            .where(UserInteraction.interaction_type == "view")
            .group_by(UserInteraction.destination_id)
        )
        views = self.session.exec(stmt).all()
        if "view" not in signals:
            signals["view"] = {}
        for dest_id, count in views:
            signals["view"][str(dest_id)] = min(float(count) / 50.0, 1.0)

        # Signal 5: Review count and rating (from Review model)
        stmt = (
            select(Review.destination_id, func.count(Review.id).label("cnt"), func.avg(Review.rating).label("avg_r"))
            .group_by(Review.destination_id)
        )
        reviews = self.session.exec(stmt).all()
        if "review" not in signals:
            signals["review"] = {}
        for dest_id, cnt, avg_r in reviews:
            if avg_r is not None:
                normalized = (float(avg_r) - 1) / 4.0
                review_factor = min(float(cnt) / 20.0, 1.0)
                signals["review"][str(dest_id)] = min(normalized * review_factor, 1.0)

        return signals

    def get_all_popularity_scores(self) -> Dict[str, float]:
        """Get all destination popularity scores (alias for _compute_all_popularity_scores)."""
        return self._compute_all_popularity_scores()

    def get_normalized_popularity(self, dest_id: UUID) -> float:
        """Get normalized popularity score for a specific destination."""
        all_scores = self._compute_all_popularity_scores()
        return all_scores.get(str(dest_id), 0.5)  # Default neutral
