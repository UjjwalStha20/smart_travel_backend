import json

from app.chat.trip_context import (
    PLAN_CHANGE_PATTERN,
    TRIP_SYSTEM_PROMPT,
    build_itinerary_context,
    classify_intent,
    parse_plan_change,
    strip_plan_change,
)


def test_prompt_uses_single_braces():
    assert "{{" not in TRIP_SYSTEM_PROMPT
    assert '{"intent": "modify_itinerary"' in TRIP_SYSTEM_PROMPT


def test_parse_plan_change_single_braces():
    change = {"intent": "modify_itinerary", "summary": "Add a viewpoint", "days": []}
    reply = f"Sure!\n<plan_change>{json.dumps(change)}</plan_change>"
    assert parse_plan_change(reply) == change
    assert "<plan_change>" not in strip_plan_change(reply)


def test_parse_plan_change_double_braces_escaped():
    change = {"intent": "modify_itinerary", "summary": "Bob's cafe", "days": []}
    raw = json.dumps(change).replace("{", "{{").replace("}", "}}")
    reply = f"Here is the change.\n<plan_change>{raw}</plan_change>"
    assert parse_plan_change(reply) == change
    assert "<plan_change>" not in strip_plan_change(reply)


def test_parse_plan_change_invalid_json():
    reply = "<plan_change>not-json</plan_change>"
    assert parse_plan_change(reply) is None


def test_parse_plan_change_missing():
    assert parse_plan_change("No change here") is None


def test_classify_intent_modify():
    assert classify_intent("move day 2 to a later time") == "modify_itinerary"
    assert classify_intent("add Bandipur as a destination") == "add_destination"
    assert classify_intent("how is the weather in Pokhara?") == "weather_question"


def test_build_itinerary_context_empty():
    assert "no itinerary" in build_itinerary_context({"itinerary_days": []})