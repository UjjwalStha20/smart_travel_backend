"""Per-trip chat: builds a compact trip context, calls the LLM, applies plan changes."""
import json
import re
from typing import Optional, List
from uuid import UUID

from openai import OpenAI
from sqlmodel import Session, select

from app.chat.tool_executor import ToolExecutor
from app.chat.tool_registry import ToolRegistry
from app.chat.trip_context import (
    TRIP_SYSTEM_PROMPT,
    build_history_context,
    build_itinerary_context,
    build_trip_context,
    classify_intent,
    parse_plan_change,
    strip_plan_change,
)
from app.core.config import settings
from app.models import TripConversation, TripMessage, TripPlan
from app.models.trip_plan_model import TripPlanStatus
from app.services.trip_plan_service import build_read, to_day_out
from sqlmodel import text as sa_text

_TOOL_CALL_RE = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)


class TripChatService:
    MAX_HISTORY = 12
    MAX_TOOL_ROUNDS = 4

    def __init__(self, session: Session, trip: TripPlan):
        self.session = session
        self.trip = trip
        self.user_id = trip.user_id
        self.client = OpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY or "ollama",
            timeout=settings.LLM_TIMEOUT_SECONDS,  # never hang the UI
        )
        self.tool_executor = ToolExecutor(ToolRegistry(session))

    def _get_or_create_conversation(self) -> TripConversation:
        conv = self.session.exec(
            select(TripConversation).where(TripConversation.trip_id == self.trip.id)
        ).first()
        if not conv:
            conv = TripConversation(trip_id=self.trip.id)
            self.session.add(conv)
            self.session.flush()
        return conv

    def _history(self, conv: TripConversation) -> list:
        msgs = self.session.exec(
            select(TripMessage)
            .where(TripMessage.conversation_id == conv.id)
            .order_by(TripMessage.created_at.asc())
        ).all()
        history = []
        for m in msgs[-self.MAX_HISTORY * 2:]:
            if m.meta and m.meta.get("tool_result"):
                history.append({"role": "user", "content": f"[Tool Result]\n{json.dumps(m.meta['tool_result'], indent=2, default=str)[:4000]}"})
            else:
                history.append({"role": m.role, "content": m.content})
        return history

    def _save(self, conv: TripConversation, role: str, content: str, intent: Optional[str] = None, metadata: Optional[dict] = None) -> TripMessage:
        msg = TripMessage(
            conversation_id=conv.id,
            role=role,
            content=content,
            intent=intent,
            meta=metadata or {},
        )
        self.session.add(msg)
        return msg

    def _resolve_tool_name(self, name: str) -> str:
        aliases = {"get_destination_details": "get_destination_by_id"}
        return aliases.get(name, name)

    def _parse_tool_calls(self, content: str) -> list:
        calls = []
        for block in _TOOL_CALL_RE.findall(content):
            func_match = re.search(r"<function(?:_name)?[=>]?\s*(\w+)", block)
            if not func_match:
                continue
            name = func_match.group(1)
            params = {}
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

    def process_message(self, message: str) -> dict:
        conv = self._get_or_create_conversation()
        intent = classify_intent(message)

        user_msg = self._save(conv, "user", message, intent=intent)
        self.session.flush()

        trip_read = build_read(self.session, self.trip)
        context = (
            TRIP_SYSTEM_PROMPT
            + "\n\n"
            + build_trip_context(trip_read)
            + "\n\n"
            + build_itinerary_context(trip_read)
            + "\n\n"
            + build_history_context(self._history(conv))
        )

        messages = [{"role": "system", "content": context}]
        for h in self._history(conv) + [{"role": "user", "content": message}]:
            messages.append(h)
        # re-add the current message if it was also included via history slice
        if messages[-1]["content"] != message:
            messages.append({"role": "user", "content": message})

        reply = ""
        proposed_change = None
        try:
            for _ in range(self.MAX_TOOL_ROUNDS):
                response = self.client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=2048,
                    extra_body={"think": False, "keep_alive": "30m"},
                )
                reply = response.choices[0].message.content or ""

                tool_calls = self._parse_tool_calls(reply)
                if not tool_calls:
                    break

                for tc in tool_calls:
                    name = self._resolve_tool_name(tc.get("name", ""))
                    args = tc.get("arguments") or {}
                    result = self.tool_executor.execute(name, args)
                    payload = json.dumps(result, default=str, indent=2)[:4000]
                    messages.append({"role": "user", "content": f"[Tool Result: {name}]\n{payload}"})
                    self._save(conv, "assistant", f"[tool:{name}]", metadata={"tool_result": result})
                self.session.flush()
        except Exception:
            self.session.rollback()
            reply = (
                "I'm having trouble reaching my AI engine right now, so I couldn't update your plan. "
                "Your trip data is safe — try again in a moment."
            )
            proposed_change = None
            msg = self._save(conv, "assistant", reply, intent="unknown")
            self.session.commit()
            return {
                "reply": reply,
                "message_id": str(msg.id),
                "intent": intent,
                "proposed_plan_change": None,
                "conversation_id": str(conv.id),
            }

        proposed_change = parse_plan_change(reply) if reply else None
        clean_reply = strip_plan_change(reply) if reply else ""
        if not clean_reply.strip():
            if proposed_change:
                clean_reply = proposed_change.get("summary") or "Here's a proposed change for your plan — review and apply it below."
            else:
                clean_reply = reply

        metadata = {}
        if proposed_change:
            metadata["proposed_plan_change"] = proposed_change

        assistant = self._save(
            conv,
            "assistant",
            clean_reply,
            intent=proposed_change.get("intent") if proposed_change else intent,
            metadata=metadata,
        )

        # status moves out of draft once conversation happens
        if self.trip.status == TripPlanStatus.draft:
            self.trip.status = TripPlanStatus.planning
        conv.updated_at = self.trip.updated_at
        self.session.commit()

        # Generate context-aware suggested questions
        suggested_questions = self._suggested_questions()

        return {
            "reply": clean_reply,
            "message_id": str(assistant.id),
            "intent": proposed_change.get("intent") if proposed_change else intent,
            "proposed_plan_change": proposed_change,
            "conversation_id": str(conv.id),
            "suggested_questions": suggested_questions,
        }

    def messages(self, limit: int = 100) -> list:
        conv = self._get_or_create_conversation()
        msgs = self.session.exec(
            select(TripMessage)
            .where(TripMessage.conversation_id == conv.id)
            .order_by(TripMessage.created_at.asc())
            .limit(limit)
        ).all()
        return [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "intent": m.intent,
                "metadata": m.meta or {},
                "created_at": m.created_at.isoformat(),
            }
            for m in msgs
        ]

    def _suggested_questions(self) -> List[str]:
        """Generate context-aware suggested questions based on the current trip
        and conversation intent."""
        trip = self.trip
        prefs = trip.preferences or {}
        budget = trip.budget or {}
        dest_names = trip.destinations or []
        styles = prefs.get("pace", "") or ""
        interests = prefs.get("interests") or []
        days = trip.duration_days

        questions: List[str] = []

        # Build questions based on trip characteristics
        if not dest_names:
            # No trip planned yet - generic questions
            questions = [
                "Where would you like to travel?",
                "How many days do you have?",
                "What kind of trip are you after?",
                "What's your budget range?"
            ]
        else:
            # Trip is in progress - generate relevant questions
            cat = trip.trip_types or []
            budget_level = budget.get("level", "") if isinstance(budget, dict) else ""

            # Cultural/religious questions
            if "cultural" in (interests or []) or "cultural_site" in (cat or []):
                questions = [
                    "Show me more cultural places.",
                    "Which sites are best for a one-day trip?",
                    "Can you make a cultural itinerary?",
                ]

            # Religious questions
            if "religious" in (interests or []) or "religious_site" in (cat or []):
                questions = [
                    "Show me more religious sites.",
                    "Which temples can I visit in one day?",
                    "Can you create a religious heritage itinerary?",
                ]

            # Trekking questions
            if "trek" in (cat or []) or "trekking" in (interests or []):
                if days:
                    questions = [
                        f"Show me trekking routes for a {days}-day trip.",
                        "Which trek has the best acclimatization schedule?",
                        "What permits are needed for this trek?",
                    ]
                else:
                    questions = [
                        "Show me trekking routes in Nepal.",
                        "Which trek is best for beginners?",
                        "What permits do I need for trekking?",
                    ]

            # Nature questions
            if "nature" in (interests or []) or any(c in (cat or []) for c in ["nature", "lake", "waterfall", "viewpoint"]):
                questions = [
                    "Show me more nature attractions.",
                    "Which viewpoints are best for sunrise?",
                    "What lakes or waterfalls can I visit?",
                ]

            # Budget questions
            if budget_level and budget_level.lower() == "budget":
                questions = [
                    "Can you make a budget-friendly itinerary?",
                    "What are the free or low-cost attractions?",
                    "How does the budget affect accommodation options?",
                ]

            # Default: if no specific questions matched, use generic
            if not questions:
                questions = [
                    "What else can I add to my trip?",
                    "Can you adjust the pace?",
                    "Suggest some places to visit?",
                    "How can I improve this itinerary?",
                ]

        # Deduplicate while preserving order
        seen = set()
        unique_questions = []
        for q in questions:
            if q not in seen:
                seen.add(q)
                unique_questions.append(q)

        return unique_questions[:4]