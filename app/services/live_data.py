"""Live data integration using Open-Meteo (free, no API key required)."""
import httpx


WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class LiveDataError(Exception):
    """Raised when an upstream live-data provider cannot be reached."""


def wmo_description(code) -> str:
    return WMO_CODES.get(code, "Unknown")


def fetch_weather(latitude: float, longitude: float, days: int = 5, timeout: float = 8.0) -> dict:
    """Fetch current conditions + daily forecast for coordinates (Nepal)."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "precipitation,wind_speed_10m,weather_code"
        ),
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max,precipitation_sum,wind_speed_10m_max"
        ),
        "timezone": "auto",
        "forecast_days": days,
    }
    try:
        response = httpx.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:  # network errors, timeouts, bad responses
        raise LiveDataError(f"Failed to fetch live weather: {exc}") from exc

    current = data.get("current") or {}
    daily = data.get("daily") or {}
    dates = daily.get("time") or []
    daily_list = []
    for i, date in enumerate(dates):
        daily_list.append(
            {
                "date": date,
                "condition": wmo_description(_safe(daily, "weather_code", i)),
                "max_temp_c": _safe(daily, "temperature_2m_max", i),
                "min_temp_c": _safe(daily, "temperature_2m_min", i),
                "precipitation_probability": _safe(daily, "precipitation_probability_max", i),
                "precipitation_mm": _safe(daily, "precipitation_sum", i),
                "wind_speed_kmh": _safe(daily, "wind_speed_10m_max", i),
            }
        )

    return {
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "timezone": data.get("timezone"),
        "source": "Open-Meteo",
        "current": {
            "time": current.get("time"),
            "condition": wmo_description(current.get("weather_code")),
            "temperature_c": current.get("temperature_2m"),
            "apparent_temperature_c": current.get("apparent_temperature"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
        },
        "daily": daily_list,
    }


def _safe(container: dict, key: str, index: int):
    values = container.get(key) or []
    return values[index] if index < len(values) else None