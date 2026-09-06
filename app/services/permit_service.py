from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import Permit


class PermitService:
    def __init__(self, session: Session):
        self.session = session

    def get_all_permits(self, offset: int = 0, limit: int = 100):
        statement = select(Permit).offset(offset).limit(limit)
        items = self.session.exec(statement).all()
        total = self.session.exec(select(func.count(Permit.id))).one()
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    def get_by_destination_id(self, destination_id) -> list[Permit]:
        statement = select(Permit).where(
            Permit.destination_id == UUID(str(destination_id))
        )
        return self.session.exec(statement).all()

    def get_permit_by_id(self, permit_id: UUID) -> Permit:
        permit = self.session.get(Permit, permit_id)
        if not permit:
            raise HTTPException(status_code=404, detail="Permit not found")
        return permit

    def create_permit(self, permit_data: Permit) -> Permit:
        permit = Permit(**permit_data.model_dump())
        self.session.add(permit)
        self.session.commit()
        self.session.refresh(permit)
        return permit

    def update_permit(self, permit_id: UUID, permit_data: Permit) -> Permit:
        existing = self.get_permit_by_id(permit_id)
        patch = permit_data.model_dump(exclude_unset=True)
        existing.sqlmodel_update(patch)
        self.session.commit()
        self.session.refresh(existing)
        return existing

    def delete_permit(self, permit_id: UUID) -> dict:
        permit = self.get_permit_by_id(permit_id)
        self.session.delete(permit)
        self.session.commit()
        return {"message": "Permit deleted successfully"}
