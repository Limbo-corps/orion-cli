from abc import ABC, abstractmethod

from memory.models import SummaryMemory


class SummaryStore(ABC):
    """
    Abstract rolling summary state

    Responsible only for persisting and retrieving
    the continuous conversation memory

    It does NOT generate summaries
    """

    @abstractmethod
    async def startup(self) -> None:
        """
        Initialize the summary backend
        """
        raise NotImplementedError

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the summary backend.
        """
        raise NotImplementedError

    @abstractmethod
    async def load(self) -> SummaryMemory:
        """
        Load the lastest converasation summary.
        """
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        summary: SummaryMemory,
    ) -> None:
        """
        Persist the updated memory
        """
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        """
        Remove the current summary
        """
        raise NotImplementedError
