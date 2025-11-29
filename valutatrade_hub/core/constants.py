#!/usr/bin/env python3
"""
Глобальные константы проекта ValutaTrade Hub.

Здесь определены значения по умолчанию для настроек приложения.
Фактические значения загружаются из config.json через SettingsLoader.
"""

from datetime import timedelta

# =============================================================================
# ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ (будут переопределены из config.json)
# =============================================================================

# Базовые директории.
DATA_DIR = "data"  # Можно изменить в config.json.
LOG_DIR = "logs"
CONFIG_FILE = "config.json"

# Файлы данных.
USERS_FILE = "data/users.json"
PORTFOLIOS_FILE = "data/portfolios.json"
RATES_FILE = "data/rates.json"
EXCHANGE_HISTORY_FILE = "data/exchange_rates.json"

# Файлы логов.
LOG_FILE = "logs/actions.log"

# Настройки валют.
BASE_CURRENCY = "USD"
SUPPORTED_FIAT = ("EUR", "GBP", "RUB")
SUPPORTED_CRYPTO = ("BTC", "ETH", "SOL")
CRYPTO_ID_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
}

# Настройки времени и TTL.
RATES_TTL = timedelta(hours=1)
ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Настройки сети и API.
REQUEST_TIMEOUT = 10
USER_AGENT = "ValutaTrade-Hub/1.0"
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
EXCHANGERATE_API_URL = "https://v6.exchangerate-api.com/v6"
EXCHANGERATE_PUBLIC_FALLBACK = "https://open.er-api.com/v6/latest"

# Настройки логирования.
LOG_MAX_BYTES = 500000
LOG_BACKUP_COUNT = 3
DEFAULT_LOG_LEVEL = "INFO"

# Валидация и лимиты.
MIN_PASSWORD_LENGTH = 4
MIN_CURRENCY_CODE_LENGTH = 2
MAX_CURRENCY_CODE_LENGTH = 5
CURRENCY_CODE_PATTERN = r"^[A-Za-z]+$"

# =============================================================================
# КОМАНДЫ CLI
# =============================================================================

AVAILABLE_COMMANDS = {
    "help": "Показать список доступных команд.",
    "exit": "Выйти из программы.",
    "register": "Регистрация нового пользователя.",
    "login": "Авторизация пользователя.",
    "show-portfolio": "Показать текущий портфель пользователя.",
    "buy": "Покупка валюты.",
    "sell": "Продажа валюты.",
    "get-rate": "Показать курс валют.",
    "update-rates": "Обновить курсы валют из внешнего API.",
    "show-rates": "Показать текущие курсы валют.",
    "start-scheduler": "Запустить фоновое обновление курсов (интервал: 60 с).",
    "deposit": "Пополнить базовую валюту для тестирования.",
}

# =============================================================================
# ТЕКСТОВЫЕ СООБЩЕНИЯ ДЛЯ ПОЛЬЗОВАТЕЛЯ
# =============================================================================

# Приветственные сообщения.
WELCOME_MESSAGE = "💰 Добро пожаловать в ValutaTrade Hub!"
HELP_PROMPT = "Введите 'help' для списка команд или 'exit' для выхода.\n"
GOODBYE_MESSAGE = "👋 Завершение работы. До свидания!"

# Сообщения об ошибках.
UNKNOWN_COMMAND = "⚠️ Неизвестная команда: '{}'. Введите 'help' для справки."
COMMAND_HELP_NOT_FOUND = (
    "ℹ️ Справка по команде '{}' не найдена. "
    "Введите 'help' для общего списка."
)
INTERNAL_CLI_ERROR = "❌ Внутренняя ошибка CLI: {}"
USER_INTERRUPT = (
    "\n⛔ Прервано пользователем. "
    "Для выхода используйте 'exit'."
)
CURRENCY_NOT_FOUND_HELP = (
    "💡 Используйте 'show-rates' для просмотра доступных валют."
)
API_ERROR_SUGGESTION = (
    "🔁 Попробуйте повторить позже или проверьте подключение к сети."
)

# Сообщения помощи по командам.
COMMAND_USAGE = "📖 Использование: {}"
COMMAND_HELP_TEXTS = {
    "register": "register --username <name> --password <pass>",
    "login": "login --username <name> --password <pass>",
    "show-portfolio": "show-portfolio [--base <currency>]",
    "buy": "buy --currency <code> --amount <number>",
    "sell": "sell --currency <code> --amount <number>",
    "get-rate": "get-rate --from <code> --to <code>",
    "update-rates": "update-rates [--source coingecko|exchangerate]",
    "show-rates": "show-rates [--currency <code>] [--top <n>] [--base <cur>]",
    "start-scheduler": "start-scheduler",
    "deposit": "deposit --amount <number>",
}

# Примеры использования команд.
COMMAND_EXAMPLES = [
    "register --username alice --password 1234",
    "login --username alice --password 1234",
    "deposit --amount 1000",
    "buy --currency BTC --amount 0.01",
    "sell --currency BTC --amount 0.01",
    "get-rate --from BTC --to USD",
    "update-rates --source coingecko",
    "show-rates --currency BTC --top 3 --base USD",
    "start-scheduler",
]
