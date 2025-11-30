#!/usr/bin/env python3
"""Singleton для загрузки и управления настройками приложения."""

import json
import threading
from datetime import timedelta
from pathlib import Path

from ..core.constants import (
    BASE_CURRENCY,
    COINGECKO_URL,
    CONFIG_FILE,
    DATA_DIR,
    DEFAULT_LOG_LEVEL,
    EXCHANGERATE_API_URL,
    EXCHANGERATE_PUBLIC_FALLBACK,
    LOG_BACKUP_COUNT,
    LOG_DIR,
    LOG_MAX_BYTES,
    MIN_PASSWORD_LENGTH,
    RATES_TTL,
    REQUEST_TIMEOUT,
    USER_AGENT,
)


class SettingsLoader:
    """Singleton для управления настройками приложения."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, path: str = CONFIG_FILE):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._path = Path(path)
                cls._instance._data = {}
                cls._instance._load_defaults()
                cls._instance._load_from_file()
        return cls._instance

    def _load_defaults(self):
        """Загружает значения по умолчанию из констант."""
        self._data = {
            # Пути и файлы.
            "data_dir": DATA_DIR,
            "users_file": "users.json",
            "portfolios_file": "portfolios.json",
            "rates_file": "rates.json",
            "exchange_history_file": "exchange_rates.json",
            "log_dir": LOG_DIR,
            "log_file": "actions.log",

            # Валюты.
            "base_currency": BASE_CURRENCY,

            # Время и TTL.
            "rates_ttl": int(RATES_TTL.total_seconds()),

            # Сеть и API.
            "request_timeout": REQUEST_TIMEOUT,
            "user_agent": USER_AGENT,
            "coingecko_url": COINGECKO_URL,
            "exchangerate_api_url": EXCHANGERATE_API_URL,
            "exchangerate_public_fallback": EXCHANGERATE_PUBLIC_FALLBACK,

            # Логирование.
            "log_max_bytes": LOG_MAX_BYTES,
            "log_backup_count": LOG_BACKUP_COUNT,
            "default_log_level": DEFAULT_LOG_LEVEL,

            # Валидация.
            "min_password_length": MIN_PASSWORD_LENGTH,
        }

    def _load_from_file(self):
        """Загружает настройки из файла конфигурации."""
        try:
            if self._path.exists():
                with open(self._path, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                    # Обновляем настройки из файла.
                    self._data.update(file_data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Ошибка загрузки конфигурации {self._path}: {e}")
            print("⚠️ Используются значения по умолчанию")

    def get(self, key: str, default=None):
        """Получает значение настройки по ключу."""
        return self._data.get(key, default)

    def get_ttl(self) -> timedelta:
        """Возвращает TTL для курсов валют."""
        seconds = self._data.get("rates_ttl", int(RATES_TTL.total_seconds()))
        return timedelta(seconds=seconds)

    def get_data_dir(self) -> str:
        """Возвращает путь к директории с данными."""
        return self._data.get("data_dir", DATA_DIR)

    def get_rates_file(self) -> str:
        """Возвращает путь к файлу с курсами."""
        data_dir = self.get_data_dir()
        rates_file = self._data.get("rates_file", "rates.json")
        return str(Path(data_dir) / rates_file)

    def get_users_file(self) -> str:
        """Возвращает путь к файлу с пользователями."""
        data_dir = self.get_data_dir()
        users_file = self._data.get("users_file", "users.json")
        return str(Path(data_dir) / users_file)

    def get_portfolios_file(self) -> str:
        """Возвращает путь к файлу с портфелями."""
        data_dir = self.get_data_dir()
        portfolios_file = self._data.get("portfolios_file", "portfolios.json")
        return str(Path(data_dir) / portfolios_file)

    def get_exchange_history_file(self) -> str:
        """Возвращает путь к файлу истории обменов."""
        data_dir = self.get_data_dir()
        history_file = self._data.get(
            "exchange_history_file", "exchange_rates.json"
        )
        return str(Path(data_dir) / history_file)

    def get_log_file(self) -> str:
        """Возвращает путь к основному файлу логов."""
        log_dir = self._data.get("log_dir", LOG_DIR)
        log_file = self._data.get("log_file", "actions.log")
        return str(Path(log_dir) / log_file)

    def get_base_currency(self) -> str:
        """Возвращает базовую валюту."""
        return self._data.get("base_currency", BASE_CURRENCY)

    def get_request_timeout(self) -> int:
        """Возвращает таймаут запросов."""
        return self._data.get("request_timeout", REQUEST_TIMEOUT)

    def get_user_agent(self) -> str:
        """Возвращает User-Agent для HTTP-запросов."""
        return self._data.get("user_agent", USER_AGENT)

    def get_api_urls(self) -> dict:
        """Возвращает словарь с URL API."""
        return {
            "coingecko": self._data.get("coingecko_url", COINGECKO_URL),
            "exchangerate_api": self._data.get(
                "exchangerate_api_url", EXCHANGERATE_API_URL
            ),
            "exchangerate_public": self._data.get(
                "exchangerate_public_fallback",
                EXCHANGERATE_PUBLIC_FALLBACK
            ),
        }

    def get_log_settings(self) -> dict:
        """Возвращает настройки логирования."""
        return {
            "log_dir": self._data.get("log_dir", LOG_DIR),
            "log_file": self.get_log_file(),
            "log_max_bytes": self._data.get("log_max_bytes", LOG_MAX_BYTES),
            "log_backup_count": self._data.get(
                "log_backup_count", LOG_BACKUP_COUNT
            ),
            "default_log_level": self._data.get(
                "default_log_level", DEFAULT_LOG_LEVEL
            ),
        }

    def get_min_password_length(self) -> int:
        """Возвращает минимальную длину пароля."""
        return self._data.get("min_password_length", MIN_PASSWORD_LENGTH)

    def reload(self):
        """Перезагружает настройки из файла."""
        self._load_from_file()

    def get_all_settings(self) -> dict:
        """Возвращает все текущие настройки (для отладки)."""
        return self._data.copy()


def create_default_config():
    """Создает файл конфигурации по умолчанию."""
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        default_config = {
            "data_dir": "data",
            "base_currency": "USD",
            "rates_ttl": 3600,
            "request_timeout": 10,
            "min_password_length": 4,
            "log_max_bytes": 500000,
            "log_backup_count": 3,
            "default_log_level": "INFO",
            "comment": "Это файл конфигурации ValutaTrade Hub. "
                       "Измените значения по необходимости."
        }
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print(f"✅ Создан файл конфигурации: {config_path}")
        except IOError as e:
            print(f"⚠️ Не удалось создать файл конфигурации: {e}")


# Автоматически создаем конфиг при импорте модуля.
create_default_config()
