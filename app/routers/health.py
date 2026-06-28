from datetime import datetime, timezone

from fastapi import APIRouter
from sqlmodel import select, func

from app.dependencies import SessionDep
from app.models import User

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(session: SessionDep):
    db_healthy = False
    try:
        session.exec(select(func.count(User.id))).one()
        db_healthy = True
    except Exception:
        db_healthy = False

    return {
        "status": "ok",
        "database": "healthy" if db_healthy else "error",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
