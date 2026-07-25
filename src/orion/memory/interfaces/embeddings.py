from __future__ import annotations
from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """
    Base interface for embedding Provider
    """

    @abstractmethod
    async def startup(self) -> None:
        """
        call this function for startup
        """
        raise NotImplementedError

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the EmbeddingProvider
        """
        raise NotImplementedError

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """
        Generate an embedding for single piece of text
        """
        raise NotImplementedError

    @abstractmethod
    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts
        """

        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Dimension of the vector embeddings
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Name of the underlying embedding model
        """

        raise NotImplementedError
