#!/usr/bin/env python3
"""Конфигурация сервиса парсинга валютных курсов."""

import os
from typing import Dict, Tuple

from valutatrade_hub.core.constants import (
    SUPPORTED_CRYPTO,
    SUPPORTED_FIAT,
)
from valutatrade_hub.infra.settings import SettingsLoader


class ParserConfig:
    """
    Класс конфигурации для модуля парсинга.
    Использует SettingsLoader для получения актуальных настроек.
    """

    def __init__(self):
        settings = SettingsLoader()

        # Ключ для ExchangeRate-API (если пуст — используется публичный API).
        self.EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")

        # Эндпоинты API.
        self.COINGECKO_URL: str = settings.get("coingecko_url")
        self.EXCHANGERATE_API_URL: str = settings.get("exchangerate_api_url")
        self.EXCHANGERATE_PUBLIC_FALLBACK: str = settings.get(
            "exchangerate_public_fallback"
        )

        # Валюты через SettingsLoader.
        # Для API используем USD по умолчанию,
        # чтобы гарантировать получение курсов
        self.BASE_FIAT_CURRENCY: str = "USD"  # Фиксируем USD для API.
        self.FIAT_CURRENCIES: Tuple[str, ...] = SUPPORTED_FIAT
        self.CRYPTO_CURRENCIES: Tuple[str, ...] = SUPPORTED_CRYPTO
        self.CRYPTO_ID_MAP: Dict[str, str] = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
        }

        # Пути данных через SettingsLoader.
        self.RATES_FILE_PATH: str = settings.get_rates_file()
        self.HISTORY_FILE_PATH: str = settings.get_exchange_history_file()

        # Формат времени.
        self.TIME_FORMAT: str = "%Y-%m-%dT%H:%M:%SZ"

        # Сетевые параметры через SettingsLoader.
        self.REQUEST_TIMEOUT: int = settings.get_request_timeout()

        # Прочее.
        self.USER_AGENT: str = settings.get_user_agent()
