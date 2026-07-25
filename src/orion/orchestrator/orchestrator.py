from orion.bus.event_bus import EventBus

from orion.orchestrator.config import OrchestratorConfig
from orion.services.logging import LoggingService
from orion.services.setup import ServiceContext, setup_services
from orion.runtime.lifecycle import Lifecycle

class Orchestrator(Lifecycle):
    """
    Coordinates the ORION runtime.

    Responsibilities:
    - Startup / shutdown services
    - Wire global observers
    """

    def __init__(
        self,
        bus: EventBus,
        config: OrchestratorConfig,
    ) -> None:
        self.bus = bus
        self.config = config

        self.logger = LoggingService()

        self.services = []
        self._started = False

    async def startup(self) -> None:
        """
        Initialize the ORION runtime.
        """

        if self._started:
            return

        service_context = ServiceContext(
            llm=self.config.llm,
            memory=self.config.memory,
        )

        self.services = [
            *setup_services(service_context),
            self.logger,
        ]

        for service in self.services:
            await service.startup()

        self.bus.subscribe_all(self.logger.handle)

        self._started = True

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the runtime.
        """

        for service in reversed(self.services):
            try:
                await service.shutdown()
            except Exception as exc:
                print(f"Failed to shutdown {service}: {exc}")

        self.services.clear()
        self._started = False
