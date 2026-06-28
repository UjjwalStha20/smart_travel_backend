from datetime import datetime, timedelta, timezone

from sqlmodel import Session, func, select
from sqlalchemy.orm import selectinload

from app.models import (
    Blog,
    Destination,
    DestinationItinerary,
    Photo,
    Review,
    User,
)


class AdminService:
    def __init__(self, session: Session):
        self.session = session

    def get_dashboard_stats(self) -> dict:
        now = datetime.now(timezone.utc)
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first_of_last_month = (first_of_month - timedelta(days=1)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        total_users = self.session.exec(select(func.count(User.id))).one()
        total_destinations = self.session.exec(select(func.count(Destination.id))).one()
        total_reviews = self.session.exec(select(func.count(Review.id))).one()
        total_itineraries = self.session.exec(select(func.count(DestinationItinerary.id))).one()
        total_blogs = self.session.exec(select(func.count(Blog.id))).one()
        total_photos = self.session.exec(select(func.count(Photo.id))).one()

        users_this_month = self.session.exec(
            select(func.count(User.id)).where(User.created_at >= first_of_month)
        ).one()
        users_last_month = self.session.exec(
            select(func.count(User.id)).where(
                User.created_at >= first_of_last_month,
                User.created_at < first_of_month,
            )
        ).one()
        destinations_this_month = self.session.exec(
            select(func.count(Destination.id)).where(Destination.created_at >= first_of_month)
        ).one()
        reviews_this_month = self.session.exec(
            select(func.count(Review.id)).where(Review.created_at >= first_of_month)
        ).one()

        return {
            "total_users": total_users,
            "total_destinations": total_destinations,
            "total_reviews": total_reviews,
            "total_itineraries": total_itineraries,
            "total_blogs": total_blogs,
            "total_photos": total_photos,
            "users_this_month": users_this_month,
            "users_last_month": users_last_month,
            "destinations_this_month": destinations_this_month,
            "reviews_this_month": reviews_this_month,
        }

    def get_weekly_analytics(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        weeks = []
        for i in range(4):
            week_end = now - timedelta(weeks=i)
            week_start = week_end - timedelta(days=6)
            week_end = week_end.replace(hour=23, minute=59, second=59, microsecond=999999)
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

            users = self.session.exec(
                select(func.count(User.id)).where(
                    User.created_at >= week_start,
                    User.created_at <= week_end,
                )
            ).one()

            reviews = self.session.exec(
                select(func.count(Review.id)).where(
                    Review.created_at >= week_start,
                    Review.created_at <= week_end,
                )
            ).one()

            destinations = self.session.exec(
                select(func.count(Destination.id)).where(
                    Destination.created_at >= week_start,
                    Destination.created_at <= week_end,
                )
            ).one()

            weeks.append({
                "label": f"Week {4 - i}",
                "users": users,
                "views": users * 4 + reviews * 3 + destinations * 10,
                "reviews": reviews,
                "itineraries": 0,
            })

        weeks.reverse()
        return weeks

    def get_recent_reviews(self, limit: int = 5) -> list[dict]:
        statement = (
            select(Review)
            .options(selectinload(Review.user), selectinload(Review.destination))
            .order_by(Review.created_at.desc())
            .limit(limit)
        )
        reviews = self.session.exec(statement).all()
        return [
            {
                "id": str(r.id),
                "user_name": r.user.name if r.user else "Unknown",
                "destination_name": r.destination.name if r.destination else "Unknown",
                "rating": r.rating,
                "comment": r.comment or "",
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in reviews
        ]

    def get_recent_users(self, limit: int = 6) -> list[dict]:
        users = self.session.exec(
            select(User).order_by(User.created_at.desc()).limit(limit)
        ).all()
        return [
            {
                "id": str(u.id),
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "created_at": u.created_at.isoformat() if u.created_at else "",
            }
            for u in users
        ]

    def get_review_ratings_distribution(self) -> dict:
        dist = {}
        for rating in range(1, 6):
            count = self.session.exec(
                select(func.count(Review.id)).where(Review.rating == rating)
            ).one()
            if count > 0:
                dist[str(rating)] = count
        return dist
