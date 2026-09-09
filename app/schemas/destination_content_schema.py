from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DestinationHighlightCreate(BaseModel):
    position: int = 0
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1000)
    distance_hint: Optional[str] = Field(default=None, max_length=200)
    visit_time: Optional[str] = Field(default=None, max_length=200)


class DestinationHighlightRead(DestinationHighlightCreate):
    id: UUID
    destination_id: UUID


class DestinationHighlightUpdate(BaseModel):
    position: Optional[int] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    distance_hint: Optional[str] = Field(default=None, max_length=200)
    visit_time: Optional[str] = Field(default=None, max_length=200)


class DestinationThingToDoCreate(BaseModel):
    position: int = 0
    title: str = Field(min_length=1, max_length=200)
    duration: Optional[str] = Field(default=None, max_length=200)
    difficulty: Optional[str] = Field(default=None, max_length=100)
    cost: Optional[str] = Field(default=None, max_length=200)


class DestinationThingToDoRead(DestinationThingToDoCreate):
    id: UUID
    destination_id: UUID


class DestinationThingToDoUpdate(BaseModel):
    position: Optional[int] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    duration: Optional[str] = Field(default=None, max_length=200)
    difficulty: Optional[str] = Field(default=None, max_length=100)
    cost: Optional[str] = Field(default=None, max_length=200)


class DestinationFaqCreate(BaseModel):
    position: int = 0
    question: str = Field(min_length=1, max_length=300)
    answer: str = Field(min_length=1, max_length=2000)


class DestinationFaqRead(DestinationFaqCreate):
    id: UUID
    destination_id: UUID


class DestinationFaqUpdate(BaseModel):
    position: Optional[int] = None
    question: Optional[str] = Field(default=None, min_length=1, max_length=300)
    answer: Optional[str] = Field(default=None, min_length=1, max_length=2000)


class DestinationContentRead(BaseModel):
    destination_id: UUID
    destination_name: str
    highlights: List[DestinationHighlightRead] = Field(default_factory=list)
    things_to_do: List[DestinationThingToDoRead] = Field(default_factory=list)
    faqs: List[DestinationFaqRead] = Field(default_factory=list)
