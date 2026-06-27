from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BlogBase(BaseModel):
    title: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    content: str = Field(min_length=1)
    excerpt: Optional[str] = None
    author_id: Optional[UUID] = None
    featured_image: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    is_published: bool = False
    published_at: Optional[datetime] = None


class BlogCreate(BlogBase):
    pass


class BlogRead(BlogBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class BlogUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    slug: Optional[str] = Field(default=None, min_length=1)
    content: Optional[str] = Field(default=None, min_length=1)
    excerpt: Optional[str] = None
    author_id: Optional[UUID] = None
    featured_image: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    is_published: Optional[bool] = None
    published_at: Optional[datetime] = None
