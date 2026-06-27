from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session, func, select

from app.chat.ai_service import AIService
from app.chat.schemas import ChatRequest, ChatResponse
from app.dependencies import CurrentUser, SessionDep
from app.models.chat_model import ChatConversation, ChatMessage

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", status_code=200)
def chat(
    request: ChatRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> ChatResponse:
    result = AIService(session, current_user).process_message(
        message=request.message,
        conversation_id=request.conversation_id,
    )
    return ChatResponse(**result)


@router.get("/conversations", status_code=200)
def list_conversations(
    session: SessionDep,
    current_user: CurrentUser,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> dict:
    conversations = session.exec(
        select(ChatConversation)
        .where(ChatConversation.user_id == current_user.id)
        .order_by(ChatConversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    total = session.exec(
        select(func.count(ChatConversation.id)).where(
            ChatConversation.user_id == current_user.id
        )
    ).one()

    conv_ids = [c.id for c in conversations]
    if conv_ids:
        msg_counts = session.exec(
            select(ChatMessage.conversation_id, func.count(ChatMessage.id))
            .where(ChatMessage.conversation_id.in_(conv_ids))
            .group_by(ChatMessage.conversation_id)
        ).all()
        count_map = dict(msg_counts)
    else:
        count_map = {}

    items = []
    for conv in conversations:
        items.append(
            {
                "id": str(conv.id),
                "title": conv.title,
                "message_count": count_map.get(conv.id, 0),
                "updated_at": conv.updated_at.isoformat(),
            }
        )
    return {"items": items, "total": total, "offset": offset, "limit": limit}


@router.get("/conversations/{conversation_id}", status_code=200)
def get_conversation(
    conversation_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    conv = session.exec(
        select(ChatConversation).where(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == current_user.id,
        )
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = session.exec(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conv.id)
        .order_by(ChatMessage.created_at.asc())
    ).all()

    return {
        "id": str(conv.id),
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
            if m.role in ("user", "assistant")
        ],
    }


@router.delete("/conversations/{conversation_id}", status_code=200)
def delete_conversation(
    conversation_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    conv = session.exec(
        select(ChatConversation).where(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == current_user.id,
        )
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = session.exec(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conv.id)
    ).all()
    for msg in messages:
        session.delete(msg)
    session.delete(conv)
    session.commit()
    return {"message": "Conversation deleted successfully"}
