from uuid import uuid4

from bus.event_bus import EventBus

from events.events import (
    PipelineStartEvent,
)

from services.logging import LoggingService
from services.setup import setup_services
from services.tui import TUIService


class Orchestrator:
    def __init__(
        self,
        bus: EventBus,
    ) -> None:

        self.bus = bus

        self.logger = LoggingService()
        self.tui = TUIService()

        self.services = []
        self._started = False

    async def startup(self) -> None:
        """
        Initialize the ORION runtime.
        """

        if self._started:
            return

        #
        # Register core services
        #
        self.services = [
            *setup_services(),
            self.logger,
            self.tui,
        ]

        #
        # Start services
        #
        for service in self.services:
            await service.startup()

        #
        # Global observers
        #
        self.bus.subscribe_all(
            self.logger.handle,
        )

        self.bus.subscribe_all(
            self.tui.handle,
        )

        self._started = True

    async def start_pipeline(self) -> None:
        """
        Start a new pipeline execution.
        """

        await self.bus.publish(
            PipelineStartEvent(
                correlation_id=uuid4(),
                source="orchestrator",
                message="Pipeline started",
            )
        )

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the runtime.
        """

        for service in reversed(self.services):
            try:
                await service.shutdown()

            except Exception as e:
                print(f"Failed to shutdown {service}: {e}")

        self.services.clear()

        self._started = False
