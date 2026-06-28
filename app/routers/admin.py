from fastapi import APIRouter, Depends

from app.dependencies import SessionDep, require_admin
from app.schemas.admin_schema import DashboardResponse
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(session: SessionDep):
    svc = AdminService(session)
    return DashboardResponse(
        stats=svc.get_dashboard_stats(),
        weekly_analytics=svc.get_weekly_analytics(),
        recent_reviews=svc.get_recent_reviews(),
        recent_users=svc.get_recent_users(),
        review_ratings=svc.get_review_ratings_distribution(),
    )
