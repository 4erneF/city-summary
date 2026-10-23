"""Исключения приложения, в которые переводятся ошибки внешних сервисов."""


class CitySummaryError(Exception):
    """Базовая ошибка приложения."""


class NotFoundError(CitySummaryError):
    """Запрошенный ресурс не найден во внешнем сервисе."""


class CityNotFoundError(NotFoundError):
    """Геокодинг не нашёл город."""


class CurrencyNotFoundError(NotFoundError):
    """Сервис курсов не знает такой код валюты."""


class ServiceUnavailableError(CitySummaryError):
    """Внешний сервис не ответил даже после всех повторов."""


class InvalidResponseError(CitySummaryError):
    """Сервис ответил, но ответ не соответствует ожидаемому формату."""


class ClientRequestError(CitySummaryError):
    """Сервис вернул 4xx: проблема в запросе, повтор не поможет."""

    def __init__(self, status_code: int, url: str) -> None:
        super().__init__(f"HTTP {status_code} от {url}")
        self.status_code = status_code
        self.url = url
