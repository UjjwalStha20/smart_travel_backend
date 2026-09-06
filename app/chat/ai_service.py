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

TOOL_NUDGE = (
    "You have tools that return this data from the database or live feeds. "
    "Call the correct tool now using the exact <tool_call> XML format described at the "
    "top of your instructions, then answer using ONLY the returned data."
)

_HEDGE_PATTERNS = (
    "i don't have",
    "i do not have",
    "doesn't have",
    "no current",
    "cannot provide",
    "can't provide",
    "unable to",
    "no real-time",
    "i don't know",
)

_DATA_INTENT = re.compile(
    r"weather|temperature|rain|forecast|price|cost|budget|how much|fare|flight|airport|"
    r"stay|room|lodge|hotel|trek|route|food|meal|dal bhat|momo|permit|"
    r"how do i get|how to get|reach|bus|schedule|attraction|ticket|entry fee",
    re.IGNORECASE,
)


class AIService:
    MAX_HISTORY = 30
    MAX_TOKENS = 2048  # headroom so a thinking preamble cannot swallow the reply

    def __init__(self, session: Session, current_user: User):
        self.session = session
        self.user = current_user
        self.client = OpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY or "ollama",
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
            title = self._generate_title(message)
            conv.title = title or (message[:80] + ("..." if len(message) > 80 else ""))
        conv.updated_at = datetime.utcnow()

    def _generate_title(self, message: str) -> str:
        """Ask the LLM for a short title; fall back to truncation if it fails."""
        for _attempt in range(2):  # retry once when the model only emits reasoning
            try:
                response = self.client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a chat titler. Reply with ONLY a short, descriptive "
                                "title (3-6 words, no quotes, no trailing punctuation)."
                            ),
                        },
                        {"role": "user", "content": f"Title for this request: {message}"},
                    ],
                    temperature=0.3,
                    max_tokens=512,
                    extra_body={"think": False},  # qwen3: reduce thinking-mode preambles
                )
                raw = response.choices[0].message.content or ""
                if not raw:
                    continue  # thinking preamble ate the budget; retry
                title = self._sanitize_title(raw)
                if self._acceptable_title(title):
                    return title
            except Exception:
                continue
        return ""

    @staticmethod
    def _should_force_tool(message: str, reply: str) -> bool:
        """True when the model hedged with 'I don't have...' but the user clearly asked for data."""
        if not reply:
            return False
        hedged = any(h in reply.lower() for h in _HEDGE_PATTERNS)
        return hedged and bool(_DATA_INTENT.search(message))

    @staticmethod
    def _acceptable_title(title: str) -> bool:
        if not title:
            return False
        lowered = title.lower()
        openers = ("hmm", "okay", "sure", "so ", "let me", "i will", "the user", "users")
        return not lowered.startswith(openers)

    @staticmethod
    def _sanitize_title(raw: str) -> str:
        if not raw:
            return ""
        lines = [ln.strip().strip('"').strip() for ln in raw.splitlines() if ln.strip()]
        title = " ".join(lines[-1].split()) if lines else ""
        return title[:60]

    def _resolve_tool_name(self, name: str) -> str:
        return TOOL_NAME_ALIASES.get(name, name)

    def _parse_text_tool_calls(self, content: str) -> list[dict]:
        calls = []
        blocks = re.findall(r"<tool_call>(.*?)</tool_call>", content, re.DOTALL)
        
        for block in blocks:
            func_match = re.search(r"<function(?:_name)?[=>]?\s*(\w+)", block)
            if not func_match:
                continue
            
            name = func_match.group(1)
            params = {}
            
            param_matches = re.findall(
                r"<parameter=(\w+)>\s*(.*?)\s*</parameter>", block, re.DOTALL
            )
            for key, val in param_matches:
                params[key] = val.strip()
                
            json_match = re.search(r"<parameters>\s*(.*?)\s*</parameters>", block, re.DOTALL)
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
        self, 
        message: str, 
        conversation_id: Optional[str] = None,
        user_profile: Optional[dict] = None
    ) -> dict:
        conversation = self._load_or_create_conversation(conversation_id)
        conv_id = str(conversation.id)

        self._save_message(conversation.id, "user", message)
        self._update_conversation_title(conversation.id, message)

        history = self._get_history_messages(conversation.id)

        # Dynamically inject user profile for adaptability
        dynamic_system_prompt = SYSTEM_PROMPT
        if user_profile:
            profile_text = (
                f"\n\nCURRENT USER CONTEXT:\n"
                f"- Traveler Type: {user_profile.get('traveler_type', 'general')}\n"
                f"- Budget: {user_profile.get('budget', 'moderate')}\n"
                f"- Fitness Level: {user_profile.get('fitness_level', 'moderate')}\n"
                f"- Dietary Restrictions: {user_profile.get('dietary_restrictions', 'none')}\n"
                f"Adapt ALL recommendations to match this specific user profile."
            )
            dynamic_system_prompt += profile_text

        messages = [
            {"role": "system", "content": dynamic_system_prompt},
            *history,
        ]

        max_tool_rounds = 5
        reply_content = None
        nudged = False

        for _round in range(max_tool_rounds):
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                temperature=0.2,    # Low temp for strict XML tool calling
                max_tokens=self.MAX_TOKENS,  # leave room for the real answer
                extra_body={"think": False},  # qwen3: keep token budget for the real answer
            )

            choice = response.choices[0]
            reply_content = choice.message.content or ""

            text_calls = self._parse_text_tool_calls(reply_content)
            if text_calls:
                messages.append({"role": "assistant", "content": reply_content})
                self._handle_tool_calls(messages, text_calls, conversation.id)
                continue

            # The model answered without tools but clearly needed data - nudge it once.
            if not nudged and self._should_force_tool(message, reply_content):
                messages.append({"role": "assistant", "content": reply_content or "(no response)"})
                messages.append({"role": "user", "content": TOOL_NUDGE})
                nudged = True
                continue

            break

        if not reply_content:
            reply_content = "I'm sorry, I couldn't process that request."

        self._save_message(conversation.id, "assistant", reply_content)
        self.session.commit()

        return {
            "reply": reply_content,
            "conversation_id": conv_id,
        }