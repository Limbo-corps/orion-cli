from abc import ABC, abstractmethod
from events.base import Event


class EventStore(ABC):
    @abstractmethod
    async def initialize(self) -> None:
        pass

    @abstractmethod
    async def append(self, event: Event) -> None:
        pass

    @abstractmethod
    async def load_all(self) -> list[Event]:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass
