#!/usr/bin/env python3
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from ..core.constants import EXCHANGE_HISTORY_FILE, RATES_FILE


def atomic_write(path: str, data: Any):
    """
    Атомарно записывает данные в JSON — сначала во временный файл,
    затем заменяет основной.
    """
    dirpath = Path(path).parent
    dirpath.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="tmp_", dir=str(dirpath))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except Exception:
            pass
        raise


class ExchangeHistoryStorage:
    """Хранилище истории обновлений exchange_rates.json."""

    def __init__(self, history_path: str = EXCHANGE_HISTORY_FILE):
        self.history_path = history_path
        os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
        if not os.path.exists(self.history_path):
            atomic_write(self.history_path, [])

    def append_record(self, record: Dict[str, Any]):
        """Добавляет запись об обновлении курсов в историю."""
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
        data.append(record)
        atomic_write(self.history_path, data)


class RatesSnapshotStorage:
    """Хранилище текущего снимка курсов (rates.json)."""

    def __init__(self, snapshot_path: str = RATES_FILE):
        self.snapshot_path = snapshot_path
        os.makedirs(os.path.dirname(self.snapshot_path), exist_ok=True)
        if not os.path.exists(self.snapshot_path):
            atomic_write(
                self.snapshot_path, {"pairs": {}, "last_refresh": None}
            )

    def write_snapshot(self, pairs: Dict[str, Dict[str, Any]]):
        """Записывает актуальный снимок курсов в файл."""
        # Гарантируем строгий ISO формат
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = {
            "pairs": pairs,
            "last_refresh": now_iso,
        }
        atomic_write(self.snapshot_path, payload)

    def read_snapshot(self) -> Dict[str, Any]:
        """Читает снимок курсов из файла."""
        try:
            with open(self.snapshot_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"pairs": {}, "last_refresh": None}
