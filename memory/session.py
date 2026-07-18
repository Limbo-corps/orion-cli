from __future__ import annotations

import asyncio
from uuid import UUID

from bus.event_bus import EventBus
from memory.events import (
    GraphFactAddedEvent,
    GraphFactFetchedEvent,
    GraphFactRemovedEvent,
    GraphQueryCompletedEvent,
    GraphQueryStartedEvent,
    MemoryRecallCompletedEvent,
    MemoryRecallFailedEvent,
    MemoryRecallStartedEvent,
    MemoryStoreCompletedEvent,
    MemoryStoreFailedEvent,
    MemoryStoreStartedEvent,
    SemanticSearchCompletedEvent,
    SemanticSearchStartedEvent,
    SummaryFetchedEvent,
    SummaryUpdatedEvent,
)
from memory.models import (
    ConversationEpisode,
    Fact,
    RetrievedContext,
    SummaryMemory,
)


class MemorySession:
    """
    Memory API bound to a single pipeline execution.
    """

    SOURCE = "memory_module"

    def __init__(
        self,
        *,
        correlation_id: UUID,
        module,
        event_bus: EventBus,
    ) -> None:
        self.correlation_id = correlation_id
        self.module = module
        self.event_bus = event_bus

    # ------------------------------------------------------------------
    # Conversation Memory
    # ------------------------------------------------------------------

    async def remember(
        self,
        episode: ConversationEpisode,
    ) -> None:
        await self.event_bus.publish(
            MemoryStoreStartedEvent(
                correlation_id=self.correlation_id,
                source=self.SOURCE,
                episode_id=episode.id,
            )
        )

        try:
            await self.module.vector.store(episode)

            await self.event_bus.publish(
                MemoryStoreCompletedEvent(
                    correlation_id=self.correlation_id,
                    source=self.SOURCE,
                    episode_id=episode.id,
                    message="Conversation stored.",
                )
            )

        except Exception as exc:
            await self.event_bus.publish(
                MemoryStoreFailedEvent(
                    correlation_id=self.correlation_id,
                    source=self.SOURCE,
                    episode_id=episode.id,
                    error=str(exc),
                    message="Failed to store conversation.",
                )
            )
            raise

    async def search_conversation_memory(
        self,
        query: str,
        *,
        limit: int = 5,
    ):
        await self.event_bus.publish(
            SemanticSearchStartedEvent(
                correlation_id=self.correlation_id,
                source=self.SOURCE,
                query=query,
                limit=limit,
            )
        )

        memories = await self.module.vector.search(
            query=query,
            limit=limit,
        )

        await self.event_bus.publish(
            SemanticSearchCompletedEvent(
                correlation_id=self.correlation_id,
                source=self.SOURCE,
                query=query,
                result_count=len(memories),
            )
        )

        return memories

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    async def get_summary(self) -> SummaryMemory:
        summary = await self.module.summary.load()

        await self.event_bus.publish(
            SummaryFetchedEvent(
                correlation_id=self.correlation_id,
                source=self.SOURCE,
                version=summary.version,
                has_summary=bool(summary.summary.strip()),
                message="Summary loaded.",
            )
        )

        return summary

    async def update_summary(
        self,
        summary: SummaryMemory,
    ) -> None:
        await self.module.summary.save(summary)

        await self.event_bus.publish(
            SummaryUpdatedEvent(
                correlation_id=self.correlation_id,
                source=self.SOURCE,
                version=summary.version,
                message="Summary updated.",
            )
        )

    # ------------------------------------------------------------------
    # Knowledge Graph
    # ------------------------------------------------------------------

    async def search_facts(
        self,
        query: str,
    ) -> list[Fact]:

        await self.event_bus.publish(
            GraphQueryStartedEvent(
                correlation_id=self.correlation_id,
                source=self.SOURCE,
                query=query,
            )
        )

        facts = await self.module.graph.query(query)

        await self.event_bus.publish(
            GraphQueryCompletedEvent(
                correlation_id=self.correlation_id,
                source=self.SOURCE,
                query=query,
                fact_count=len(facts),
                message="Graph query completed.",
            )
        )

        for fact in facts:
            await self.event_bus.publish(
                GraphFactFetchedEvent(
                    correlation_id=self.correlation_id,
                    source=self.SOURCE,
                    subject=fact.subject,
                    predicate=fact.predicate,
                    object=fact.object,
                    message="Graph fact fetched.",
                )
            )

        return facts

    async def remember_fact(
        self,
        fact: Fact,
    ) -> None:

        await self.module.graph.add_fact(fact)

        await self.event_bus.publish(
            GraphFactAddedEvent(
                correlation_id=self.correlation_id,
                source=self.SOURCE,
                subject=fact.subject,
                predicate=fact.predicate,
                object=fact.object,
                message="Fact added.",
            )
        )

    async def forget_fact(
        self,
        fact: Fact,
    ) -> None:

        await self.module.graph.remove_fact(fact)

        await self.event_bus.publish(
            GraphFactRemovedEvent(
                correlation_id=self.correlation_id,
                source=self.SOURCE,
                subject=fact.subject,
                predicate=fact.predicate,
                object=fact.object,
                message="Fact removed.",
            )
        )

    # ------------------------------------------------------------------
    # Combined Retrieval
    # ------------------------------------------------------------------
    async def retrieve(
        self,
        query: str,
        *,
        semantic_limit: int = 5,
        history_limit: int = 10,
    ) -> RetrievedContext:
        await self.event_bus.publish(
            MemoryRecallStartedEvent(
                correlation_id=self.correlation_id,
                source=self.SOURCE,
                query=query,
                message="Memory retrieval started.",
            )
        )

        try:
            (
                summary,
                facts,
                semantic_memories,
                recent_messages,
            ) = await asyncio.gather(
                self.get_summary(),
                self.search_facts(query),
                self.search_conversation_memory(
                    query=query,
                    limit=semantic_limit,
                ),
                self.module.vector.recent(
                    limit=history_limit,
                ),
            )

            context = RetrievedContext(
                summary=summary,
                facts=facts,
                episodes=semantic_memories,
                recent_messages=recent_messages,
            )

            await self.event_bus.publish(
                MemoryRecallCompletedEvent(
                    correlation_id=self.correlation_id,
                    source=self.SOURCE,
                    query=query,
                    summary_loaded=bool(summary.summary.strip()),
                    semantic_count=len(semantic_memories),
                    fact_count=len(facts),
                    recent_count=len(recent_messages),
                    message="Memory retrieval completed.",
                )
            )

            return context

        except Exception as exc:
            await self.event_bus.publish(
                MemoryRecallFailedEvent(
                    correlation_id=self.correlation_id,
                    source=self.SOURCE,
                    query=query,
                    error=str(exc),
                    message="Memory retrieval failed.",
                )
            )
            raise
