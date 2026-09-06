"""Tests for forcing tool use when the LLM hedges on a data question."""
import types
from uuid import UUID

import pytest

from app.chat.ai_service import AIService
from app.chat.ai_service import TOOL_NUDGE


def _fake_completion(content: str):
    return types.SimpleNamespace(
        choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=content))]
    )


def test_should_force_tool_detects_hedge_on_data_question():
    assert AIService._should_force_tool(
        "what is the weather in pokhara?", "I don't have current weather data for Pokhara."
    ) is True
    assert AIService._should_force_tool("how much is dal bhat?", "I cannot provide that right now.") is True
    assert AIService._should_force_tool("How should I pace myself at altitude?", "I don't have that information.") is False
    assert AIService._should_force_tool("hello", "Namaste! How can I help?") is False
    assert AIService._should_force_tool("weather in pokhara?", "The best time to visit is spring.") is False


def test_process_message_nudges_hedging_model_then_answers(session, monkeypatch):
    from sqlmodel import select

    from app.chat.ai_service import AIService as _AS
    from app.chat.tool_executor import ToolExecutor
    from app.chat.tool_registry import ToolRegistry
    from app.core.security import hash_password
    from app.models import User
    from app.models.chat_model import ChatMessage

    user = User(
        name="Nudge User", email="nudge@test.com", password=hash_password("pass123"),
        role="traveler", nationality="Nepal", phone="+977-9800000088",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    calls = {"n": 0}

    class FakeClient:
        def __init__(self):
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(create=self._create)
            )

        def _create(self, **kwargs):
            calls["n"] += 1
            msgs = kwargs["messages"]
            if "chat titler" in msgs[0]["content"]:
                return _fake_completion('"Dal Bhat Price"')
            last = msgs[-1]["content"]
            if last.startswith("[Tool Result:"):
                return _fake_completion("Here is the data for your answer.")
            if last == TOOL_NUDGE:
                return _fake_completion(
                    "<tool_call><function_name>search_food_costs</function_name>"
                    "<parameters>{\"name\": \"dal bhat\"}</parameters></tool_call>"
                )
            return _fake_completion("I don't have current data on that right now.")

    def init_override(self, s, u):
        self.session = s
        self.user = u
        self.client = FakeClient()
        self.tool_executor = None

    monkeypatch.setattr(_AS, "__init__", init_override)

    svc = _AS(session, user)
    svc.tool_executor = ToolExecutor(ToolRegistry(session))

    result = svc.process_message(message="how much is dal bhat these days?", conversation_id=None)
    assert result["reply"] == "Here is the data for your answer."
    assert calls["n"] >= 4  # title + hedge + nudge + tool round + final answer

    saved = session.exec(select(ChatMessage)).all()
    assert any(m.role == "tool" for m in saved)


def test_process_message_does_not_nudge_when_answer_is_helpful(session, monkeypatch):
    from app.chat.ai_service import AIService as _AS

    from app.core.security import hash_password
    from app.models import User

    user = User(
        name="User2", email="nudge2@test.com", password=hash_password("pass123"),
        role="traveler", nationality="Nepal", phone="+977-9800000077",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    calls = {"n": 0}

    class FakeClient:
        def __init__(self):
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(create=self._create)
            )

        def _create(self, **kwargs):
            calls["n"] += 1
            if "chat titler" in kwargs["messages"][0]["content"]:
                return _fake_completion('"A Trek"')
            return _fake_completion("Start slow, drink lots of water, and go with a trusted guide.")

    def init_override(self, s, u):
        self.session = s
        self.user = u
        self.client = FakeClient()
        self.tool_executor = None

    monkeypatch.setattr(_AS, "__init__", init_override)

    svc = _AS(session, user)
    result = svc.process_message(message="What safety advice do you have?", conversation_id=None)
    assert result["reply"] == "Start slow, drink lots of water, and go with a trusted guide."
    assert calls["n"] == 2  # title + one main call, no nudge