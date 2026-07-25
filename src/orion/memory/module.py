from __future__ import annotations

from uuid import UUID

from orion.bus.event_bus import EventBus
from orion.memory.config import MemoryConfig
from orion.memory.factory import MemoryFactory
from orion.memory.planner.planner import RetrievalPlanner
from orion.memory.session import MemorySession
from orion.runtime.lifecycle import Lifecycle


class MemoryModule(Lifecycle):
    """
    Application-wide memory subsystem.
    Owns all memory providers and the retrieval planner.
    """

    def __init__(
        self,
        config: MemoryConfig,
        planner: RetrievalPlanner,
    ) -> None:
        self.event_bus = EventBus()

        self.providers = MemoryFactory.create(config)

        self.embeddings = self.providers.embeddings
        self.summary = self.providers.summary
        self.vector = self.providers.vector
        self.graph = self.providers.graph

        self.planner = planner

    async def startup(self) -> None:
        await self.embeddings.startup()
        await self.summary.startup()
        await self.vector.startup()
        await self.graph.startup()

    async def shutdown(self) -> None:
        await self.graph.shutdown()
        await self.vector.shutdown()
        await self.summary.shutdown()

    async def clear(self) -> None:
        await self.summary.clear()
        await self.vector.clear()
        await self.graph.clear()

    def session(
        self,
        correlation_id: UUID,
        session_id: UUID,
    ) -> MemorySession:
        return MemorySession(
            session_id=session_id,
            correlation_id=correlation_id,
            module=self,
            event_bus=self.event_bus,
        )
