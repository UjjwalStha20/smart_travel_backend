"""Tests for auto-generated chat conversation titles."""
import types
from uuid import UUID

import pytest

from app.chat.ai_service import AIService


def _service_with(create):
    svc = object.__new__(AIService)
    svc.client = types.SimpleNamespace(
        chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create))
    )
    return svc


def _fake_completion(content: str):
    return types.SimpleNamespace(
        choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=content))]
    )


def test_title_generated_from_first_message():
    received = {}

    def create_with_capture(**kwargs):
        received["prompt"] = kwargs["messages"][-1]["content"]
        return _fake_completion('"Budget Trek ABC"')

    svc = _service_with(create_with_capture)
    title = svc._generate_title("How much for a 3-person ABC trek?")
    assert title == "Budget Trek ABC"
    assert "3-person ABC trek" in received["prompt"]


def test_title_strips_reasoning_prefix_and_quotes():
    svc = _service_with(
        lambda **kwargs: _fake_completion("<thinking>about it</thinking>\n\"Best Everest Route\"")
    )
    assert svc._generate_title("EBC itinerary") == "Best Everest Route"


def test_title_capped_at_60_chars():
    long = "This is an extremely long generated title that keeps going well beyond the sixty character limit"
    svc = _service_with(lambda **kwargs: _fake_completion(long))
    assert len(svc._generate_title("anything")) <= 60


def test_title_falls_back_on_llm_failure():
    def boom(**kwargs):
        raise RuntimeError("ollama offline")

    svc = _service_with(boom)
    assert svc._generate_title("hello") == ""
    assert svc._generate_title("x" * 100) == ""


def test_sanitize_handles_empty_and_quoted_input():
    assert AIService._sanitize_title("") == ""
    assert AIService._sanitize_title("\n\n  \"\"  \n") == ""


def test_preamble_titles_rejected_and_retried():
    calls = {"n": 0}

    def create(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return _fake_completion("<thinking>thinking</thinking>\n\nHmm, the user wants a title")
        return _fake_completion('"Pokhara Trek Plan"')

    svc = _service_with(create)
    assert svc._generate_title("Plan my Pokhara trek") == "Pokhara Trek Plan"
    assert calls["n"] == 2

    assert AIService._acceptable_title("Budget Trek") is True
    assert AIService._acceptable_title("Hmm, the user wants") is False
    assert AIService._acceptable_title("") is False


def test_process_message_assigns_generated_title(session, client, monkeypatch):
    """End-to-end through AIService with a mocked LLM."""
    from sqlmodel import select

    from app.chat.ai_service import AIService as _AS
    from app.chat.tool_executor import ToolExecutor
    from app.chat.tool_registry import ToolRegistry
    from app.core.security import hash_password
    from app.models import User
    from app.models.chat_model import ChatConversation

    user = User(
        name="Chat User", email="chat@test.com", password=hash_password("pass123"),
        role="traveler", nationality="Nepal", phone="+977-9800000099",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    calls = {"n": 0}

    class FakeClient:
        def __init__(self):
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))

        def _create(self, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                return _fake_completion('"Pokhara Trek Plan"')
            return _fake_completion("Here is your trek plan!")

    def init_override(self, s, u):
        self.session = s
        self.user = u
        self.client = FakeClient()
        self.tool_executor = None

    monkeypatch.setattr(_AS, "__init__", init_override)

    svc = _AS(session, user)
    svc.tool_executor = ToolExecutor(ToolRegistry(session))

    result = svc.process_message(message="Plan my Pokhara trek", conversation_id=None)
    assert result["reply"] == "Here is your trek plan!"

    conv = session.exec(
        select(ChatConversation).where(ChatConversation.id == UUID(result["conversation_id"]))
    ).first()
    assert conv is not None
    assert conv.title == "Pokhara Trek Plan"
    assert conv.title != "Plan my Pokhara trek"