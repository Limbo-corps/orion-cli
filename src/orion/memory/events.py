from uuid import UUID

from orion.events.base import Event, EventStatus

# ------------------------------------------------------------------
# Lifecycle
# ------------------------------------------------------------------


class MemoryStartupEvent(Event):
    status: EventStatus = EventStatus.SUCCESS


class MemoryShutdownEvent(Event):
    status: EventStatus = EventStatus.SUCCESS


# ------------------------------------------------------------------
# Store
# ------------------------------------------------------------------


class MemoryStoreStartedEvent(Event):
    status: EventStatus = EventStatus.INFO
    episode_id: UUID | None


class MemoryStoreCompletedEvent(Event):
    status: EventStatus = EventStatus.SUCCESS
    episode_id: UUID


class MemoryStoreFailedEvent(Event):
    status: EventStatus = EventStatus.ERROR
    episode_id: UUID
    error: str


# ------------------------------------------------------------------
# Recall
# ------------------------------------------------------------------


class MemoryRecallStartedEvent(Event):
    status: EventStatus = EventStatus.INFO
    query: str


class MemoryRecallCompletedEvent(Event):
    status: EventStatus = EventStatus.SUCCESS
    query: str
    summary_loaded: bool
    semantic_count: int
    recent_count: int
    fact_count: int


class MemoryRecallFailedEvent(Event):
    status: EventStatus = EventStatus.ERROR
    query: str
    error: str


# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------


class SummaryFetchedEvent(Event):
    status: EventStatus = EventStatus.SUCCESS
    version: int
    has_summary: bool


class SummaryUpdatedEvent(Event):
    status: EventStatus = EventStatus.SUCCESS
    version: int


# ------------------------------------------------------------------
# Vector Memory
# ------------------------------------------------------------------


class SemanticSearchStartedEvent(Event):
    status: EventStatus = EventStatus.INFO
    query: str
    limit: int


class SemanticSearchCompletedEvent(Event):
    status: EventStatus = EventStatus.SUCCESS
    query: str
    result_count: int


# ------------------------------------------------------------------
# Knowledge Graph
# ------------------------------------------------------------------


class GraphQueryStartedEvent(Event):
    status: EventStatus = EventStatus.INFO
    query: str


class GraphQueryCompletedEvent(Event):
    status: EventStatus = EventStatus.SUCCESS
    query: str
    fact_count: int


class GraphFactFetchedEvent(Event):
    status: EventStatus = EventStatus.SUCCESS
    subject: str
    predicate: str
    object: str


class GraphFactAddedEvent(Event):
    status: EventStatus = EventStatus.SUCCESS
    subject: str
    predicate: str
    object: str


class GraphFactRemovedEvent(Event):
    status: EventStatus = EventStatus.SUCCESS
    subject: str
    predicate: str
    object: str
