"""Tests for the live-weather signal inside the contextual recommender."""
import pytest

from sqlmodel import select

from app.models import User
from app.services.contextual import (
    ContextAwareFiltering,
    WEATHER_NOTES,
    reset_weather_state,
    weather_comfort_factor,
)


def _fake_weather(temp: float, rain_probs: list) -> dict:
    return {
        "source": "Open-Meteo",
        "current": {"condition": "Partly cloudy", "temperature_c": temp},
        "daily": [
            {
                "date": f"2026-09-{d:02d}",
                "condition": "Rain" if p > 40 else "Clear",
                "max_temp_c": temp + 4,
                "min_temp_c": temp - 3,
                "precipitation_probability": p,
                "precipitation_mm": p / 10.0,
            }
            for d, p in enumerate(rain_probs, start=1)
        ],
    }


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_weather_comfort_factor_math():
    assert weather_comfort_factor(_fake_weather(18, [10, 5, 0])) == pytest.approx(1.0)
    rainy = _fake_weather(18, [80, 70, 10])
    assert weather_comfort_factor(rainy) == pytest.approx(0.7, abs=1e-6)
    freezing = _fake_weather(2, [10, 5, 0])
    assert weather_comfort_factor(freezing) < 1.0


# ---------------------------------------------------------------------------
# Offline behaviour
# ---------------------------------------------------------------------------

def test_offline_fallback_is_neutral_and_scoreable(monkeypatch, session, test_destinations):
    def boom(*args, **kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr("app.services.contextual.fetch_weather", boom)
    reset_weather_state()

    ctx = ContextAwareFiltering(session)
    scores = ctx.compute_all_context_scores({"preferred_season": ["Spring"]})

    assert scores, "recommendations must still work offline"
    assert all(0 <= v <= 1 for v in scores.values())
    assert WEATHER_NOTES == {}, "no weather notes when offline"


def test_weather_mode_off_never_calls_network(monkeypatch, session, test_destinations):
    from app.services import contextual

    calls = []

    def fake(lat, lon, days=5, timeout=8.0):
        calls.append(lat)
        return _fake_weather(18, [10, 5, 5])

    monkeypatch.setattr("app.services.contextual.fetch_weather", fake)
    monkeypatch.setattr(contextual.settings, "WEATHER_MODE", "off")
    reset_weather_state()

    ContextAwareFiltering(session).compute_all_context_scores({"preferred_season": ["Spring"]})
    assert calls == []
    assert WEATHER_NOTES == {}


# ---------------------------------------------------------------------------
# Live behaviour (network mocked)
# ---------------------------------------------------------------------------

def test_live_weather_penalizes_rainy_destination(monkeypatch, session, test_destinations):
    trek, temple, _ = test_destinations  # trek in Pokhara, temple in Kathmandu

    def fake(lat, lon, days=5, timeout=8.0):
        # Pokhara coords (~28.2) get fine weather; Kathmandu (~27.7) gets heavy rain
        return _fake_weather(18, [10, 5, 5]) if abs(lat - 28.2) < 0.1 else _fake_weather(18, [80, 85, 75])

    monkeypatch.setattr("app.services.contextual.fetch_weather", fake)
    reset_weather_state()

    ctx = ContextAwareFiltering(session)
    scores = ctx.compute_all_context_scores({"preferred_season": ["Spring"]})

    assert scores[str(trek.id)] > scores[str(temple.id)], "rainy destination should score lower"
    assert WEATHER_NOTES.get(str(temple.id)), "weather note expected for the rainy destination"


def test_recommendation_explanation_includes_live_weather(monkeypatch, session, user_token,
                                                         test_destinations):
    monkeypatch.setattr(
        "app.services.contextual.fetch_weather",
        lambda lat, lon, days=5, timeout=8.0: _fake_weather(18, [10, 5, 5]),
    )
    reset_weather_state()

    from app.services.recommendation_service import RecommendationService

    user = session.exec(select(User).where(User.email == "user@test.com")).first()
    recs = RecommendationService(session).get_recommendations(user.id, limit=3)

    assert recs
    assert any("Live weather" in (r.explanation.reason_summary or "") for r in recs)