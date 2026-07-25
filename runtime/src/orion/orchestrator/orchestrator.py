from __future__ import annotations

from orion.bus.event_bus import EventBus
from orion.orchestrator.config import OrchestratorConfig
from orion.runtime.lifecycle import Lifecycle
from orion.services.base import BaseService
from orion.services.ipc_publisher import IPCPublisherService
from orion.services.logging import LoggingService
from orion.services.setup import ServiceContext, setup_runtime_services


class Orchestrator(Lifecycle):
    """
    Coordinates the ORION runtime.

    Responsibilities:
    - Create runtime services
    - Create global services
    - Start and stop all services
    - Register global observers
    """

    def __init__(
        self,
        bus: EventBus,
        config: OrchestratorConfig,
    ) -> None:
        self.bus = bus
        self.config = config

        self.runtime_services: list[BaseService] = []
        self.global_services: list[BaseService] = []
        self.services: list[BaseService] = []

        self.bridge = self.config.bridge

        self._started = False

    async def startup(self) -> None:
        """
        Initialize the ORION runtime.
        """

        if self._started:
            return

        context = ServiceContext(
            llm=self.config.llm,
            memory=self.config.memory,
        )

        self.runtime_services = setup_runtime_services(context)

        self.global_services = [
            LoggingService(),
            IPCPublisherService(bridge=self.bridge),
            # MetricsService(...),
            # TracingService(...),
        ]

        self.services = [
            *self.runtime_services,
            *self.global_services,
        ]

        for service in self.services:
            await service.startup()

        for service in self.global_services:
            self.bus.subscribe_all(service.handle)

        self._started = True

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the ORION runtime.
        """

        if not self._started:
            return

        for service in reversed(self.services):
            try:
                await service.shutdown()
            except Exception as exc:
                print(f"Failed to shutdown {service.__class__.__name__}: {exc}")

        self.runtime_services.clear()
        self.global_services.clear()
        self.services.clear()

        self._started = False
