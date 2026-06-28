from fastapi import APIRouter, Query

from app.dependencies import SessionDep
from app.models.activity_log_model import ActivityLog
from app.schemas.pagination import PaginatedResponse
from app.services.activity_log_service import ActivityLogService

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])


@router.get("/", response_model=PaginatedResponse[ActivityLog], status_code=200)
async def get_all(
    session: SessionDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    type: str = Query(None),
):
    return ActivityLogService(session).get_all(offset=offset, limit=limit, type_filter=type)
