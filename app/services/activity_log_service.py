from typing import Optional
from uuid import UUID

from sqlmodel import Session, func, select

from app.models.activity_log_model import ActivityLog


class ActivityLogService:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self, offset: int = 0, limit: int = 100, type_filter: Optional[str] = None):
        query = select(ActivityLog).order_by(ActivityLog.created_at.desc())
        if type_filter:
            query = query.where(ActivityLog.type == type_filter)
        items = self.session.exec(query.offset(offset).limit(limit)).all()
        total = self.session.exec(select(func.count(ActivityLog.id))).one()
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    def log(self, user_id: Optional[UUID], user_name: str, action: str, target: str, type: str) -> ActivityLog:
        entry = ActivityLog(
            user_id=user_id,
            user_name=user_name,
            action=action,
            target=target,
            type=type,
        )
        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry
