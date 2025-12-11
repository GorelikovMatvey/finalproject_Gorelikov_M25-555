#!/usr/bin/env python3
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict

import requests

from ..core.exceptions import ApiRequestError
from .config import ParserConfig


class BaseApiClient(ABC):
    """Абстрактный интерфейс для клиентов API валютных курсов."""

    def __init__(self, cfg: ParserConfig):
        self.cfg = cfg

    @abstractmethod
    def fetch_rates(self) -> Dict[str, Dict[str, Any]]:
        """
        Возвращает стандартизированные данные:
        {"BTC_USD": {"rate": 59337.21, "source": "CoinGecko",
        "updated_at": "ISO"}, ... }.
        """
        pass


class CoinGeckoClient(BaseApiClient):
    """Клиент для получения криптокурсов с CoinGecko."""

    def fetch_rates(self) -> Dict[str, Dict[str, Any]]:
        ids = ",".join(self.cfg.CRYPTO_ID_MAP.values())
        base_currency = self.cfg.BASE_FIAT_CURRENCY  # Всегда USD
        params = {"ids": ids, "vs_currencies": base_currency.lower()}
        headers = {"User-Agent": self.cfg.USER_AGENT}

        try:
            resp = requests.get(
                self.cfg.COINGECKO_URL,
                params=params,
                headers=headers,
                timeout=self.cfg.REQUEST_TIMEOUT,
            )
            resp.raise_for_status()

            try:
                data = resp.json()
            except json.JSONDecodeError as e:
                raise ApiRequestError(f"Некорректный JSON от CoinGecko: {e}")

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Ошибка запроса CoinGecko: {e}")
        except Exception as e:
            raise ApiRequestError(f"Неожиданная ошибка CoinGecko: {e}")

        result: Dict[str, Dict[str, Any]] = {}
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        for code, raw_id in self.cfg.CRYPTO_ID_MAP.items():
            raw = data.get(raw_id, {})
            rate = raw.get(base_currency.lower())
            if rate is None:
                continue

            key = f"{code}_{base_currency}"
            result[key] = {
                "rate": float(rate),
                "source": "CoinGecko",
                "updated_at": ts,
                "meta": {"raw_id": raw_id, "status_code": resp.status_code},
            }

            inv_key = f"{base_currency}_{code}"
            inv_rate = 1.0 / float(rate) if float(rate) != 0 else 0.0
            result[inv_key] = {
                "rate": inv_rate,
                "source": "CoinGecko",
                "updated_at": ts,
                "meta": {"raw_id": raw_id, "status_code": resp.status_code},
            }

        return result


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для получения фиатных курсов с ExchangeRate API."""

    def fetch_rates(self) -> Dict[str, Dict[str, Any]]:
        base = self.cfg.BASE_FIAT_CURRENCY
        headers = {"User-Agent": self.cfg.USER_AGENT}
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Выбор эндпоинта: приватный (с API-ключом) или публичный.
        if self.cfg.EXCHANGERATE_API_KEY:
            url = (
                f"{self.cfg.EXCHANGERATE_API_URL}/"
                f"{self.cfg.EXCHANGERATE_API_KEY}/latest/{base}"
            )
        else:
            url = f"{self.cfg.EXCHANGERATE_PUBLIC_FALLBACK}/{base}"

        try:
            resp = requests.get(
                url, headers=headers, timeout=self.cfg.REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Ошибка запроса ExchangeRate API: {e}")
        except Exception as e:
            raise ApiRequestError(f"Неожиданная ошибка ExchangeRate API: {e}")

        rates = data.get("rates") or data.get("conversion_rates")
        if not rates:
            raise ApiRequestError(
                "Некорректный ответ ExchangeRate API — отсутствует 'rates'."
            )

        result: Dict[str, Dict[str, Any]] = {}

        for code in self.cfg.FIAT_CURRENCIES:
            if code == base:
                continue

            try:
                rate_from_base = float(rates.get(code))
            except (TypeError, ValueError):
                continue

            key = f"{base}_{code}"
            result[key] = {
                "rate": rate_from_base,
                "source": "ExchangeRate-API",
                "updated_at": ts,
                "meta": {"status_code": resp.status_code},
            }

            inv_key = f"{code}_{base}"
            inv_rate = 1.0 / rate_from_base if rate_from_base != 0 else 0.0
            result[inv_key] = {
                "rate": inv_rate,
                "source": "ExchangeRate-API",
                "updated_at": ts,
                "meta": {"status_code": resp.status_code},
            }

        return result
