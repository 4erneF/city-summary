"""Общий GET-запрос с timeout, retry и разбором JSON."""

import logging
import random
import time
from typing import Any

import requests

from clients.errors import (
    ClientRequestError,
    InvalidResponseError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)

# (connect, read): в сумме не больше 10 секунд на один запрос.
TIMEOUT: tuple[float, float] = (3, 7)
# Повторов после первой попытки (итого до 3 попыток).
MAX_RETRIES = 2
RETRY_STATUSES = frozenset({500, 502, 503, 504})
TOO_MANY_REQUESTS = 429
# Не ждём по Retry-After дольше этого, чтобы CLI не зависал.
MAX_RETRY_AFTER = 30.0
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "CitySummary/1.0 (study project)",
}


def _backoff_delay(attempt: int) -> float:
    """Экспоненциальная пауза 1s, 2s, 4s... плюс случайный jitter."""
    return 2 ** (attempt - 1) + random.uniform(0, 0.5)


def _retry_after_delay(response: requests.Response) -> float | None:
    """Числовое значение заголовка Retry-After в секундах, если оно есть."""
    value = response.headers.get("Retry-After", "")
    try:
        seconds = float(value)
    except ValueError:
        return None
    if seconds < 0:
        return None
    return min(seconds, MAX_RETRY_AFTER)


def get_json(
    url: str,
    params: dict[str, Any] | None = None,
    *,
    service: str,
) -> Any:
    """Выполняет GET и возвращает разобранный JSON.

    Повторяет запрос при Timeout, ConnectionError, 500/502/503/504 и 429.
    Остальные 4xx не повторяет и сразу выбрасывает ClientRequestError.
    """
    attempts = MAX_RETRIES + 1
    for attempt in range(1, attempts + 1):
        reason: str
        delay: float | None = None
        try:
            response = requests.get(
                url, params=params, headers=HEADERS, timeout=TIMEOUT
            )
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as exc:
            reason = type(exc).__name__
        else:
            status = response.status_code
            if status == TOO_MANY_REQUESTS:
                reason = "HTTP 429"
                delay = _retry_after_delay(response)
            elif status in RETRY_STATUSES:
                reason = f"HTTP {status}"
            elif status >= 500:
                # Например 501: повтор не поможет, но это всё равно сбой сервиса.
                raise ServiceUnavailableError(f"{service}: HTTP {status}")
            elif status >= 400:
                raise ClientRequestError(status, url)
            else:
                return _parse_json(response, service)

        if attempt == attempts:
            break
        if delay is None:
            delay = _backoff_delay(attempt)
        logger.warning(
            "%s: retry %s/%s url=%s reason=%s pause=%.1fs",
            service,
            attempt,
            MAX_RETRIES,
            url,
            reason,
            delay,
        )
        time.sleep(delay)

    raise ServiceUnavailableError(
        f"{service}: сервис недоступен после {attempts} попыток ({reason})"
    )


def _parse_json(response: requests.Response, service: str) -> Any:
    content_type = response.headers.get("Content-Type", "")
    if "json" not in content_type:
        raise InvalidResponseError(
            f"{service}: ожидали JSON, пришёл Content-Type '{content_type}'"
        )
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as exc:
        raise InvalidResponseError(f"{service}: тело ответа не JSON") from exc
