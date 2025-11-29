#!/usr/bin/env python3
"""
Бизнес-логика приложения.
Здесь реализованы все основные операции: регистрация, авторизация,
управление портфелем, трейды и работа с курсами валют.
"""

import hashlib
import json
from datetime import datetime
from typing import Optional

from prettytable import PrettyTable

from ..core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from ..decorators import log_action
from ..infra.settings import SettingsLoader
from ..parser_service.config import ParserConfig
from ..parser_service.updater import RatesUpdater
from .currencies import get_currency
from .models import Portfolio, User
from .utils import ensure_data_dir, load_json, save_json

_current_user: Optional[User] = None


def _load_user_portfolio(user_id: int) -> Portfolio:
    """Загружает портфель пользователя или создает новый."""
    settings = SettingsLoader()
    portfolios_file = settings.get_portfolios_file()
    portfolios_data = load_json(portfolios_file)
    portfolio_data = next(
        (p for p in portfolios_data if p["user_id"] == user_id), None
    )

    if not portfolio_data:
        portfolio = Portfolio(user_id, settings.get_base_currency())
        _save_user_portfolio(portfolio)
        return portfolio

    return Portfolio.from_dict(portfolio_data)


def _save_user_portfolio(portfolio: Portfolio):
    """Сохраняет портфель пользователя."""
    settings = SettingsLoader()
    portfolios_file = settings.get_portfolios_file()
    portfolios_data = load_json(portfolios_file)
    portfolios_data = [
        p for p in portfolios_data if p["user_id"] != portfolio.user_id
    ]
    portfolios_data.append(portfolio.to_dict())
    save_json(portfolios_file, portfolios_data)


def _validate_user_logged_in() -> User:
    """Проверяет, что пользователь авторизован."""
    user = get_logged_user()
    if not user:
        raise ValueError("Сначала выполните login.")
    return user


def _validate_positive_amount(amount: float):
    """Проверяет, что сумма положительная."""
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом.")


def _validate_currency_code(currency_code: str):
    """Проверяет существование валюты."""
    try:
        get_currency(currency_code)
    except CurrencyNotFoundError:
        raise CurrencyNotFoundError(currency_code)


def _get_conversion_rate(
        from_currency: str, to_currency: str
) -> Optional[float]:
    """Получает курс конвертации между валютами."""
    if from_currency == to_currency:
        return 1.0

    settings = SettingsLoader()
    rates_file = settings.get_rates_file()
    rates = load_json(rates_file)
    exchange_pairs = rates.get("pairs", {})

    direct_key = f"{from_currency}_{to_currency}"
    if direct_key in exchange_pairs:
        rate_data = exchange_pairs[direct_key]
        rate = rate_data.get("rate")
        if rate and rate > 0:
            return float(rate)

    reverse_key = f"{to_currency}_{from_currency}"
    if reverse_key in exchange_pairs:
        rate_data = exchange_pairs[reverse_key]
        reverse_rate = rate_data.get("rate")
        if reverse_rate and reverse_rate > 0:
            return 1.0 / float(reverse_rate)

    if from_currency != "USD" and to_currency != "USD":
        usd_to_from = _get_conversion_rate(from_currency, "USD")
        usd_to_to = _get_conversion_rate("USD", to_currency)
        if usd_to_from and usd_to_from > 0 and usd_to_to and usd_to_to > 0:
            return usd_to_from * usd_to_to

    return None


def _format_currency_message(
        action: str, currency: str, amount: float, rate: Optional[float],
        old_bal: float, base_currency: str = "USD"
) -> str:
    """Форматирует сообщение о валютной операции."""
    new_bal = old_bal + amount if action == "buy" else old_bal - amount
    action_verb = "Покупка" if action == "buy" else "Продажа"

    if rate and rate > 0:
        value = amount * rate
        value_type = 'стоимость' if action == 'buy' else 'выручка'
        value_info = f"Оценочная {value_type}: {value:.4f} {base_currency}"
        rate_info = f"по курсу {rate:.4f} {base_currency}/{currency}"
    else:
        value_info = (
            "⚠️ Курс для расчета стоимости недоступен. "
            "Выполните 'update-rates'."
        )
        rate_info = "курс недоступен"

    return (
        f"{action_verb} выполнена: {amount:.4f} {currency} {rate_info}\n"
        f"Изменения в портфеле:\n"
        f"- {currency}: было {old_bal:.4f} → "
        f"{'стало' if action == 'buy' else 'осталось'} {new_bal:.4f}\n"
        f"{value_info}"
    )


def _format_operation_result(
        action: str, currency: str, amount: float, converted_amount: float,
        rate: float, old_balance: float, new_balance: float,
        base_currency: str, old_base_balance: float, new_base_balance: float
) -> str:
    """Форматирует результат операции покупки/продажи."""
    action_verb = "Покупка" if action == "buy" else "Продажа"
    amount_type = "Стоимость" if action == "buy" else "Выручка"
    rate_pair = (
        f"{base_currency}/{currency}"
        if action == "buy"
        else f"{currency}/{base_currency}"
    )

    return (
        f"✅ {action_verb} выполнена: {amount:.4f} {currency}\n"
        f" {amount_type}: {converted_amount:.4f} {base_currency} "
        f"(курс: {rate:.6f} {rate_pair})\n"
        f" Изменения в портфеле:\n"
        f"- {base_currency}: было {old_base_balance:.4f} → "
        f"стало {new_base_balance:.4f}\n"
        f"- {currency}: было {old_balance:.4f} → "
        f"стало {new_balance:.4f}"
    )


def _get_rates_unavailable_message(base_currency: str, code: str) -> str:
    """Возвращает сообщение о недоступности курса."""
    return (
        f"❌ Курс {base_currency}→{code} недоступен. "
        f"Выполните 'update-rates'."
    )


@log_action("buy")
def buy(currency: str, amount: float) -> str:
    """Покупка валюты."""

    user = _validate_user_logged_in()

    _validate_positive_amount(amount)

    code = currency.upper()
    _validate_currency_code(code)

    portfolio = _load_user_portfolio(user.user_id)
    base_currency = portfolio.base_currency

    # Проверяем, что не пытаемся купить базовую валюту.
    if code == base_currency:
        return f"❌ Нельзя покупать базовую валюту ({base_currency})."

    # Получаем курс конвертации.
    rate = _get_conversion_rate(base_currency, code)
    if not rate or rate <= 0:
        return _get_rates_unavailable_message(base_currency, code)

    # Рассчитываем стоимость в базовой валюте.
    cost_in_base = amount / rate

    # Проверяем достаточность средств в базовой валюте.
    base_wallet = portfolio.get_base_wallet()
    if base_wallet.balance < cost_in_base:
        raise InsufficientFundsError(
            available=base_wallet.balance,
            required=cost_in_base,
            code=base_currency
        )

    # Выполняем операцию: списываем базовую валюту, добавляем целевую.
    old_base_balance = base_wallet.balance
    base_wallet.withdraw(cost_in_base)

    # Создаем/получаем кошелек для целевой валюты.
    if code not in portfolio.wallets:
        portfolio.add_currency(code)
    target_wallet = portfolio.get_wallet(code)
    old_target_balance = target_wallet.balance
    target_wallet.deposit(amount)

    _save_user_portfolio(portfolio)

    return _format_operation_result(
        action="buy",
        currency=code,
        amount=amount,
        converted_amount=cost_in_base,
        rate=rate,
        old_balance=old_target_balance,
        new_balance=target_wallet.balance,
        base_currency=base_currency,
        old_base_balance=old_base_balance,
        new_base_balance=base_wallet.balance
    )


@log_action("sell")
def sell(currency: str, amount: float) -> str:
    """Продажа валюты."""
    user = _validate_user_logged_in()

    _validate_positive_amount(amount)

    code = currency.upper()
    _validate_currency_code(code)

    portfolio = _load_user_portfolio(user.user_id)
    base_currency = portfolio.base_currency

    # Проверяем, что не пытаемся продать базовую валюту.
    if code == base_currency:
        return f"❌ Продажа базовой валюты ({base_currency}) запрещена."

    # Проверяем наличие кошелька и достаточность средств.
    if code not in portfolio.wallets:
        return f"❌ У вас нет валюты '{code}' для продажи."

    target_wallet = portfolio.get_wallet(code)
    if target_wallet.balance < amount:
        raise InsufficientFundsError(
            available=target_wallet.balance,
            required=amount,
            code=code
        )

    # Получаем курс конвертации.
    rate = _get_conversion_rate(code, base_currency)
    if not rate or rate <= 0:
        return _get_rates_unavailable_message(code, base_currency)

    # Рассчитываем выручку в базовой валюте.
    revenue_in_base = amount * rate

    # Выполняем операцию: списываем целевую валюту, добавляем базовую.
    old_target_balance = target_wallet.balance
    target_wallet.withdraw(amount)

    base_wallet = portfolio.get_base_wallet()
    old_base_balance = base_wallet.balance
    base_wallet.deposit(revenue_in_base)

    _save_user_portfolio(portfolio)

    return _format_operation_result(
        action="sell",
        currency=code,
        amount=amount,
        converted_amount=revenue_in_base,
        rate=rate,
        old_balance=old_target_balance,
        new_balance=target_wallet.balance,
        base_currency=base_currency,
        old_base_balance=old_base_balance,
        new_base_balance=base_wallet.balance
    )


@log_action("deposit")
def deposit(amount: float) -> str:
    """Пополнение базовой валюты для тестирования."""
    user = _validate_user_logged_in()

    _validate_positive_amount(amount)

    portfolio = _load_user_portfolio(user.user_id)
    base_currency = portfolio.base_currency

    base_wallet = portfolio.get_base_wallet()
    old_balance = base_wallet.balance
    base_wallet.deposit(amount)

    _save_user_portfolio(portfolio)

    return (
        f"✅ Базовая валюта пополнена: +{amount:.4f} {base_currency}\n"
        f" Баланс {base_currency}: было {old_balance:.4f} → "
        f"стало {base_wallet.balance:.4f}"
    )


def _check_data_freshness(rates_data: dict) -> Optional[str]:
    """Проверяет свежесть данных о курсах."""
    settings = SettingsLoader()
    last_refresh = rates_data.get("last_refresh")

    if not last_refresh:
        return "Данные курсов не имеют временной метки."

    try:
        last_update = datetime.fromisoformat(
            last_refresh.replace("Z", "+00:00")
        )
        now = datetime.now().astimezone()
        ttl = settings.get_ttl()

        if now - last_update > ttl:
            minutes = ttl.total_seconds() / 60
            return (
                f"⚠️ Данные курсов устарели "
                f"(последнее обновление: {last_refresh}).\n"
                f"⚠️ TTL: {minutes:.1f} минут.\n"
                f"⚠️ Выполните 'update-rates' для обновления данных."
            )
    except (ValueError, TypeError) as e:
        return f"⚠️ Ошибка проверки свежести данных: {e}"

    return None


@log_action("register")
def register(username: str, password: str) -> str:
    """Регистрация нового пользователя."""
    ensure_data_dir()
    settings = SettingsLoader()
    users_file = settings.get_users_file()
    users = load_json(users_file)

    if any(u["username"] == username for u in users):
        return f"Имя пользователя '{username}' уже занято."

    min_password_length = settings.get_min_password_length()

    if len(password) < min_password_length:
        return (
            f"Пароль должен быть не короче "
            f"{min_password_length} символов."
        )

    user_id = len(users) + 1
    user = User(user_id=user_id, username=username, password=password)

    users.append({
        "user_id": user.user_id,
        "username": user.username,
        "hashed_password": user._hashed_password,
        "salt": user._salt,
        "registration_date": user._registration_date.isoformat()
    })
    save_json(users_file, users)

    # Создаем портфель с базовой валютой.
    portfolio = Portfolio(user_id, settings.get_base_currency())
    _save_user_portfolio(portfolio)

    return (
        f"Пользователь '{username}' зарегистрирован (id={user_id}). "
        f"Войдите: login --username {username} --password ****"
    )


@log_action("login")
def login(username: str, password: str) -> str:
    """Авторизация пользователя."""
    global _current_user
    settings = SettingsLoader()
    users_file = settings.get_users_file()
    users = load_json(users_file)

    found = next((u for u in users if u["username"] == username), None)
    if not found:
        return f"Пользователь '{username}' не найден."

    hashed = hashlib.sha256((password + found["salt"]).encode()).hexdigest()
    if hashed != found["hashed_password"]:
        return "Неверный пароль."

    _current_user = User(
        user_id=found["user_id"],
        username=found["username"],
        password=password,
        registration_date=datetime.fromisoformat(found["registration_date"]),
    )
    _current_user._salt = found["salt"]
    _current_user._hashed_password = found["hashed_password"]

    return f"Вы вошли как '{username}'."


def get_logged_user() -> Optional[User]:
    """Возвращает текущего авторизованного пользователя."""
    return _current_user


def show_portfolio(base_currency: Optional[str] = None) -> str:
    """Отображает портфель пользователя."""
    user = _validate_user_logged_in()

    settings = SettingsLoader()
    portfolio = _load_user_portfolio(user.user_id)
    base = (
        base_currency.upper()
        if base_currency
        else portfolio.base_currency
    )

    try:
        _validate_currency_code(base)
    except CurrencyNotFoundError:
        return f"Неизвестная базовая валюта '{base}'."

    if not portfolio.wallets:
        return "Портфель пуст."

    rates_file = settings.get_rates_file()
    rates = load_json(rates_file)

    table = PrettyTable()
    table.field_names = ["Валюта", "Баланс", f"Стоимость в {base}"]
    table.align["Валюта"] = "l"
    table.align["Баланс"] = "r"
    table.align[f"Стоимость в {base}"] = "r"

    total_value = 0.0
    has_unavailable_rates = False

    for currency_code, wallet in portfolio.wallets.items():
        bal = wallet.balance

        if currency_code == base:
            value = bal
            value_str = f"{value:.4f}"
            total_value += value
        else:
            rate = _get_conversion_rate(currency_code, base)
            if rate and rate > 0:
                value = bal * rate
                value_str = f"{value:.4f}"
                total_value += value
            else:
                value_str = "курс недоступен"
                has_unavailable_rates = True

        table.add_row([currency_code, f"{bal:.4f}", value_str])

    result = [
        f" Портфель пользователя '{user.username}' (база: {base}):",
        "",
        table.get_string(),
        "",
        f" Общая стоимость: {total_value:.4f} {base}"
    ]

    if has_unavailable_rates:
        result.append("")
        result.append(
            "⚠️ Для некоторых валют курсы недоступен. "
            "Выполните 'update-rates'."
        )

    freshness_error = _check_data_freshness(rates)
    if freshness_error:
        result.append("")
        result.append(freshness_error)

    return "\n".join(result)


def get_rate(from_code: str, to_code: str) -> str:
    """Получает курс между двумя валютами."""
    from_code = from_code.upper()
    to_code = to_code.upper()

    _validate_currency_code(from_code)
    _validate_currency_code(to_code)

    settings = SettingsLoader()
    rates_file = settings.get_rates_file()

    rates = load_json(rates_file)

    if not rates or "pairs" not in rates or not rates["pairs"]:
        return "Локальный кеш курсов пуст. Выполните 'update-rates'."

    freshness_error = _check_data_freshness(rates)
    if freshness_error:
        return freshness_error

    key = f"{from_code}_{to_code}"
    reverse_key = f"{to_code}_{from_code}"
    pair = rates["pairs"].get(key)
    reverse = rates["pairs"].get(reverse_key)

    if pair:
        rate = pair["rate"]
        updated = pair.get("updated_at", rates.get("last_refresh"))
        reverse_rate = 1 / rate if rate and rate != 0 else None
        return (
            f"Курс {from_code}→{to_code}: {rate:.6f} (обновлено: {updated})"
            f"\nОбратный курс {to_code}→{from_code}: {reverse_rate:.6f}"
        )
    elif reverse:
        rate = reverse["rate"]
        updated = reverse.get("updated_at", rates.get("last_refresh"))
        direct_rate = 1 / rate if rate and rate != 0 else None
        return (
            f"Курс {from_code}→{to_code}: {direct_rate:.6f} "
            f"(обновлено: {updated})\n"
            f"Обратный курс {to_code}→{from_code}: {rate:.6f}"
        )
    else:
        return (
            f"Курс {from_code}→{to_code} недоступен. "
            f"Повторите попытку позже."
        )


def update_rates(source: Optional[str] = None) -> str:
    """Обновляет курсы валют."""
    cfg = ParserConfig()
    updater = RatesUpdater(cfg=cfg)

    try:
        res = updater.run_update(source=source)
    except Exception as e:
        raise ApiRequestError(str(e))

    raw_time = res.get("last_refresh")
    formatted_time = raw_time or "неизвестно"

    fetched = res.get("fetched", 0)
    errors = res.get("errors", [])

    source_name = "все источники"
    if source == "coingecko":
        source_name = "CoinGecko"
    elif source == "exchangerate":
        source_name = "ExchangeRate API"

    if errors:
        return (
            f"⚠️ Обновление с {source_name} завершено с ошибками.\n"
            f"✅ Успешно обновлено: {fetched} пар\n"
            f"❌ Ошибок: {len(errors)}\n"
            f" Время: {formatted_time}"
        )
    else:
        return (
            f"✅ Курсы успешно обновлены с {source_name}!\n"
            f" Обновлено пар: {fetched}\n"
            f" Время: {formatted_time}"
        )


def show_rates(
        currency: Optional[str] = None,
        top: Optional[int] = None,
        base: Optional[str] = None
) -> str:
    """Отображает курсы валют."""
    settings = SettingsLoader()
    rates_file = settings.get_rates_file()

    try:
        with open(rates_file, "r", encoding="utf-8") as f:
            snap = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "Локальный кеш курсов пуст. Выполните 'update-rates'."

    pairs = snap.get("pairs", {})
    last = snap.get("last_refresh")

    if not pairs:
        return "Локальный кеш курсов пуст. Выполните 'update-rates'."

    currency = currency.upper() if currency else None
    base = base.upper() if base else "USD"

    if currency:
        try:
            _validate_currency_code(currency)
        except CurrencyNotFoundError:
            return f"Неизвестная валюта '{currency}'."

    if base:
        try:
            _validate_currency_code(base)
        except CurrencyNotFoundError:
            return f"Неизвестная базовая валюта '{base}'."

    filtered = {}
    for k, v in pairs.items():
        try:
            from_c, to_c = k.split("_", 1)
        except ValueError:
            continue
        if currency and currency != from_c and currency != to_c:
            continue
        if base and base != from_c and base != to_c:
            continue
        filtered[k] = v

    if last:
        try:
            dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
            formatted_time = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            formatted_time = last
    else:
        formatted_time = "неизвестно"

    if top:
        items = [
            (k, v) for k, v in filtered.items()
            if k.endswith(f"_{base}") and v.get("rate", 0) > 0
        ]
        items.sort(key=lambda kv: kv[1].get("rate", 0), reverse=True)
        items = items[:top]

        if not items:
            return "❌ Не найдено подходящих курсов для отображения."

        table = PrettyTable()
        table.field_names = ["#", "Пара", "Курс", "Источник"]
        table.align["#"] = "r"
        table.align["Пара"] = "l"
        table.align["Курс"] = "r"
        table.align["Источник"] = "l"

        for i, (k, v) in enumerate(items, 1):
            from_curr, to_curr = k.split("_", 1)
            rate = v.get("rate", 0)
            source = v.get("source", "unknown")
            table.add_row(
                [i, f"{from_curr} → {to_curr}", f"{rate:.6f}", source]
            )

        result = [
            f" Курсы валют (обновлено: {formatted_time})",
            f" Базовая валюта отображения: {base}",
            "",
            f" Топ-{top} курсов к {base}:",
            table.get_string()
        ]

    else:
        if not filtered:
            return "❌ Не найдено курсов по указанным фильтрам."

        table = PrettyTable()
        table.field_names = ["Пара", "Курс", "Источник"]
        table.align["Пара"] = "l"
        table.align["Курс"] = "r"
        table.align["Источник"] = "l"

        for k in sorted(filtered.keys()):
            v = filtered[k]
            from_curr, to_curr = k.split("_", 1)
            rate = v.get("rate", 0)
            source = v.get("source", "unknown")

            if rate >= 1:
                rate_str = f"{rate:,.4f}"
            else:
                rate_str = f"{rate:.8f}"

            table.add_row([f"{from_curr} → {to_curr}", rate_str, source])

        result = [
            f" Курсы валют (обновлено: {formatted_time})",
            f" Базовая валюта отображения: {base}",
            "",
            table.get_string()
        ]

    freshness_error = _check_data_freshness(snap)
    if freshness_error:
        result.append("")
        result.append(freshness_error)

    return "\n".join(result)
