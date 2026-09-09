from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import event

if TYPE_CHECKING:
    from app.models import User


class ChatConversation(SQLModel, table=True):
    __tablename__ = "chat_conversation"

    id:          UUID     = Field(default_factory=uuid4, primary_key=True)
    user_id:     UUID     = Field(foreign_key="users.id", index=True)
    trip_plan_id: Optional[UUID] = Field(default=None, foreign_key="trip_plans.id")
    title:       str      = "New Conversation"
    created_at:  datetime = Field(default_factory=datetime.utcnow)
    updated_at:  datetime = Field(default_factory=datetime.utcnow)

    messages: List["ChatMessage"] = Relationship(back_populates="conversation")
    user: "User" = Relationship(back_populates="chat_conversations")


# Auto-update the timestamp whenever the conversation is modified
@event.listens_for(ChatConversation, "before_update")
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_message"

    id:               UUID     = Field(default_factory=uuid4, primary_key=True)
    conversation_id:  UUID     = Field(foreign_key="chat_conversation.id", ondelete="CASCADE")
    role:             str
    content:          str
    created_at:       datetime = Field(default_factory=datetime.utcnow)

    conversation: ChatConversation = Relationship(back_populates="messages")