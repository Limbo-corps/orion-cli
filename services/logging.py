from services.base import BaseService
from events.base import Event

import os
import json 
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import asyncio




class LoggingService(BaseService):
    service_name = "logger"

    def __init__(self, log_dir: str | Path = "logs", log_file: str | Path = None):
        super().__init__()
        self.logger_instance = None
        self.handler = None

        self.log_dir = Path(log_dir)
        self.log_file = Path(log_file) if log_file else self.log_dir / "orion.log"

    async def startup(self)->None:
        try:
            self.log_dir.mkdir(parents=True,exist_ok=True)
            self.logger_instance = logging.getLogger("orion_event_logger")
            self.logger_instance.setLevel(logging.INFO)
            self.logger_instance.propagate = False

            # Config Rotating file handler: 5MB per file , max 5 backups
            self.handler = RotatingFileHandler(
                self.log_file,
                maxBytes=5 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            self.handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger_instance.addHandler(self.handler)
        except Exception as e:
            print(f"Failed to initialize logging service: {e}", file=sys.stderr)
            sys.exit(1)

    async def shutdown(self)->None:
        if self.handler:
            self.handler.close()
            if self.logger_instance:
                self.logger_instance.removeHandler(self.handler)


    async def handle(
        self,
        event: Event,
    ) -> None:
        await asyncio.to_thread(self._log_event_sync, event)

    def _log_event_sync(self, event: Event) -> None:
        if not self.logger_instance:
            return
        try:
            full_dump = event.model_dump(mode="json")

            base_keys = {
                "event_id",
                "status",
                "correlation_id",
                "timestamp",
                "source",
                "message",
            }

            payload = {
                k:v for k,v in full_dump.items() if k not in base_keys
            }

            structured_log = {
                "timestamp":full_dump.get("timestamp"),
                "event_id":full_dump.get("event_id"),
                "correlation_id":full_dump.get("correlation_id"),
                "event_type":event.__class__.__name__,
                "source":full_dump.get("source"),
                "message":full_dump.get("message"),
                "payload":payload,
            }


            self.logger_instance.info(json.dumps(structured_log,ensure_ascii=False))
        except Exception as e:
            print(f"Failed to log event {event.event_id}: {e}", file=sys.stderr)

    def log_event(
        self,
        event: Event,
    ) -> None:
        pass
        # print(
        #     f"[{event.status}] "
        #     f"[{event.timestamp}] "
        #     f"[{event.correlation_id}] "
        #     f"[{event.source}] "
        #     f"{event.__class__.__name__} "
        #     f"{event.message}"
        # )

        # error = getattr(event, "error", None)

        # if error:
        #     print(f"└─ ERROR: {error}")

        # text = getattr(event, "text", None)

        # if text:
        #     print(f"└─ TEXT: {text}")
