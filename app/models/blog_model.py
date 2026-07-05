from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel, Text

if TYPE_CHECKING:
    from app.models import User


class Blog(SQLModel, table=True):
    __tablename__ = "blog"

    id:              UUID            = Field(default_factory=uuid4, primary_key=True)
    title:           str
    slug:            str            = Field(unique=True)
    content:         str            = Field(sa_type=Text)
    excerpt:         Optional[str]  = None
    author_id:       Optional[UUID] = Field(default=None, foreign_key="users.id")
    featured_image:  Optional[str]  = None
    category:        Optional[str]  = None
    tags:            Optional[list] = Field(default=None, sa_type=JSON)
    is_published:    bool           = False
    published_at:    Optional[datetime] = None
    created_at:      datetime       = Field(default_factory=datetime.utcnow)
    updated_at:      datetime       = Field(default_factory=datetime.utcnow)

    # relationships
    author: Optional["User"] = Relationship(back_populates="blogs")
