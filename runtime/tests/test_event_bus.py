import pytest
from uuid import uuid4

from orion.bus.event_bus import EventBus
from orion.events.base import Event
from orion.events.events import TranscriptGeneratedEvent
from orion.store.base import EventStore


class FakeStore(EventStore):
    def __init__(self) -> None:
        self.events: list[Event] = []

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def append(self, event: Event) -> None:
        self.events.append(event)

    async def load_all(self) -> list[Event]:
        return list(self.events)


@pytest.mark.asyncio
async def test_event_bus_publishes_to_handlers_and_persists() -> None:
    store = FakeStore()
    await store.startup()

    bus = EventBus(store)
    received: list[str] = []

    async def handler(event: Event) -> None:
        assert isinstance(event, TranscriptGeneratedEvent)
        received.append(event.text)

    bus.subscribe(TranscriptGeneratedEvent, handler)

    event = TranscriptGeneratedEvent(
        session_id=uuid4(),
        correlation_id=uuid4(),
        source="stt",
        text="Hello ORION",
    )

    await bus.publish(event)

    assert received == ["Hello ORION"]
    assert store.events == [event]

    await store.shutdown()
