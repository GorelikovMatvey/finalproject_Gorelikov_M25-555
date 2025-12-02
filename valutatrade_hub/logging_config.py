#!/usr/bin/env python3
"""Настройка логирования для приложения."""

import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from valutatrade_hub.infra.settings import SettingsLoader


def setup_logger():
    """Настройка ротации логов для приложения."""
    settings = SettingsLoader()
    log_settings = settings.get_log_settings()

    log_dir = log_settings["log_dir"]
    log_file = log_settings["log_file"]
    log_max_bytes = log_settings["log_max_bytes"]
    log_backup_count = log_settings["log_backup_count"]
    log_level = log_settings["default_log_level"]

    # Создаем директорию для логов.
    os.makedirs(log_dir, exist_ok=True)

    # Создаем основной логгер.
    logger = logging.getLogger("valutatrade_hub")
    logger.setLevel(log_level)

    # Очищаем существующие обработчики (на случай перезагрузки).
    logger.handlers.clear()

    # Форматтер с временем в формате ISO 8601 (UTC)
    class ISOFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            return datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")

    formatter = ISOFormatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # Файловый обработчик с ротацией для actions.log.
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=log_max_bytes,
        backupCount=log_backup_count,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Запрещаем распространение логов на корневой логгер.
    logger.propagate = False

    return logger


# Создаем глобальный логгер при запуске модуля.
_app_logger = setup_logger()


def get_logger(name: str = None):
    """
    Унифицированная точка доступа к логгеру приложения.
    Все логи записываются в один файл actions.log.
    """
    if name:
        # Создаем дочерний логгер с указанным именем.
        child_logger = _app_logger.getChild(name)
        return child_logger
    return _app_logger
