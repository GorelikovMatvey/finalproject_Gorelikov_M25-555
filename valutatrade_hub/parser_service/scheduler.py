#!/usr/bin/env python3
import threading

from ..logging_config import get_logger
from .config import ParserConfig
from .updater import RatesUpdater

logger = get_logger(__name__)


class SimpleScheduler:
    """Простейший планировщик для периодического обновления курсов."""

    def __init__(self, interval_seconds: int = 300, cfg: ParserConfig = None):
        self.cfg = cfg or ParserConfig()
        self.interval = interval_seconds or self.cfg.REQUEST_TIMEOUT * 30
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.updater = RatesUpdater(self.cfg)

    def _loop(self):
        """Основной цикл с обновлением через заданный интервал."""
        logger.info(f"Планировщик запущен, интервал: {self.interval} с.")
        while not self._stop_event.is_set():
            try:
                result = self.updater.run_update()
                logger.info(f"Результат обновления: {result}")
            except Exception as e:
                logger.error(f"Ошибка обновления в планировщике: {e}")
            self._stop_event.wait(self.interval)
        logger.info("Планировщик остановлен.")

    def start(self):
        """Запускает планировщик в отдельном потоке."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Останавливает планировщик."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
