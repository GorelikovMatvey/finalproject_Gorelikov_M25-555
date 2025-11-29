#!/usr/bin/env python3
import json
import os
from typing import Any

from valutatrade_hub.infra.settings import SettingsLoader


def ensure_data_dir():
    """Создаёт структуру папок и базовые JSON файлы, если они отсутствуют."""
    settings = SettingsLoader()
    data_dir = settings.get_data_dir()

    os.makedirs(data_dir, exist_ok=True)

    # Получаем пути из настроек.
    users_file = settings.get_users_file()
    portfolios_file = settings.get_portfolios_file()
    rates_file = settings.get_rates_file()

    for path in [users_file, portfolios_file, rates_file]:
        if not os.path.exists(path):
            # Файлы users.json и portfolios.json содержат списки.
            # Файл rates.json содержит объект.
            initial_data = (
                [] if any(k in path for k in ("users", "portfolios"))
                else {}
            )
            with open(path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=4, ensure_ascii=False)


def load_json(path: str) -> Any:
    """Безопасная загрузка JSON-файлов."""
    if not os.path.exists(path):
        return (
            [] if any(k in path for k in ("users", "portfolios"))
            else {}
        )
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return (
                [] if any(k in path for k in ("users", "portfolios"))
                else {}
            )


def save_json(path: str, data: Any):
    """Сохраняет данные в JSON с красивым форматированием."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
