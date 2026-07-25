from __future__ import annotations

from abc import ABC, abstractmethod

from orion.events.base import Event
from orion.runtime.lifecycle import Lifecycle


class EventStore(Lifecycle, ABC):
    """
    Base interface for event stores.

    An event store is responsible for persisting and replaying events.
    """

    @abstractmethod
    async def append(self, event: Event) -> None:
        """
        Persist an event.
        """
        raise NotImplementedError

    @abstractmethod
    async def load_all(self) -> list[Event]:
        """
        Load all persisted events in chronological order.
        """
        raise NotImplementedError
