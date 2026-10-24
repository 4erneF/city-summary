# City Summary

CLI-утилита «Сводка по городу»: получает погоду и курс выбранной валюты к рублю из внешних API, приводит ответы к единому виду, применяет правила и печатает сводку.

- Погода: [Open-Meteo](https://open-meteo.com/) — сначала геокодинг города, затем текущая погода по координатам. Ключ не нужен.
- Курсы: [Frankfurter](https://frankfurter.dev/) — `GET https://api.frankfurter.dev/v2/rate/{currency}/RUB`. Ключ не нужен.

## Требования

- Python 3.12 (работает на 3.10+)
- зависимости из `requirements.txt` (`requests`)

## Установка

```bash
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Запуск

```bash
python main.py --city Moscow                  # курс USD→RUB
python main.py --city Moscow --currency EUR   # курс EUR→RUB
python main.py --city Moscow --json           # вывод в JSON
python main.py --city Moscow -v               # подробные логи с run_id в stderr
```

Пример вывода:

```text
Город: Moscow
Погода: -3.2°C, clear sky
Тёплая одежда: да
USD→RUB: 92.15
Дорогой курс: нет
```

## Коды выхода

| Код | Когда |
|-----|-------|
| 0 | успех |
| 2 | ошибка аргументов: нет `--city`, `--currency` не из трёх букв |
| 3 | город или код валюты не найден |
| 4 | внешний сервис недоступен после retry или вернул некорректный ответ |

## Структура

```text
main.py                    # CLI: argparse, вывод, коды выхода, logging с run_id
clients/                   # только общение с внешними API
├── errors.py              # исключения приложения
├── http.py                # общий GET: timeout, retry, разбор и проверка JSON
├── weather.py             # get_weather(city) → dict
└── rates.py               # get_rate(currency) → float
processing/
├── preprocessing.py       # правила: warm_clothes, expensive
└── service.py             # build_city_summary(city, currency="USD") → dict
tests/                     # unittest + unittest.mock, без сети
```

## Устойчивость к сбоям

- timeout `(3, 7)` — 3 с на соединение и 7 с на ответ, в сумме не больше 10 с на запрос;
- до 2 повторов после первой попытки при `Timeout`, `ConnectionError`, 500/502/503/504 и 429;
- пауза между попытками — экспоненциальная (1 с, 2 с) со случайным jitter; при 429 берётся числовой `Retry-After` (не больше 30 с);
- остальные 4xx не повторяются: повтор не исправит запрос;
- перед использованием проверяются `Content-Type`, что тело — JSON, и обязательные поля с типами (`temperature_2m`, `weather_code`, `rate`); некорректный ответ даёт код выхода 4.

## Правила предобработки

1. `warm_clothes: true`, если температура ниже 0 °C.
2. `expensive: true`, если курс выше 100 ₽.

## Дополнительно

- логи с `run_id` в stderr (stdout остаётся чистым для сводки);
- флаг `--json`;
- тесты клиентов через `unittest.mock`;
- аннотации типов.

## Тесты и проверка кода

```bash
python -m unittest discover -s tests -t . -v
pip install -r requirements-dev.txt
ruff check . && ruff format --check .
```
