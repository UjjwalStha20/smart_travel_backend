from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    # Added to enable AI adaptability (budget, fitness, dietary needs, etc.)
    user_profile: Optional[dict] = None 


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


class ConversationListItem(BaseModel):
    id: UUID
    title: str
    message_count: int
    updated_at: datetime

    class Config:
        # Ensures UUIDs and datetimes are serialized correctly to JSON
        json_encoders: ClassVar[dict] = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }
        # If using Pydantic V2, use this instead of class Config:
        # model_config = {"json_schema_extra": {"example": {"id": "123e4567-e89b-12d3-a456-426614174000"}}}