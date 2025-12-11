#!/usr/bin/env python3
"""Модуль для обновления валютных курсов из внешних API."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from valutatrade_hub.infra.settings import SettingsLoader

from ..core.exceptions import ApiRequestError
from ..decorators import log_action
from ..logging_config import get_logger
from .api_clients import BaseApiClient, CoinGeckoClient, ExchangeRateApiClient
from .config import ParserConfig
from .storage import ExchangeHistoryStorage, RatesSnapshotStorage

logger = get_logger(__name__)


class RatesUpdater:
    """Класс для координации обновления валютных курсов."""

    def __init__(
            self,
            cfg: Optional[ParserConfig] = None,
            clients: Optional[List[BaseApiClient]] = None,
            history_path: Optional[str] = None,
            snapshot_path: Optional[str] = None,
    ):
        self.cfg = cfg or ParserConfig()
        self.clients = clients or [
            CoinGeckoClient(self.cfg),
            ExchangeRateApiClient(self.cfg),
        ]

        # Используем SettingsLoader для получения путей
        settings = SettingsLoader()
        self.history = ExchangeHistoryStorage(
            history_path or settings.get_exchange_history_file()
        )
        self.snapshot = RatesSnapshotStorage(
            snapshot_path or settings.get_rates_file()
        )

    @log_action("START_UPDATE", verbose=True)
    def run_update(
            self, source: Optional[str] = None
    ) -> Dict[str, Any]:
        """Выполняет обновление курсов валют."""
        source_name = "всех источников" if not source else source
        logger.info(f"Запуск обновления курсов из {source_name}")

        # Загружаем существующие данные чтобы не потерять их.
        existing_snapshot = self.snapshot.read_snapshot()
        existing_pairs = existing_snapshot.get("pairs", {})

        # Начинаем с существующих данных.
        combined_pairs = existing_pairs.copy()
        errors = []
        total_fetched = 0

        # Выбор клиентов по источнику.
        target_clients = self._select_clients_by_source(source)

        for client in target_clients:
            cname = client.__class__.__name__
            logger.info(f"Получение данных от {cname}...")
            try:
                pairs = client.fetch_rates()
                fetched_count = len(pairs)
                total_fetched += fetched_count

                self._process_client_data(client, pairs, combined_pairs)
                logger.info(f"{cname}: успешно ({fetched_count} курсов).")

            except ApiRequestError as e:
                logger.error(f"Ошибка при получении данных от {cname}: {e}")
                errors.append(str(e))

        if combined_pairs:
            self.snapshot.write_snapshot(combined_pairs)

        result = self._build_result(combined_pairs, total_fetched, errors)

        if errors:
            logger.warning(f"Обновление завершено с {len(errors)} ошибками")
        else:
            logger.info(f"Обновление успешно: {total_fetched} пар")

        return result

    def _select_clients_by_source(
            self, source: Optional[str]
    ) -> List[BaseApiClient]:
        """Выбирает клиентов API на основе указанного источника."""
        if not source:
            return self.clients

        target_clients = []
        source_lower = source.strip().lower()

        for client in self.clients:
            if (isinstance(client, CoinGeckoClient)
                    and source_lower == "coingecko"):
                target_clients.append(client)
            elif (isinstance(client, ExchangeRateApiClient)
                  and source_lower in self._get_exchangerate_aliases()):
                target_clients.append(client)

        return target_clients

    def _get_exchangerate_aliases(self) -> tuple:
        """Возвращает допустимые варианты названий для ExchangeRate API."""
        return (
            "exchangerate",
            "exchange_rate",
            "exchange-rate",
            "exchangerate-api",
        )

    def _process_client_data(
            self,
            client: BaseApiClient,
            pairs: Dict[str, Dict[str, Any]],
            combined_pairs: Dict[str, Dict[str, Any]]
    ):
        """Обрабатывает данные от клиента API и обновляет combined_pairs."""
        for pair_key, meta in pairs.items():
            from_code, to_code = pair_key.split("_", 1)
            timestamp = self._get_timestamp(meta)

            record = {
                "id": f"{from_code}_{to_code}_{timestamp}",
                "from_currency": from_code,
                "to_currency": to_code,
                "rate": meta.get("rate"),
                "timestamp": timestamp,
                "source": meta.get("source"),
                "meta": meta.get("meta", {}),
            }
            self.history.append_record(record)

            # Обновляем существующие данные, а не заменяем.
            self._update_combined_pairs(combined_pairs, pair_key, meta)

    def _get_timestamp(self, meta: Dict[str, Any]) -> str:
        """Возвращает timestamp из метаданных или текущее время."""
        return meta.get(
            "updated_at",
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )

    def _update_combined_pairs(
            self,
            combined_pairs: Dict[str, Dict[str, Any]],
            pair_key: str,
            meta: Dict[str, Any]
    ):
        """Обновляет combined_pairs новыми данными если они свежее."""
        existing = combined_pairs.get(pair_key)
        new_updated_at = meta.get("updated_at", "")

        if (existing is None or
                existing.get("updated_at", "") < new_updated_at):
            combined_pairs[pair_key] = {
                "rate": meta.get("rate"),
                "updated_at": new_updated_at,
                "source": meta.get("source"),
            }

    def _build_result(
            self,
            combined_pairs: Dict[str, Dict[str, Any]],
            total_fetched: int,
            errors: List[str]
    ) -> Dict[str, Any]:
        """Формирует результат выполнения обновления."""
        return {
            "total": len(combined_pairs),
            "fetched": total_fetched,
            "errors": errors,
            "last_refresh": datetime.now(timezone.utc).isoformat().replace(
                "+00:00", "Z"
            ),
        }
