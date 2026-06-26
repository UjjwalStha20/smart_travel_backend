from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models import Destination, User



# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------

class Review(SQLModel, table=True):
    __tablename__ = "review"

    id:             UUID          = Field(default_factory=uuid4, primary_key=True)
    user_id:        UUID          = Field(foreign_key="users.id")
    destination_id: UUID          = Field(foreign_key="destination.id")
    rating:         int
    comment:        Optional[str] = None
    created_at:     datetime      = Field(default_factory=datetime.utcnow)

    # relationships
    user:        "User"        = Relationship(back_populates="reviews")
    destination: "Destination" = Relationship(back_populates="reviews")
