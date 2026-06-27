from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


class ConversationListItem(BaseModel):
    id: UUID
    title: str
    message_count: int
    updated_at: datetime
