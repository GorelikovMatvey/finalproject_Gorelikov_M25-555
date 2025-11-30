#!/usr/bin/env python3
"""
Абстракция над файловым хранилищем данных (JSON).
Позволяет централизовать доступ к users.json, portfolios.json,
rates.json и т.д.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Union

from valutatrade_hub.core.utils import ensure_data_dir
from valutatrade_hub.logging_config import get_logger

logger = get_logger(__name__)


class JSONDatabase:
    """Универсальный интерфейс для работы с JSON-хранилищем."""

    def __init__(self, base_dir: Union[str, Path] = "data"):
        self.base_dir = Path(base_dir)
        ensure_data_dir()

    def _path(self, filename: str) -> Path:
        return self.base_dir / filename

    def load(
            self, filename: str, default: Union[List, Dict, None] = None
    ) -> Union[List, Dict]:
        """Безопасное чтение JSON-файла."""
        path = self._path(filename)
        if not path.exists():
            logger.warning(f"[DB] Файл {filename} не найден — создан пустой.")
            return default if default is not None else {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(
                    f"[DB] Загружено: {filename} "
                    f"({len(data) if isinstance(data, list) else 'dict'})"
                )

                return data
        except json.JSONDecodeError as e:
            logger.error(f"[DB] Ошибка чтения {filename}: {e}")
            return default if default is not None else {}

    def save(self, filename: str, data: Union[List, Dict]) -> bool:
        """Сохранение данных в JSON."""
        path = self._path(filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(
                "[DB] Сохранено: {} ({})".format(
                    filename,
                    len(data) if isinstance(data, list) else 'dict'
                )
            )
            return True
        except Exception as e:
            logger.error(f"[DB] Ошибка сохранения {filename}: {e}")
            return False

    def exists(self, filename: str) -> bool:
        return self._path(filename).exists()

    def remove(self, filename: str) -> bool:
        """Удаление файла (если существует)."""
        path = self._path(filename)
        try:
            if path.exists():
                os.remove(path)
                logger.info(f"[DB] Удалён файл: {filename}")
                return True
            return False
        except Exception as e:
            logger.error(f"[DB] Не удалось удалить {filename}: {e}")
            return False

    def list_files(self) -> List[str]:
        """Список всех JSON-файлов в data/."""
        files = [f.name for f in self.base_dir.glob("*.json")]
        logger.info(f"[DB] Найдено JSON-файлов: {len(files)}")
        return files


# Глобальный экземпляр для использования в других модулях.
db = JSONDatabase()
