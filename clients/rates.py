"""Клиент курсов валют Frankfurter: курс выбранной валюты к рублю."""

from clients.errors import (
    ClientRequestError,
    CurrencyNotFoundError,
    InvalidResponseError,
)
from clients.http import get_json

RATE_URL = "https://api.frankfurter.dev/v2/rate/{currency}/RUB"
SERVICE = "frankfurter"
# Статусы, которыми Frankfurter сообщает о неизвестной валюте.
UNKNOWN_CURRENCY_STATUSES = frozenset({400, 404, 422})


def get_rate(currency: str) -> float:
    """Сколько рублей стоит 1 единица валюты (ISO-код, например USD)."""
    currency = currency.upper()
    if currency == "RUB":
        return 1.0
    try:
        data = get_json(RATE_URL.format(currency=currency), service=SERVICE)
    except ClientRequestError as exc:
        if exc.status_code in UNKNOWN_CURRENCY_STATUSES:
            raise CurrencyNotFoundError(f"Код валюты '{currency}' не найден") from exc
        raise

    rate = data.get("rate") if isinstance(data, dict) else None
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or rate <= 0:
        raise InvalidResponseError(
            f"{SERVICE}: поле 'rate' отсутствует или некорректно"
        )
    return float(rate)
