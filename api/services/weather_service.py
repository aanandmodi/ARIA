"""
Weather service — Open-Meteo (no API key needed).
"""

from __future__ import annotations

import httpx

from api.core.config import settings
from api.core.logging import log

# Timezone-to-coordinates mapping for common timezones
_TZ_COORDS: dict[str, tuple[float, float]] = {
    "Asia/Kolkata": (28.6139, 77.2090),      # Delhi
    "America/New_York": (40.7128, -74.0060),
    "America/Los_Angeles": (34.0522, -118.2437),
    "Europe/London": (51.5074, -0.1278),
    "Europe/Berlin": (52.5200, 13.4050),
    "Asia/Tokyo": (35.6762, 139.6503),
    "Australia/Sydney": (-33.8688, 151.2093),
}

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


async def get_forecast(tz: str | None = None) -> dict:
    """
    Get today's weather forecast from Open-Meteo.
    Returns: {temp_max, temp_min, condition, precipitation_chance, wind}
    """
    timezone = tz or settings.timezone
    lat, lon = _TZ_COORDS.get(timezone, (28.6139, 77.2090))

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                OPEN_METEO_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,windspeed_10m_max,weathercode",
                    "timezone": timezone,
                    "forecast_days": 1,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        daily = data.get("daily", {})
        weather_code = (daily.get("weathercode", [0]) or [0])[0]

        return {
            "temp_max": (daily.get("temperature_2m_max", [None]) or [None])[0],
            "temp_min": (daily.get("temperature_2m_min", [None]) or [None])[0],
            "condition": _weather_code_to_text(weather_code),
            "precipitation_chance": (daily.get("precipitation_probability_max", [None]) or [None])[0],
            "wind": (daily.get("windspeed_10m_max", [None]) or [None])[0],
        }
    except Exception as exc:
        log.error("weather_fetch_failed", error=str(exc))
        return {
            "temp_max": None,
            "temp_min": None,
            "condition": "Unknown",
            "precipitation_chance": None,
            "wind": None,
        }


def _weather_code_to_text(code: int) -> str:
    """Convert WMO weather code to human-readable text."""
    mapping = {
        0: "Clear sky ☀️",
        1: "Mainly clear 🌤",
        2: "Partly cloudy ⛅",
        3: "Overcast ☁️",
        45: "Foggy 🌫",
        48: "Rime fog 🌫",
        51: "Light drizzle 🌦",
        53: "Moderate drizzle 🌧",
        55: "Dense drizzle 🌧",
        61: "Slight rain 🌧",
        63: "Moderate rain 🌧",
        65: "Heavy rain ⛈",
        71: "Slight snow ❄️",
        73: "Moderate snow 🌨",
        75: "Heavy snow 🌨",
        77: "Snow grains ❄️",
        80: "Slight rain showers 🌦",
        81: "Moderate rain showers 🌧",
        82: "Violent rain showers ⛈",
        85: "Slight snow showers 🌨",
        86: "Heavy snow showers 🌨",
        95: "Thunderstorm ⛈",
        96: "Thunderstorm with hail ⛈",
        99: "Thunderstorm with heavy hail ⛈",
    }
    return mapping.get(code, f"Code {code}")


def format_forecast(data: dict) -> str:
    """Format forecast dict into a readable string for briefing."""
    if not data or data.get("temp_max") is None:
        return "Weather data unavailable."
    return (
        f"{data['condition']}\n"
        f"🌡 {data['temp_min']}°C — {data['temp_max']}°C\n"
        f"🌧 Precip: {data['precipitation_chance'] or 0}%\n"
        f"💨 Wind: {data['wind'] or 0} km/h"
    )
