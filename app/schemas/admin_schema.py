from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_users: int
    total_destinations: int
    total_reviews: int
    total_itineraries: int
    total_blogs: int
    total_photos: int
    users_this_month: int
    users_last_month: int
    destinations_this_month: int
    reviews_this_month: int


class WeeklyAnalyticsItem(BaseModel):
    label: str
    users: int
    views: int
    reviews: int
    itineraries: int


class RecentReviewItem(BaseModel):
    id: str
    user_name: str
    destination_name: str
    rating: int
    comment: str
    created_at: str


class RecentUserItem(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: str


class ReviewRatingsDistribution(BaseModel):
    ratings: dict[str, int]


class DashboardResponse(BaseModel):
    stats: DashboardStats
    weekly_analytics: list[WeeklyAnalyticsItem]
    recent_reviews: list[RecentReviewItem]
    recent_users: list[RecentUserItem]
    review_ratings: dict[str, int]
