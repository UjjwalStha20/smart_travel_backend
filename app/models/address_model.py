from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from app.models import Attraction , RoutePoint , Destination


# ---------------------------------------------------------------------------
# Address
# ---------------------------------------------------------------------------



class Address(SQLModel , table=True):
    __tablename__ = "address"

    id:          UUID                   = Field(default_factory=uuid4, primary_key=True)
    province:       str                 = None
    district:      str                  = None  
    place:         str | None              = None
    latitude:    float                  = None
    longitude:   float                  = None
    altitude:    float                  = None

    # relationships
    route_points: List["RoutePoint"] = Relationship(back_populates="address")
    destinations: List["Destination"] = Relationship(back_populates="address")
    
