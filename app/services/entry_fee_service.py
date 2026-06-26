from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import EntryFee


class EntryFeeService:
    def __init__(self, session: Session):
        self.session = session

    def get_all_entry_fees(self, offset: int = 0, limit: int = 100):
        statement = select(EntryFee).offset(offset).limit(limit)
        return self.session.exec(statement).all()

    def get_entry_fee_by_id(self, fee_id: UUID) -> EntryFee:
        fee = self.session.get(EntryFee, fee_id)
        if not fee:
            raise HTTPException(status_code=404, detail="Entry fee not found")
        return fee

    def create_entry_fee(self, fee_data: EntryFee) -> EntryFee:
        fee = EntryFee(**fee_data.model_dump())
        self.session.add(fee)
        self.session.commit()
        self.session.refresh(fee)
        return fee

    def update_entry_fee(self, fee_id: UUID, fee_data: EntryFee) -> EntryFee:
        existing = self.get_entry_fee_by_id(fee_id)
        patch = fee_data.model_dump(exclude_unset=True)
        existing.sqlmodel_update(patch)
        self.session.commit()
        self.session.refresh(existing)
        return existing

    def delete_entry_fee(self, fee_id: UUID) -> dict:
        fee = self.get_entry_fee_by_id(fee_id)
        self.session.delete(fee)
        self.session.commit()
        return {"message": "Entry fee deleted successfully"}
