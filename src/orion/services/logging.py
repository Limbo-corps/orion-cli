from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from orion.events.base import Event
from orion.services.base import BaseService


class LoggingService(BaseService):
    service_name = "logger"

    def __init__(
        self,
        log_dir: str | Path = "logs",
        log_file: str | Path | None = None,
    ) -> None:
        super().__init__()

        self.log_dir = Path(log_dir)
        self.log_file = Path(log_file) if log_file else self.log_dir / "orion.log"

        self.logger = logging.getLogger("orion")

    async def startup(self) -> None:
        self.log_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Prevent duplicate handlers on restart
        self.logger.handlers.clear()

        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        handler = RotatingFileHandler(
            filename=self.log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )

        handler.setFormatter(logging.Formatter("%(message)s"))

        self.logger.addHandler(handler)

        # Force creation of the file
        self.logger.info(json.dumps({"event": "LoggingService started"}))

        for h in self.logger.handlers:
            h.flush()

        print(f"[LOGGER] {self.log_file.resolve()}")

    async def shutdown(self) -> None:
        for handler in self.logger.handlers[:]:
            handler.flush()
            handler.close()
            self.logger.removeHandler(handler)

    async def handle(
        self,
        event: Event,
    ) -> None:
        self._log(event)

    def _log(
        self,
        event: Event,
    ) -> None:

        dump = event.model_dump(mode="json")

        payload = {
            k: v
            for k, v in dump.items()
            if k
            not in {
                "event_id",
                "status",
                "correlation_id",
                "timestamp",
                "source",
                "message",
            }
        }

        self.logger.info(
            json.dumps(
                {
                    "timestamp": dump["timestamp"],
                    "event_id": dump["event_id"],
                    "correlation_id": dump["correlation_id"],
                    "event_type": event.__class__.__name__,
                    "status": dump["status"],
                    "source": dump["source"],
                    "message": dump["message"],
                    "payload": payload,
                },
                ensure_ascii=False,
            )
        )

        for handler in self.logger.handlers:
            handler.flush()
