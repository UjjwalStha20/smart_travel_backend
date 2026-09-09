from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models import Destination


class DestinationHighlight(SQLModel, table=True):
    __tablename__ = "destination_highlight"

    id:             UUID               = Field(default_factory=uuid4, primary_key=True)
    destination_id: UUID               = Field(foreign_key="destination.id", index=True)
    position:       int                = Field(default=0)
    title:          str
    description:    str
    distance_hint:  Optional[str]      = None
    visit_time:     Optional[str]      = None

    destination: "Destination" = Relationship(back_populates="highlights")


class DestinationThingToDo(SQLModel, table=True):
    __tablename__ = "destination_thing_to_do"

    id:             UUID               = Field(default_factory=uuid4, primary_key=True)
    destination_id: UUID               = Field(foreign_key="destination.id", index=True)
    position:       int                = Field(default=0)
    title:          str
    duration:       Optional[str]      = None
    difficulty:     Optional[str]      = None
    cost:           Optional[str]      = None

    destination: "Destination" = Relationship(back_populates="things_to_do")


class DestinationFaq(SQLModel, table=True):
    __tablename__ = "destination_faq"

    id:             UUID               = Field(default_factory=uuid4, primary_key=True)
    destination_id: UUID               = Field(foreign_key="destination.id", index=True)
    position:       int                = Field(default=0)
    question:       str
    answer:         str

    destination: "Destination" = Relationship(back_populates="faqs")
