from abc import ABC, abstractmethod

from orion.memory.models import Entity, Fact, Relationship


class KnowledgeGraph(ABC):
    """
    Abstract Knowledge Graph.

    Graph is reponsible only for storing and
    retrieving structured facts

    It never dedicates what should be remastered
    The LLM controls all graph mutations through tools
    """

    @abstractmethod
    async def startup(self) -> None:
        """
        Initialize the graph backend
        """
        raise NotImplementedError

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the graph backend
        """
        raise NotImplementedError

    @abstractmethod
    async def add_entity(self, entity: Entity) -> None:
        """
        Insert or Update an Entity
        """
        raise NotImplementedError

    @abstractmethod
    async def add_relationship(self, relationship: Relationship) -> None:
        """
        Insert or update a Relationship
        """
        raise NotImplementedError

    @abstractmethod
    async def add_fact(self, fact: Fact) -> None:
        """
        Convinience API for adding a fast triple
        """
        raise NotImplementedError

    @abstractmethod
    async def remove_fact(self, fact: Fact) -> None:
        """
        Remove a fact from the graph
        """
        raise NotImplementedError

    @abstractmethod
    async def query(self, query: str) -> list[Fact]:
        """
        Query the knowledge Graph
        """
        raise NotImplementedError

    @abstractmethod
    async def related_entities(
        self,
        entity: str,
        *,
        depth: int = 1,
    ) -> list[Entity]:
        """
        Retrieve entities related to the given entity.
        """
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        """
        Remove all graph data.
        """
        raise NotImplementedError

    @abstractmethod
    async def count(self) -> int:
        """
        Return the number of stored facts.
        """
        raise NotImplementedError
