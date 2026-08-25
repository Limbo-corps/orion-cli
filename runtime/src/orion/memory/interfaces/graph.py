from abc import ABC, abstractmethod

from orion.memory.models import Entity, Fact, GraphSchema


class KnowledgeGraph(ABC):
    """
    Abstract knowledge graph.

    Responsible only for storing and retrieving structured knowledge.

    Implementations may use Neo4j, an MCP server, an in-memory graph,
    or any other graph backend.
    """

    # ==========================================================
    # Lifecycle
    # ==========================================================

    @abstractmethod
    async def startup(self) -> None:
        """
        Initialize the graph backend.
        """
        raise NotImplementedError

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the graph backend.
        """
        raise NotImplementedError

    # ==========================================================
    # Storage
    # ==========================================================

    @abstractmethod
    async def add_fact(
        self,
        fact: Fact,
    ) -> None:
        """
        Store a single fact.
        """
        raise NotImplementedError

    @abstractmethod
    async def add_facts(
        self,
        facts: list[Fact],
    ) -> None:
        """
        Store multiple facts efficiently.
        """
        raise NotImplementedError

    @abstractmethod
    async def remove_fact(
        self,
        fact: Fact,
    ) -> None:
        """
        Remove a single fact.
        """
        raise NotImplementedError

    @abstractmethod
    async def remove_facts(
        self,
        facts: list[Fact],
    ) -> None:
        """
        Remove multiple facts.
        """
        raise NotImplementedError

    # ==========================================================
    # Retrieval
    # ==========================================================

    @abstractmethod
    async def search_facts(
        self,
        query: str,
    ) -> list[Fact]:
        """
        Search for facts relevant to a query or entity.
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
        Retrieve entities connected to the supplied entity.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_schema(self) -> GraphSchema:
        """
        Retrieve the graph schema.
        """
        raise NotImplementedError

    # ==========================================================
    # Maintenance
    # ==========================================================

    @abstractmethod
    async def clear(self) -> None:
        """
        Remove every stored entity and fact.
        """
        raise NotImplementedError

    @abstractmethod
    async def count(self) -> int:
        """
        Return the total number of stored facts.
        """
        raise NotImplementedError
