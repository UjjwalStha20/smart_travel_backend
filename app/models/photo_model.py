from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models import Destination, User


# ---------------------------------------------------------------------------
# Photos
# ---------------------------------------------------------------------------

class Photo(SQLModel, table=True):
    __tablename__ = "photos"

    id:             UUID          = Field(default_factory=uuid4, primary_key=True)
    destination_id: UUID          = Field(foreign_key="destination.id")
    uploaded_by:    UUID          = Field(foreign_key="users.id")
    image_url:      str
    caption:        Optional[str] = None
    is_featured:    bool          = False

    # relationships
    destination: "Destination" = Relationship(back_populates="photos")
    uploader:    "User"       = Relationship(back_populates="photos")

