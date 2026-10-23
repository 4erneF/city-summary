"""Тесты CLI: коды выхода без обращения к сети."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import main
from clients.errors import (
    CityNotFoundError,
    CurrencyNotFoundError,
    ServiceUnavailableError,
)

SUMMARY = {
    "city": "Moscow",
    "weather": {"temp_c": -3.2, "description": "clear sky", "warm_clothes": True},
    "rates": {"currency": "USD", "rate_to_rub": 92.15, "expensive": False},
}


def run(argv: list[str]) -> tuple[int, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main.main(argv)
        except SystemExit as exc:  # argparse
            code = int(exc.code)
    return code, out.getvalue()


@mock.patch("main.build_city_summary")
class MainExitCodesTest(unittest.TestCase):
    def test_success_text(self, build: mock.Mock) -> None:
        build.return_value = SUMMARY
        code, out = run(["--city", "Moscow"])
        self.assertEqual(code, 0)
        self.assertIn("USD→RUB: 92.15", out)
        self.assertIn("Тёплая одежда: да", out)
        build.assert_called_once_with("Moscow", "USD")

    def test_currency_is_uppercased(self, build: mock.Mock) -> None:
        build.return_value = SUMMARY
        run(["--city", "Moscow", "--currency", "eur"])
        build.assert_called_once_with("Moscow", "EUR")

    def test_bad_args(self, build: mock.Mock) -> None:
        self.assertEqual(run([])[0], 2)
        self.assertEqual(run(["--city", "Moscow", "--currency", "US1"])[0], 2)

    def test_not_found(self, build: mock.Mock) -> None:
        for error in (CityNotFoundError("x"), CurrencyNotFoundError("x")):
            build.side_effect = error
            self.assertEqual(run(["--city", "Nowhere"])[0], 3)

    def test_unavailable(self, build: mock.Mock) -> None:
        build.side_effect = ServiceUnavailableError("down")
        self.assertEqual(run(["--city", "Moscow"])[0], 4)


if __name__ == "__main__":
    unittest.main()
