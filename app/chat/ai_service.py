import json
import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from openai import OpenAI
from sqlmodel import Session, select

from app.chat.prompts import SYSTEM_PROMPT
from app.chat.tool_executor import ToolExecutor
from app.chat.tool_registry import ToolRegistry
from app.core.config import settings
from app.models import User
from app.models.chat_model import ChatConversation, ChatMessage


TOOL_NAME_ALIASES = {
    "get_destination_details": "get_destination_by_id",
}


class AIService:
    MAX_HISTORY = 30

    def __init__(self, session: Session, current_user: User):
        self.session = session
        self.user = current_user
        self.client = OpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
        )
        self.tool_executor = ToolExecutor(ToolRegistry(session))

    def _load_or_create_conversation(
        self, conversation_id: Optional[str] = None
    ) -> ChatConversation:
        if conversation_id:
            conv = self.session.exec(
                select(ChatConversation).where(
                    ChatConversation.id == UUID(conversation_id),
                    ChatConversation.user_id == self.user.id,
                )
            ).first()
            if conv:
                return conv
        conv = ChatConversation(user_id=self.user.id)
        self.session.add(conv)
        self.session.commit()
        self.session.refresh(conv)
        return conv

    def _get_history_messages(self, conversation_id: UUID) -> list[dict]:
        messages = self.session.exec(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
        ).all()
        result = []
        for m in messages[-self.MAX_HISTORY :]:
            if m.role == "tool":
                try:
                    data = json.loads(m.content)
                    tool_name = data.get("tool", "unknown")
                    result_content = json.dumps(data.get("result", ""), indent=2)
                except (json.JSONDecodeError, TypeError):
                    tool_name = "unknown"
                    result_content = m.content
                result.append(
                    {
                        "role": "user",
                        "content": f"[Tool Result: {tool_name}]\n{result_content}",
                    }
                )
            else:
                result.append({"role": m.role, "content": m.content})
        return result

    def _save_message(self, conversation_id: UUID, role: str, content: str):
        msg = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        self.session.add(msg)

    def _update_conversation_title(self, conversation_id: UUID, message: str):
        conv = self.session.get(ChatConversation, conversation_id)
        if conv and conv.title == "New Conversation":
            conv.title = message[:80] + ("..." if len(message) > 80 else "")
        conv.updated_at = datetime.utcnow()

    def _resolve_tool_name(self, name: str) -> str:
        return TOOL_NAME_ALIASES.get(name, name)

    def _parse_text_tool_calls(self, content: str) -> list[dict]:
        calls = []
        blocks = re.findall(
            r"<tool_call>(.*?)</tool_call>", content, re.DOTALL
        )
        for block in blocks:
            func_match = re.search(
                r"<function(?:_name)?[=>]?\s*(\w+)", block
            )
            if not func_match:
                continue
            name = func_match.group(1)
            params = {}
            param_matches = re.findall(
                r"<parameter=(\w+)>\s*(.*?)\s*</parameter>",
                block,
                re.DOTALL,
            )
            for key, val in param_matches:
                params[key] = val.strip()
            json_match = re.search(
                r"<parameters>\s*(.*?)\s*</parameters>", block, re.DOTALL
            )
            if json_match:
                try:
                    parsed = json.loads(json_match.group(1))
                    if isinstance(parsed, dict):
                        params.update(parsed)
                except json.JSONDecodeError:
                    pass
            calls.append({"name": name, "arguments": params})
        return calls

    def _handle_tool_calls(
        self, messages: list, tool_calls_data: list, conversation_id: UUID
    ):
        for tc_data in tool_calls_data:
            tool_name = self._resolve_tool_name(tc_data["name"])
            arguments = tc_data["arguments"]
            tool_result = self.tool_executor.execute(tool_name, arguments)

            content = json.dumps(tool_result, indent=2)
            messages.append(
                {
                    "role": "user",
                    "content": f"[Tool Result: {tool_name}]\n{content}",
                }
            )

            self._save_message(
                conversation_id,
                "tool",
                json.dumps({"tool": tool_name, "result": tool_result}),
            )

    def process_message(
        self, message: str, conversation_id: Optional[str] = None
    ) -> dict:
        conversation = self._load_or_create_conversation(conversation_id)
        conv_id = str(conversation.id)

        self._save_message(conversation.id, "user", message)
        self._update_conversation_title(conversation.id, message)

        history = self._get_history_messages(conversation.id)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
        ]

        max_tool_rounds = 5
        reply_content = None

        for _round in range(max_tool_rounds):
            response = self.client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=messages,
            )

            choice = response.choices[0]
            reply_content = choice.message.content or ""

            text_calls = self._parse_text_tool_calls(reply_content)
            if not text_calls:
                break

            messages.append({"role": "assistant", "content": reply_content})
            self._handle_tool_calls(messages, text_calls, conversation.id)

        if not reply_content:
            reply_content = "I'm sorry, I couldn't process that request."

        self._save_message(conversation.id, "assistant", reply_content)
        self.session.commit()

        return {
            "reply": reply_content,
            "conversation_id": conv_id,
        }
