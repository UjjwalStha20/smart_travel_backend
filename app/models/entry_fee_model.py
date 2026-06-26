from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models import Attraction


class EntryCategory(str, Enum):
    nepali  = "Nepali"
    saarc   = "SAARC"
    foreign = "Foreign"


# ---------------------------------------------------------------------------
# EntryFee
# ---------------------------------------------------------------------------

class EntryFee(SQLModel, table=True):
    __tablename__ = "entry_fee"

    id:             UUID           = Field(default_factory=uuid4, primary_key=True)
    attraction_id: UUID           = Field(foreign_key="attraction.id")
    category:       EntryCategory
    price:          Decimal

    __table_args__ = (UniqueConstraint("attraction_id", "category"),)

    # relationships
    attraction: "Attraction" = Relationship(back_populates="entry_fees")
