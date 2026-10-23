"""Правила предобработки: зависят от полученных данных, не от клиентов."""

from typing import Any

COLD_THRESHOLD_C = 0.0
EXPENSIVE_RATE_RUB = 100.0
DEFAULT_DESCRIPTION = "no description"


def preprocess_weather(weather: dict[str, Any]) -> dict[str, Any]:
    """Правила 1–2: флаг тёплой одежды и описание по умолчанию."""
    description = (weather.get("description") or "").strip()
    return {
        "temp_c": weather["temp_c"],
        "description": description or DEFAULT_DESCRIPTION,
        "warm_clothes": weather["temp_c"] < COLD_THRESHOLD_C,
    }


def preprocess_rate(currency: str, rate_to_rub: float) -> dict[str, Any]:
    """Правило 3: флаг «дорогой курс», курс округляется до копеек."""
    return {
        "currency": currency.upper(),
        "rate_to_rub": round(rate_to_rub, 2),
        "expensive": rate_to_rub > EXPENSIVE_RATE_RUB,
    }
