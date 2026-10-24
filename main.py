"""CLI «Сводка по городу»: аргументы, вызов сервиса, печать, коды выхода."""

import argparse
import json
import logging
import re
import sys
import uuid
from typing import Any

from clients.errors import (
    ClientRequestError,
    InvalidResponseError,
    NotFoundError,
    ServiceUnavailableError,
)
from processing.service import build_city_summary

EXIT_OK = 0
EXIT_BAD_ARGS = 2  # argparse сам завершает программу с этим кодом
EXIT_NOT_FOUND = 3
EXIT_UNAVAILABLE = 4

logger = logging.getLogger("city_summary")


def currency_code(value: str) -> str:
    code = value.strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", code):
        raise argparse.ArgumentTypeError(
            f"'{value}' не похож на ISO-код валюты (три буквы, например USD)"
        )
    return code


def city_name(value: str) -> str:
    name = value.strip()
    if not name:
        raise argparse.ArgumentTypeError("название города не может быть пустым")
    return name


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Сводка по городу: погода и курс валюты"
    )
    parser.add_argument(
        "--city", required=True, type=city_name, help="город, например Moscow"
    )
    parser.add_argument(
        "--currency",
        default="USD",
        type=currency_code,
        help="ISO-код валюты, курс к рублю (по умолчанию USD)",
    )
    parser.add_argument("--json", action="store_true", help="вывести сводку в JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="подробные логи")
    return parser.parse_args(argv)


def setup_logging(run_id: str, verbose: bool) -> None:
    """Логи идут в stderr с run_id, чтобы stdout оставался чистым."""

    def add_run_id(record: logging.LogRecord) -> bool:
        record.run_id = run_id
        return True

    handler = logging.StreamHandler(sys.stderr)
    handler.addFilter(add_run_id)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s run_id=%(run_id)s %(name)s: %(message)s"
        )
    )
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING, handlers=[handler]
    )


def yes_no(flag: bool) -> str:
    return "да" if flag else "нет"


def format_text(summary: dict[str, Any]) -> str:
    weather = summary["weather"]
    rates = summary["rates"]
    return "\n".join(
        [
            f"Город: {summary['city']}",
            f"Погода: {weather['temp_c']:.1f}°C, {weather['description']}",
            f"Тёплая одежда: {yes_no(weather['warm_clothes'])}",
            f"{rates['currency']}→RUB: {rates['rate_to_rub']:.2f}",
            f"Дорогой курс: {yes_no(rates['expensive'])}",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_id = uuid.uuid4().hex[:8]
    setup_logging(run_id, args.verbose)
    logger.info("start city=%s currency=%s", args.city, args.currency)

    try:
        summary = build_city_summary(args.city, args.currency)
    except NotFoundError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return EXIT_NOT_FOUND
    except (ServiceUnavailableError, InvalidResponseError, ClientRequestError) as exc:
        print(f"Ошибка: внешний сервис недоступен — {exc}", file=sys.stderr)
        return EXIT_UNAVAILABLE

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(format_text(summary))
    logger.info("done")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
