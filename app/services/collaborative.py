from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlmodel import select, func

from app.models import User, Destination, UserInteraction, Review


class CollaborativeFiltering:
    """Collaborative filtering based on user-interaction data."""

    def __init__(self, session):
        self.session = session

    def compute_all_collab_scores(
        self, user_profile: Dict[str, Any], all_destinations: List[Any]
    ) -> Dict[str, float]:
        """
        Compute collaborative filtering scores for all destinations.

        Returns dict mapping destination_id -> collaborative_score [0, 1]
        """
        user_id = user_profile.get("user_id")

        # If no user ID or no interaction data, return neutral scores
        if not user_id:
            return {str(dest.id): 0.5 for dest in all_destinations}

        # Get user's interaction history
        user_interactions = self._get_user_interactions(user_id)
        if not user_interactions:
            # New user with no history - return neutral scores
            return {str(dest.id): 0.5 for dest in all_destinations}

        # Build interaction profile for the user
        user_profile_build = self._build_interaction_profile(user_interactions)

        # Get all destination IDs as strings
        dest_ids = [str(dest.id) for dest in all_destinations]

        # Compute similarity-based scores
        scores: Dict[str, float] = {}

        # Find users with similar interaction patterns
        similar_users = self._find_similar_users(user_id, user_interactions)

        if not similar_users:
            # No similar users found, fall back to global popularity
            return self._global_population_fallback(user_id, dest_ids)

        # For each destination, compute weighted score from similar users
        for dest_id in dest_ids:
            score = self._compute_dest_collab_score(dest_id, similar_users, user_interactions)
            # Normalize to [0, 1]
            scores[dest_id] = max(0.0, min(1.0, score))

        # If no destinations scored, give neutral
        if not scores:
            scores = {dest_id: 0.5 for dest_id in dest_ids}

        return scores

    def _get_user_interactions(self, user_id: UUID) -> List[Any]:
        """Get all interactions for a user."""
        statement = select(UserInteraction).where(UserInteraction.user_id == user_id)
        return self.session.exec(statement).all()

    def _build_interaction_profile(
        self, interactions: List[Any]
    ) -> Dict[str, Any]:
        """Build an interaction profile from a user's interaction history."""
        profile: Dict[str, Any] = {
            "interacted_destinations": [],
            "rated_destinations": [],  # (dest_id, rating)
            "saved_destinations": [],
            "interaction_weights": {},  # dest_id -> total weighted score
        }

        weight_map = {"view": 1, "click": 2, "save": 3, "rating": 4, "itinerary": 5, "booking": 6}

        for interaction in interactions:
            dest_id = str(interaction.destination_id)
            itype = interaction.interaction_type
            rating = interaction.rating

            # Track by type
            if itype == "save":
                profile["saved_destinations"].append(dest_id)
            elif itype == "rating" and rating:
                profile["rated_destinations"].append(
                    {"destination_id": dest_id, "rating": rating}
                )

            # Accumulate weighted score
            w = weight_map.get(itype, 1)
            profile["interaction_weights"][dest_id] = (
                profile["interaction_weights"].get(dest_id, 0) + w
            )
            profile["interacted_destinations"].append(dest_id)

        # Deduplicate interacted destinations
        profile["interacted_destinations"] = list(
            set(profile["interacted_destinations"])
        )

        return profile

    def _find_similar_users(
        self, user_id: UUID, user_interactions: List[Any]
    ) -> List[Dict[str, Any]]:
        """Find users with similar interaction patterns."""
        # Get all users who interacted with the same destinations
        interacted_destinations = set()
        for interaction in user_interactions:
            interacted_destinations.add(str(interaction.destination_id))

        if not interacted_destinations:
            return []

        # Find other users who interacted with similar destinations
        stmt = select(UserInteraction.user_id, UserInteraction.destination_id).where(
            UserInteraction.destination_id.in_(list(interacted_destinations))
        )
        all_similar = self.session.exec(stmt).all()

        # Group by user
        user_interaction_counts: Dict[UUID, Dict[str, int]] = {}
        for interaction in all_similar:
            u_id = interaction.user_id
            if u_id == user_id:
                continue  # Skip the target user
            if u_id not in user_interaction_counts:
                user_interaction_counts[u_id] = {}
            dest_id = str(interaction.destination_id)
            user_interaction_counts[u_id][dest_id] = (
                user_interaction_counts[u_id].get(dest_id, 0) + 1
            )

        # Compute similarity scores
        user_similarity: Dict[UUID, float] = {}
        target_interacted = set(
            str(i.destination_id) for i in user_interactions
        )

        for u_id, dest_counts in user_interaction_counts.items():
            # Jaccard similarity: intersection / union
            other_interacted = set(dest_counts.keys())
            intersection = len(target_interacted & other_interacted)
            union = len(target_interacted | other_interacted)

            if union == 0:
                continue

            jaccard = intersection / union if union > 0 else 0

            # Also factor in interaction weight similarity
            # Simple: use Jaccard as the similarity score
            user_similarity[u_id] = jaccard

        # Filter to users with meaningful similarity (above threshold)
        # and who have sufficient interaction data
        min_similarity = 0.15  # Minimum Jaccard similarity
        min_interactions = 3  # Minimum interactions with common destinations

        similar_users = []
        for u_id, similarity in user_similarity.items():
            # Count how many of this user's interactions are with our target destinations
            u_stmt = select(UserInteraction.destination_id).where(
                UserInteraction.user_id == u_id
            )
            u_interacted = set(self.session.exec(u_stmt).all())
            common = len(u_interacted & target_interacted)

            if similarity >= min_similarity and common >= min_interactions:
                similar_users.append(
                    {
                        "user_id": u_id,
                        "similarity": similarity,
                        "common_destinations": common,
                    }
                )

        # Sort by similarity (most similar first)
        similar_users.sort(key=lambda x: x["similarity"], reverse=True)

        # Return top N similar users
        return similar_users[:10]

    def _compute_dest_collab_score(
        self,
        dest_id: str,
        similar_users: List[Dict[str, Any]],
        user_interactions: List[Any],
    ) -> float:
        """Compute collaborative score for a specific destination."""
        # Collect ratings/preferences from similar users for this destination
        similar_ratings: List[float] = []
        similar_weights: List[float] = []

        for sim_user in similar_users:
            u_id = sim_user["user_id"]
            similarity = sim_user["similarity"]

            # Get this similar user's interactions with this destination
            u_stmt = select(UserInteraction).where(
                UserInteraction.user_id == u_id,
                UserInteraction.destination_id == int(dest_id) if dest_id.isdigit() else dest_id,
            )
            similar_interactions = self.session.exec(u_stmt).all()

            for sim_interaction in similar_interactions:
                itype = sim_interaction.interaction_type
                rating = sim_interaction.rating

                # Weight by interaction type and similarity
                weight_map = {"view": 1, "click": 2, "save": 3, "rating": 4, "itinerary": 5, "booking": 6}
                itype_weight = weight_map.get(itype, 1)

                # Combined weight: similarity * interaction type weight
                combined_weight = similarity * itype_weight
                similar_weights.append(combined_weight)

                # Use rating if available, otherwise derive from interaction type
                if rating and 1 <= rating <= 5:
                    similar_ratings.append(rating / 5.0)  # Normalize to [0, 1]
                elif itype == "save":
                    # Save indicates positive preference
                    similar_ratings.append(0.8)
                elif itype == "rating" and rating is None:
                    # Rating given but value missing - treat as neutral positive
                    similar_ratings.append(0.5)
                else:
                    # Other interactions - mild positive
                    similar_ratings.append(0.5)

        if not similar_ratings:
            # No similar users interacted with this destination
            return 0.5  # Neutral

        # Weighted average of similar users' ratings
        weighted_sum = sum(w * r for w, r in zip(similar_weights, similar_ratings))
        total_weight = sum(similar_weights)

        if total_weight > 0:
            score = weighted_sum / total_weight
        else:
            score = 0.5

        # Also factor in the target user's own interaction with this destination
        # if they have one
        own_rating = self._get_own_rating(user_interactions, dest_id)
        if own_rating is not None:
            # Blend: 70% collaborative, 30% own history
            score = 0.7 * score + 0.3 * (own_rating / 5.0)

        return min(max(score, 0.0), 1.0)  # Clamp to [0, 1]

    def _get_own_rating(
        self, user_interactions: List[Any], dest_id: str
    ) -> Optional[float]:
        """Get the target user's rating for a destination, if any."""
        for interaction in user_interactions:
            if str(interaction.destination_id) == dest_id and interaction.interaction_type == "rating":
                if interaction.rating and 1 <= interaction.rating <= 5:
                    return float(interaction.rating) / 5.0
        return None

    def _global_population_fallback(
        self, user_id: UUID, dest_ids: List[str]
    ) -> Dict[str, float]:
        """Fallback when no similar users found - use global popularity."""
        # Get global average ratings and interaction frequencies
        stmt = select(UserInteraction.interaction_type, func.count(UserInteraction.id)).group_by(
            UserInteraction.interaction_type
        )
        interaction_counts = self.session.exec(stmt).all()

        weight_map = {"view": 1, "click": 2, "save": 3, "rating": 4, "itinerary": 5, "booking": 6}
        global_weights: Dict[str, float] = {}

        for itype, count in interaction_counts:
            global_weights[itype] = float(count) / sum(
                c for _, c in interaction_counts
            ) if interaction_counts else 0

        # Return neutral scores for all destinations
        # (In a real implementation, would compute global popularity)
        return {dest_id: 0.5 for dest_id in dest_ids}


class CollabScoreOutput:
    """Output model for collaborative scores."""
    pass
