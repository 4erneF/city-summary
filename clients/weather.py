"""Клиент погоды Open-Meteo: геокодинг города, затем текущая погода."""

from typing import Any

from clients.errors import CityNotFoundError, InvalidResponseError
from clients.http import get_json

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
SERVICE = "open-meteo"

# Коды погоды WMO, которые возвращает Open-Meteo.
WEATHER_CODES: dict[int, str] = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snow fall",
    73: "moderate snow fall",
    75: "heavy snow fall",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}


def _require_number(data: dict[str, Any], key: str) -> float:
    value = data.get(key)
    # bool — подкласс int, его отсекаем отдельно.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidResponseError(f"{SERVICE}: поле '{key}' отсутствует или не число")
    return float(value)


def _geocode(city: str) -> dict[str, Any]:
    data = get_json(
        GEOCODING_URL,
        {"name": city, "count": 1, "language": "en", "format": "json"},
        service=SERVICE,
    )
    if not isinstance(data, dict):
        raise InvalidResponseError(f"{SERVICE}: геокодинг вернул не объект")
    results = data.get("results")
    if not results:
        raise CityNotFoundError(f"Город '{city}' не найден")
    if not isinstance(results, list) or not isinstance(results[0], dict):
        raise InvalidResponseError(f"{SERVICE}: неожиданный формат results")
    place = results[0]
    name = place.get("name")
    return {
        "name": name if isinstance(name, str) and name else city,
        "latitude": _require_number(place, "latitude"),
        "longitude": _require_number(place, "longitude"),
    }


def get_weather(city: str) -> dict[str, Any]:
    """Возвращает {"city": str, "temp_c": float, "description": str}."""
    place = _geocode(city)
    data = get_json(
        FORECAST_URL,
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,weather_code",
        },
        service=SERVICE,
    )
    current = data.get("current") if isinstance(data, dict) else None
    if not isinstance(current, dict):
        raise InvalidResponseError(f"{SERVICE}: в ответе нет блока 'current'")

    temp_c = _require_number(current, "temperature_2m")
    code = current.get("weather_code")
    # bool — подкласс int, его отсекаем отдельно.
    if isinstance(code, bool) or not isinstance(code, int):
        raise InvalidResponseError(
            f"{SERVICE}: поле 'weather_code' отсутствует или не целое число"
        )
    if code not in WEATHER_CODES:
        raise InvalidResponseError(f"{SERVICE}: неизвестный weather_code {code}")
    return {
        "city": place["name"],
        "temp_c": temp_c,
        "description": WEATHER_CODES[code],
    }
