from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4
from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.destination_model import Destination


class PermitCategory(str, Enum):
    nepali  = "Nepali"
    saarc   = "SAARC"
    foreign = "Foreign"


# ---------------------------------------------------------------------------
# Permit
# ---------------------------------------------------------------------------

class Permit(SQLModel, table=True):
    __tablename__ = "permit"

    id:             UUID           = Field(default_factory=uuid4, primary_key=True)
    destination_id: UUID           = Field(foreign_key="destination.id")
    category:       PermitCategory
    price:          Decimal

    # relationships
    destination: "Destination" = Relationship(back_populates="permits")
