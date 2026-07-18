from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class MemoryType(str, Enum):
    VECTOR = "vector"
    GRAPH = "graph"
    SUMMARY = "summary"


@dataclass(slots=True)
class ConversationEpisode:
    id: UUID = field(default_factory=uuid4)

    correlation_id: UUID | None = None

    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    user_message: str = ""

    assistant_message: str = ""

    summary: str = ""

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RetrievedEpisode:
    episode: ConversationEpisode
    score: float


@dataclass(slots=True)
class MemoryChunk:
    """
    A semantic chunk stored in vector memory
    """

    id: UUID = field(default_factory=uuid4)

    episode_id: UUID | None = None

    text: str = ""

    embedding: list[float] = field(
        default_factory=list,
    )

    importance: float = 0.5

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class Entity:
    """
    A node in the knowledge graph
    """

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    label: str = "Entity"


@dataclass(slots=True)
class Relationship:
    """
    The Relationship Between two entites
    """

    source: UUID | None = None

    predicate: str = ""

    target: UUID | None = None

    confidence: float = 1.0

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class Fact:
    """
    Human-readable graph triple
    """

    subject: str
    predicate: str
    object: str
    confidence: float = 1.0


@dataclass(slots=True)
class SummaryMemory:
    """
    Rolling summary maintained across conversation
    """

    version: int = 1
    summary: str = ""

    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class MemoryBundle:
    """
    Return to the agent before reasoning
    """

    summary: SummaryMemory

    semantic: list[MemoryChunk] = field(default_factory=list)

    facts: list[Fact] = field(default_factory=list)


@dataclass(slots=True)
class MemoryContext:
    """
    Complete context for indexing

    Created once a conversation turn finishes
    """

    correlation_id: UUID

    episode: ConversationEpisode

    mode: str = "chat"

    tags: list[str] = field(default_factory=list)

@dataclass(slots=True)
class RetrievedContext:
    """
    Context retrieved for the current query before the agent reasons.
    """

    summary: SummaryMemory | None = None
    # semantic memories
    episodes: list[ConversationEpisode] = field(default_factory=list)
    # graph
    facts: list[Fact] = field(default_factory=list)
    # recent chat history
    recent_messages: list[ConversationEpisode] = field(default_factory=list)
