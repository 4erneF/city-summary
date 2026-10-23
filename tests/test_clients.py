"""Тесты клиентов: внешние API подменяются через unittest.mock."""

import unittest
from unittest import mock

import requests

from clients import http
from clients.errors import (
    CityNotFoundError,
    ClientRequestError,
    CurrencyNotFoundError,
    InvalidResponseError,
    ServiceUnavailableError,
)
from clients.rates import get_rate
from clients.weather import get_weather


def fake_response(
    status: int = 200,
    payload: object | None = None,
    headers: dict[str, str] | None = None,
) -> mock.Mock:
    response = mock.Mock(spec=requests.Response)
    response.status_code = status
    response.headers = {"Content-Type": "application/json", **(headers or {})}
    response.json.return_value = payload
    return response


@mock.patch("clients.http.time.sleep")
@mock.patch("clients.http.requests.get")
class GetJsonRetryTest(unittest.TestCase):
    def test_success_without_retry(self, get: mock.Mock, sleep: mock.Mock) -> None:
        get.return_value = fake_response(payload={"ok": True})
        self.assertEqual(http.get_json("https://x", service="t"), {"ok": True})
        self.assertEqual(get.call_count, 1)
        sleep.assert_not_called()

    def test_timeout_is_passed(self, get: mock.Mock, sleep: mock.Mock) -> None:
        get.return_value = fake_response(payload={})
        http.get_json("https://x", service="t")
        connect, read = get.call_args.kwargs["timeout"]
        self.assertLessEqual(connect + read, 10)

    def test_retries_5xx_then_succeeds(self, get: mock.Mock, sleep: mock.Mock) -> None:
        get.side_effect = [
            fake_response(503),
            fake_response(502),
            fake_response(payload=[1]),
        ]
        self.assertEqual(http.get_json("https://x", service="t"), [1])
        self.assertEqual(get.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_gives_up_after_two_retries(self, get: mock.Mock, sleep: mock.Mock) -> None:
        get.side_effect = requests.exceptions.ConnectionError()
        with self.assertRaises(ServiceUnavailableError):
            http.get_json("https://x", service="t")
        self.assertEqual(get.call_count, 1 + http.MAX_RETRIES)

    def test_timeout_is_retried(self, get: mock.Mock, sleep: mock.Mock) -> None:
        get.side_effect = [requests.exceptions.Timeout(), fake_response(payload={})]
        self.assertEqual(http.get_json("https://x", service="t"), {})
        self.assertEqual(get.call_count, 2)

    def test_429_waits_retry_after(self, get: mock.Mock, sleep: mock.Mock) -> None:
        get.side_effect = [
            fake_response(429, headers={"Retry-After": "7"}),
            fake_response(payload={}),
        ]
        http.get_json("https://x", service="t")
        sleep.assert_called_once_with(7.0)

    def test_4xx_is_not_retried(self, get: mock.Mock, sleep: mock.Mock) -> None:
        get.return_value = fake_response(404)
        with self.assertRaises(ClientRequestError):
            http.get_json("https://x", service="t")
        self.assertEqual(get.call_count, 1)
        sleep.assert_not_called()

    def test_html_instead_of_json(self, get: mock.Mock, sleep: mock.Mock) -> None:
        response = fake_response()
        response.headers = {"Content-Type": "text/html"}
        get.return_value = response
        with self.assertRaises(InvalidResponseError):
            http.get_json("https://x", service="t")


@mock.patch("clients.http.requests.get")
class WeatherClientTest(unittest.TestCase):
    def test_parses_weather(self, get: mock.Mock) -> None:
        get.side_effect = [
            fake_response(
                payload={
                    "results": [
                        {"name": "Moscow", "latitude": 55.75, "longitude": 37.62}
                    ]
                }
            ),
            fake_response(
                payload={"current": {"temperature_2m": -3.2, "weather_code": 0}}
            ),
        ]
        self.assertEqual(
            get_weather("moscow"),
            {"city": "Moscow", "temp_c": -3.2, "description": "clear sky"},
        )

    def test_city_not_found(self, get: mock.Mock) -> None:
        get.return_value = fake_response(payload={"generationtime_ms": 0.1})
        with self.assertRaises(CityNotFoundError):
            get_weather("Qwertyzzz")

    def test_missing_temperature(self, get: mock.Mock) -> None:
        get.side_effect = [
            fake_response(
                payload={
                    "results": [
                        {"name": "Moscow", "latitude": 55.75, "longitude": 37.62}
                    ]
                }
            ),
            fake_response(payload={"current": {"weather_code": 0}}),
        ]
        with self.assertRaises(InvalidResponseError):
            get_weather("Moscow")


@mock.patch("clients.http.requests.get")
class RatesClientTest(unittest.TestCase):
    def test_parses_rate(self, get: mock.Mock) -> None:
        get.return_value = fake_response(
            payload={"base": "USD", "quote": "RUB", "rate": 81.83}
        )
        self.assertEqual(get_rate("usd"), 81.83)
        self.assertIn("/USD/RUB", get.call_args.args[0])

    def test_unknown_currency(self, get: mock.Mock) -> None:
        get.return_value = fake_response(422, payload={"message": "invalid currency"})
        with self.assertRaises(CurrencyNotFoundError):
            get_rate("XYZ")

    def test_rub_needs_no_request(self, get: mock.Mock) -> None:
        self.assertEqual(get_rate("RUB"), 1.0)
        get.assert_not_called()

    def test_rate_must_be_number(self, get: mock.Mock) -> None:
        get.return_value = fake_response(payload={"rate": "81.83"})
        with self.assertRaises(InvalidResponseError):
            get_rate("USD")


if __name__ == "__main__":
    unittest.main()
