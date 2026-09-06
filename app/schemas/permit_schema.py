from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.permit_model import PermitCategory


class PermitBase(BaseModel):
    destination_id: UUID
    # ✅ ADDED: Crucial for the AI to tell the user exactly which permits are needed
    permit_type: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="Type of permit (e.g., TIMS, ACAP, Sagarmatha_National_Park, MCAP)"
    )
    category: PermitCategory
    price: Decimal = Field(ge=Decimal("0"))


class PermitCreate(PermitBase):
    pass


class PermitRead(PermitBase):
    id: UUID


class PermitUpdate(BaseModel):
    destination_id: Optional[UUID] = None
    # ✅ ADDED: Optional for partial updates
    permit_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category: Optional[PermitCategory] = None
    price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))