from abc import ABC, abstractmethod
from bus.event_bus import EventBus
from events.base import Event

class BaseService(ABC):
    """
    Base class for all services.

    Reponsibilities:
    - Provides access to the Event Bus
    - Provides event publishing helper
    - Provides lifecycle hooks
    """
    service_name: str = "base"
    subscribed_events: list[type[Event]] = []

    def __init__(self):
        self.bus = EventBus()

    async def publish(
        self,
        event: Event
    ) -> None:
        await self.bus.publish(event)

    @abstractmethod
    async def handle(
        self,
        event: Event
    ) -> None:
        """
        Handle an incoming event
        """
        pass

    async def startup(self) -> None:
        """
        Called during application startup.
        Override if needed.
        """
        pass

    async def shutdown(self) -> None:
        """
        Called during application shutdown.
        Override if needed.
        """
        pass

    def register(self) -> None:
        """
        Register the Service
        """
        for event_type in self.subscribed_events:
            self.bus.subscribe(
                event_type,
                self.handle
            )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}"

    