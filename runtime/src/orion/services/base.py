from abc import ABC, abstractmethod
from uuid import UUID

from orion.bus.event_bus import EventBus
from orion.events.base import Event


class BaseService(ABC):
    """
    Base class for all services.

    Responsibilities:
    - Provides access to the Event Bus.
    - Provides event publishing helper.
    - Provides event validation.
    - Provides lifecycle hooks.
    """

    service_name: str = "base"
    subscribed_events: list[type[Event]] = []

    def __init__(self) -> None:
        self.bus = EventBus()

    async def publish(self, event: Event) -> None:
        """Publish an event through the Event Bus."""
        await self.bus.publish(event)

    def validate_event(
        self,
        event: Event,
    ) -> tuple[UUID, UUID]:
        """
        Validate and return the session and correlation identifiers.

        Request-scoped events must contain both identifiers.
        """

        assert isinstance(
            event.session_id,
            UUID,
        ), "Event session_id must be a UUID"

        assert isinstance(
            event.correlation_id,
            UUID,
        ), "Event correlation_id must be a UUID"

        return event.session_id, event.correlation_id

    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle an incoming event."""
        pass

    async def startup(self) -> None:
        """Called during application startup."""
        pass

    async def shutdown(self) -> None:
        """Called during application shutdown."""
        pass

    def register(self) -> None:
        """Register the service for its subscribed events."""

        for event_type in self.subscribed_events:
            self.bus.subscribe(
                event_type,
                self.handle,
            )

    def __str__(self) -> str:
        return self.__class__.__name__
