#!/usr/bin/env python3
"""
Пользовательские исключения.
"""


class InsufficientFundsError(Exception):
    """Исключение при недостатке средств для операции."""

    def __init__(self, available: float, required: float, code: str):
        super().__init__(
            f"Недостаточно средств:"
            f" {available:.4f} {code} < {required:.4f} {code}"
        )


class CurrencyNotFoundError(Exception):
    """Исключение при запросе неизвестной валюты."""

    def __init__(self, code: str):
        super().__init__(f"Неизвестная валюта '{code}'")


class ApiRequestError(Exception):
    """Исключение при ошибках обращения к внешнему API."""

    def __init__(self, reason: str):
        super().__init__(f"Ошибка при обращении к API: {reason}")
