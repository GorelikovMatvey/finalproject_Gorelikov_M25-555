# ValutaTrade Hub

Проект **ValutaTrade Hub** — это учебное приложение для управления валютным портфелем и работы с обменными курсами.  
Оно объединяет **CLI-интерфейс**, **Core-логику** и **Parser Service**, который периодически получает курсы валют из внешних API.

---

## 1. Идея проекта

ValutaTrade Hub моделирует базовую инфраструктуру торгового терминала для крипто- и фиатных валют.

Функциональность разделена на независимые слои:
- **CLI (Command Line Interface)** — интерфейс команд пользователя.
- **Core Service** — бизнес-логика (регистрация, логин, операции с портфелем, получение курсов).
- **Parser Service** — обновление данных о курсах с внешних API (CoinGecko, ExchangeRate API).
- **Infra Layer** — инфраструктура и конфигурации.
- **Data Layer** — JSON-файлы с пользователями, портфелями и кэшированными курсами.

---

## 2. Структура каталогов

```
finalproject_Gorelikov_M25-555/
│
├── data/
│   ├── users.json
│   ├── portfolios.json
│   ├── rates.json
│   └── exchange_rates.json
│
├── valutatrade_hub/
│   ├── core/
│   │   ├── constants.py
│   │   ├── usecases.py
│   │   ├── utils.py
│   │   ├── models.py
│   │   ├── exceptions.py
│   │   └── ...
│   ├── parser_service/
│   │   ├── api_clients.py
│   │   ├── config.py
│   │   ├── updater.py
│   │   ├── scheduler.py
│   │   └── storage.py
│   ├── cli/
│   │   └── interface.py
│   ├── infra/
│   │   ├── settings.py
│   │   └── database.py
│   ├── decorators.py
│   └── logging_config.py
│
├── main.py
├── Makefile
├── config.json
├── .env
├── pyproject.toml
├── poetry.lock
├── README.md
└── .gitignore
```

---

## 3. Установка и запуск

### Установка зависимостей

Используется Poetry (в соответствии с ТЗ):
```
make install
```
или вручную:
```
poetry install
```

### Запуск приложения

Запуск основной CLI-программы:
```
make project
```
или напрямую через Poetry:
```
poetry run project
```

При запуске появится командная строка:
```
💰 Добро пожаловать в ValutaTrade Hub!
Введите 'help' для списка команд или 'exit' для выхода.
```

---

## 4. Примеры команд CLI

| Команда | Назначение |
|----------|------------|
| `register --username user --password 1234` | Регистрация нового пользователя |
| `login --username user --password 1234` | Авторизация |
| `show-portfolio` | Показать портфель текущего пользователя |
| `buy --currency BTC --amount 0.5` | Купить валюту |
| `sell --currency ETH --amount 1.0` | Продать валюту |
| `get-rate --from USD --to EUR` | Получить курс валюты |
| `update-rates` | Обновить локальные курсы через Parser Service |
| `show-rates` | Просмотр всех кэшированных курсов |
| `start-scheduler` | Запустить фоновое обновление курсов |
| `deposit --amount 1000` | Пополнить базовую валюту для тестирования |
| `help` | Показать справку |
| `exit` | Завершить работу программы |

---

## 5. Конфигурация приложения

При первом запуске автоматически создается файл `config.json` с настройками по умолчанию:

```
{
    "data_dir": "data",
    "base_currency": "USD",
    "rates_ttl": 3600,
    "request_timeout": 10,
    "min_password_length": 4,
    "log_max_bytes": 500000,
    "log_backup_count": 3,
    "default_log_level": "INFO"
}
```

### Настраиваемые параметры:

- **`data_dir`** (строка): Директория для хранения файлов данных
- **`base_currency`** (строка): Базовая валюта для отображения портфеля (USD, EUR, RUB)
- **`rates_ttl`** (число): Время жизни кэша курсов в секундах
- **`request_timeout`** (число): Таймаут HTTP-запросов к API в секундах
- **`min_password_length`** (число): Минимальная длина пароля пользователя
- **`log_max_bytes`** (число): Максимальный размер лог-файла в байтах
- **`log_backup_count`** (число): Количество резервных копий лог-файлов
- **`default_log_level`** (строка): Уровень логирования (DEBUG, INFO, WARNING, ERROR)

### Пример настройки для работы с евро:

```
{
    "data_dir": "my_data",
    "base_currency": "EUR",
    "rates_ttl": 1800,
    "min_password_length": 6
}
```

После изменения конфигурации перезапустите приложение для применения новых настроек.

---

## 6. Кэш, TTL и Parser Service

- Все курсы валют сохраняются в файле `data/rates.json`.
- Исторические данные обновлений сохраняются в `data/exchange_rates.json`.
- Время жизни кэша (`TTL`) настраивается в `config.json` (параметр `rates_ttl`).
- Parser Service автоматически обновляет курсы, получая данные из:
  - **CoinGecko** — для криптовалют;
  - **ExchangeRate API** — для фиатных валют.

Parser Service может работать в двух режимах:
- **Ручное обновление**: команда `update-rates`
- **Фоновое обновление**: команда `start-scheduler` (интервал: 60 секунд)

Для запуска фонового обновления выполните:

---

## 7. Использование API-ключа (EXCHANGERATE_API_KEY)

Parser Service поддерживает приватный доступ к **ExchangeRate API**.  
Ключ хранится в переменной окружения `EXCHANGERATE_API_KEY`.

### Что это такое
**Переменные окружения** — это безопасный способ хранить секреты и настройки,  
которые не должны быть закодированы напрямую в исходниках.

### Как задать переменную

Создайте файл `.env` в корне проекта и добавьте в него строку:
```
EXCHANGERATE_API_KEY=ваш_ключ_от_exchangerate_api
```

После этого при запуске через Poetry ключ будет автоматически считан функцией:
```
os.getenv("EXCHANGERATE_API_KEY", "")
```

Если ключ не указан, используется публичная версия API с ограничением по скорости запросов.

---

## 8. Логи и формат времени

- Все логи сохраняются в каталоге `logs/` (файл `actions.log`).
- Формат времени — **ISO 8601 (UTC)**, пример:
  ```
  INFO 2025-10-28T10:47:49Z Обновление курсов успешно выполнено.
  ```

---

## 9. Демозапись

[![asciicast](https://asciinema.org/a/IrlPacC1vXo9apYWQ1KIYQ0tZ.svg)](https://asciinema.org/a/IrlPacC1vXo9apYWQ1KIYQ0tZ)
---

## 10. Контакты

Автор: **Матвей Гореликов (M25-555)**  
Проект выполнен в рамках учебного задания по Python.
