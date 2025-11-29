# !/usr/bin/env python3
"""Модели данных для пользователей, кошельков и портфелей."""

import hashlib
import os
from datetime import datetime
from typing import Dict


class User:
    """Класс пользователя системы."""

    def __init__(
            self,
            user_id: int,
            username: str,
            password: str,
            registration_date: datetime | None = None
    ):
        if not username:
            raise ValueError("Имя пользователя не может быть пустым.")
        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")

        self._user_id = user_id
        self._username = username
        self._salt = os.urandom(4).hex()
        self._hashed_password = self._hash_password(password)
        self._registration_date = registration_date or datetime.now()

    def _hash_password(self, password: str) -> str:
        """Хеширует пароль с использованием соли."""
        return hashlib.sha256(
            (password + self._salt).encode()
        ).hexdigest()

    @property
    def user_id(self) -> int:
        """Возвращает идентификатор пользователя."""
        return self._user_id

    @property
    def username(self) -> str:
        """Возвращает имя пользователя."""
        return self._username

    def verify_password(self, password: str) -> bool:
        """Проверяет соответствие пароля хешу."""
        return self._hashed_password == hashlib.sha256(
            (password + self._salt).encode()
        ).hexdigest()

    def get_user_info(self) -> dict:
        """Возвращает информацию о пользователе для сериализации."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }


class Wallet:
    """Кошелёк пользователя для конкретной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        if not currency_code.isalpha():
            raise ValueError("Некорректный код валюты.")
        self.currency_code = currency_code.upper()
        self._balance = float(balance)

    @property
    def balance(self) -> float:
        """Возвращает текущий баланс кошелька."""
        return self._balance

    def deposit(self, amount: float):
        """Пополняет баланс кошелька."""
        if amount <= 0:
            raise ValueError("Сумма должна быть > 0.")
        self._balance += amount

    def withdraw(self, amount: float):
        """Снимает средства с кошелька."""
        if amount <= 0:
            raise ValueError("Сумма должна быть > 0.")
        if amount > self._balance:
            raise ValueError("Недостаточно средств.")
        self._balance -= amount


class Portfolio:
    """Портфель пользователя с несколькими кошельками."""

    def __init__(self, user_id: int, base_currency: str = "USD"):
        self._user_id = user_id
        self._base_currency = base_currency.upper()
        self._wallets: Dict[str, Wallet] = {}

        # Создаем кошелек базовой валюты при инициализации портфеля
        self.add_currency(self._base_currency)

    @property
    def user_id(self) -> int:
        """Возвращает идентификатор пользователя."""
        return self._user_id

    @property
    def base_currency(self) -> str:
        """Возвращает базовую валюту портфеля."""
        return self._base_currency

    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Возвращает копию словаря кошельков."""
        return self._wallets.copy()

    def add_currency(self, code: str):
        """Добавляет новый кошелёк в портфель."""
        code = code.upper()
        if code in self._wallets:
            return  # Кошелек уже существует, ничего не делаем
        self._wallets[code] = Wallet(code)

    def get_wallet(self, code: str) -> Wallet:
        """Возвращает кошелёк по коду валюты."""
        code = code.upper()
        if code not in self._wallets:
            raise ValueError(f"Кошелёк {code} не найден.")
        return self._wallets[code]

    def get_base_wallet(self) -> Wallet:
        """Возвращает кошелек базовой валюты."""
        return self.get_wallet(self._base_currency)

    def get_total_value(
            self, rates_data: dict, base_currency: str = 'USD'
    ) -> float:
        """
        Рассчитывает общую стоимость портфеля в базовой валюте.
        """
        total_value = 0.0
        base_currency = base_currency.upper()
        exchange_pairs = rates_data.get("pairs", {})

        for currency_code, wallet in self._wallets.items():
            balance = wallet.balance

            # Если валюта совпадает с базовой.
            if currency_code == base_currency:
                total_value += balance
                continue

            # Пытаемся найти прямой курс: currency_code -> base_currency.
            direct_rate_key = f"{currency_code}_{base_currency}"
            if direct_rate_key in exchange_pairs:
                rate_data = exchange_pairs[direct_rate_key]
                rate = rate_data.get("rate", 0.0)
                if rate and rate > 0:
                    total_value += balance * rate
                    continue

            # Пытаемся найти обратный курс: base_currency -> currency_code.
            reverse_rate_key = f"{base_currency}_{currency_code}"
            if reverse_rate_key in exchange_pairs:
                rate_data = exchange_pairs[reverse_rate_key]
                reverse_rate = rate_data.get("rate", 0.0)
                if reverse_rate and reverse_rate > 0:
                    total_value += balance / reverse_rate
                    continue

        return total_value

    def to_dict(self) -> dict:
        """Конвертирует портфель в словарь для сохранения в JSON."""
        active_wallets = {
            code: {
                "currency_code": wallet.currency_code,
                "balance": wallet.balance
            }
            for code, wallet in self._wallets.items()
            if wallet.balance != 0
        }

        return {
            "user_id": self._user_id,
            "base_currency": self._base_currency,
            "wallets": active_wallets
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Portfolio':
        """Создает объект Portfolio из словаря."""
        portfolio = cls(data["user_id"], data.get("base_currency", "USD"))
        for wallet_data in data.get("wallets", {}).values():
            wallet = Wallet(
                currency_code=wallet_data["currency_code"],
                balance=wallet_data["balance"]
            )
            portfolio._wallets[wallet.currency_code] = wallet
        return portfolio
