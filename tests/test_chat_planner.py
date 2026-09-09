"""Tests for progressive requirement gathering in the chat planner."""

from app.chat.planner import (
    collect_facts,
    extract_days,
    follow_up_question,
    is_in_gather_flow,
    is_planning_request,
)
from app.chat.intent import ITINERARY, RECOMMENDATION, TREKKING


def test_extract_days():
    assert extract_days("I have 5 days in Nepal") == 5
    assert extract_days("two weeks") == 14
    assert extract_days("a week") == 7
    assert extract_days("plan a 10-day trip") == 10
    assert extract_days("1d") == 1
    assert extract_days("how many days for ABC?") is None


def test_planning_request_on_thin_input():
    # "I have 5 days in Nepal" must gate for trip style, not produce an itinerary.
    facts = collect_facts([], "I have 5 days in Nepal")
    assert is_planning_request(ITINERARY, "I have 5 days in Nepal", facts) is True
    assert follow_up_question(facts) == (
        "What kind of trip are you after — trekking, hiking, nature, "
        "sightseeing, culture, or a mix?"
    )


def test_no_reasking_in_gather_flow():
    history = [
        {"role": "user", "content": "I have 5 days in Nepal"},
        {"role": "assistant", "content": "What kind of trip are you after — trekking, hiking, nature, sightseeing, culture, or a mix?"},
    ]
    facts = collect_facts(history, "trekking")
    assert is_in_gather_flow(history) is True
    assert facts["days"] == 5
    assert facts["styles"] == ["trekking"]
    assert follow_up_question(facts) is not None  # asks season, not style again


def test_enough_info_stops_asking():
    history = [
        {"role": "user", "content": "I have 5 days for a trek in October"},
    ]
    facts = collect_facts(history, "")
    assert follow_up_question(facts) is None


def test_direct_questions_not_gated():
    # Asking how many days a trek needs is a direct question, not a plan request.
    msg = "how many days do I need for ABC trek?"
    facts = collect_facts([], msg)
    assert is_planning_request(TREKKING, msg, facts) is False
    assert facts["days"] is None  # the number is not stated, it is being asked


def test_vague_recommendation_gated():
    facts = collect_facts([], "recommend something in Nepal")
    assert is_planning_request(RECOMMENDATION, "recommend something in Nepal", facts) is True
    assert follow_up_question(facts) is not None