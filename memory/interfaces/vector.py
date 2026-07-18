from abc import ABC, abstractmethod
from uuid import UUID

from memory.models import ConversationEpisode


class VectorMemory(ABC):
    """
    Abstract semantic memory

    Implementation are responsible for storing
    embedded conversation episodes and retrieving
    semantically similar memories
    """

    @abstractmethod
    async def startup(self) -> None:
        """
        Initialize the vector store.
        """
        raise NotImplementedError

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the vector store.
        """
        raise NotImplementedError

    @abstractmethod
    async def store(self, episode: ConversationEpisode) -> None:
        """
        Store a Conversation episode

        Implemetations are reponsible for
        generating embeddings and indexing them
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, episode_id: UUID) -> None:
        """
        Deletes all the memories from a Episode
        """
        raise NotImplementedError

    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        limit: int = 5,
        min_score: float = 0.0,
    ) -> list[ConversationEpisode]:
        """
        Retrieve the most semantically similar conversation episodes.
        """
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        """
        Remove every stored memory
        """
        raise NotImplementedError

    @abstractmethod
    async def count(self) -> int:
        """
        Return the number of stored memories
        """
        raise NotImplementedError

    @abstractmethod
    async def recent(
        self,
        *,
        limit: int = 5,
    ) -> list[ConversationEpisode]:
        """
        Retrieve the most recent conversation episodes.
        """
        raise NotImplementedError
