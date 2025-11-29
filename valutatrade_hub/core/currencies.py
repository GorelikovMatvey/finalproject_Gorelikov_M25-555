#!/usr/bin/env python3
"""Модуль с классами валют и реестром поддерживаемых валют."""

from abc import ABC, abstractmethod

from .exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный базовый класс для представления валюты."""

    def __init__(self, name: str, code: str):
        """
        Инициализирует валюту.

        Args:
            name: Название валюты.
            code: Код валюты (например, 'USD', 'EUR').
        """
        self.name = name
        self.code = code.upper()

    @abstractmethod
    def get_display_info(self) -> str:
        """
        Возвращает строку с информацией о валюте для отображения.

        Returns:
            Строка с описанием валюты.
        """
        pass


class FiatCurrency(Currency):
    """Класс для представления фиатной валюты."""

    def __init__(self, name: str, code: str, issuing_country: str):
        """
        Инициализирует фиатную валюту.

        Args:
            name: Название валюты.
            code: Код валюты.
            issuing_country: Страна-эмитент валюты.
        """
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        """
        Возвращает информацию о фиатной валюте.

        Returns:
            Строка в формате: [FIAT] CODE — Name (Country)
        """
        return f"[FIAT] {self.code} — {self.name} ({self.issuing_country})"


class CryptoCurrency(Currency):
    """Класс для представления криптовалюты."""

    def __init__(
            self, name: str, code: str, algorithm: str, market_cap: float
    ):
        """
        Инициализирует криптовалюту.

        Args:
            name: Название криптовалюты.
            code: Код криптовалюты.
            algorithm: Алгоритм консенсуса/майнинга.
            market_cap: Рыночная капитализация.
        """
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        """
        Возвращает информацию о криптовалюте.

        Returns:
            Строка в формате: [CRYPTO] CODE — Name (Algo: ..., MCAP: ...)
        """
        return (f"[CRYPTO] {self.code} — {self.name}"
                f" (Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})")


# Реестр поддерживаемых валют
CURRENCY_REGISTRY = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 5.6e11),
    "SOL": CryptoCurrency("Solana", "SOL", "Proof of History", 8.5e10)
}


def get_currency(code: str) -> Currency:
    """
    Возвращает объект валюты по коду.

    Args:
        code: Код валюты для поиска.

    Returns:
        Объект Currency (FiatCurrency или CryptoCurrency).

    Raises:
        CurrencyNotFoundError: Если валюта с указанным кодом не найдена.
    """
    code = code.upper()
    if code not in CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(code)
    return CURRENCY_REGISTRY[code]
