from services.base import BaseService
from events.base import Event

class LoggingService(BaseService):
    service_name = "logger"

    async def handle(
        self,
        event: Event,
    ) -> None:
        self.log_event(event)

    def log_event(
        self,
        event: Event,
    ) -> None:

        print(
            f"[{event.status}] "
            f"[{event.timestamp}] "
            f"[{event.correlation_id}] "
            f"[{event.source}] "
            f"{event.__class__.__name__} "
            f"{event.message}"
        )

        error = getattr(event, "error", None)

        if error:
            print(f"└─ ERROR: {error}")
        
        text = getattr(event, "text", None)

        if text:
            print(f"└─ TEXT: {text}")