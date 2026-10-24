"""Правила предобработки: зависят от полученных данных, не от клиентов."""

from typing import Any

COLD_THRESHOLD_C = 0.0
EXPENSIVE_RATE_RUB = 100.0


def preprocess_weather(weather: dict[str, Any]) -> dict[str, Any]:
    """Правило 1: флаг тёплой одежды при температуре ниже порога."""
    return {
        "temp_c": weather["temp_c"],
        "description": weather["description"],
        "warm_clothes": weather["temp_c"] < COLD_THRESHOLD_C,
    }


def preprocess_rate(currency: str, rate_to_rub: float) -> dict[str, Any]:
    """Правило 2: флаг «дорогой курс», курс округляется до копеек."""
    return {
        "currency": currency.upper(),
        "rate_to_rub": round(rate_to_rub, 2),
        "expensive": rate_to_rub > EXPENSIVE_RATE_RUB,
    }
