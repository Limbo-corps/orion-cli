import asyncio
from collections import defaultdict
from typing import Awaitable, Callable

from orion.core.singleton import SingletonMeta
from orion.events.base import Event
from orion.store.base import EventStore


EventHandler = Callable[[Event], Awaitable[None]]


class EventBus(metaclass=SingletonMeta):
    def __init__(self, store: EventStore | None = None):
        if hasattr(self, "_initialized"):
            return

        if store is None:
            raise RuntimeError("Event Bus must be initialized before use")
        self.store = store

        self.subscribers: dict[type[Event], list[EventHandler]] = defaultdict(list)

        self.global_subscribers: list[EventHandler] = []

        self._initialized = True

    def subscribe(
        self,
        event_type: type[Event],
        handler: EventHandler,
    ) -> None:
        self.subscribers[event_type].append(handler)

    def subscribe_all(
        self,
        handler: EventHandler,
    ) -> None:
        self.global_subscribers.append(handler)

    async def publish(
        self,
        event: Event,
    ) -> None:
        await self.store.append(event)

        handlers = self.subscribers.get(type(event), [])

        all_handlers = [
            *handlers,
            *self.global_subscribers,
        ]

        if all_handlers:
            await asyncio.gather(*(handler(event) for handler in all_handlers))
