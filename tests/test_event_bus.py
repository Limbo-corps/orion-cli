import asyncio
from uuid import uuid4

import events  # noqa: F401 - import registers event types
from bus.event_bus import EventBus
from events import TranscriptGeneratedEvent


class FakeStore:
    def __init__(self) -> None:
        self.events = []

    async def append(self, event) -> None:
        self.events.append(event)


def test_event_bus_publishes_to_handlers_and_persists():
    async def scenario():
        store = FakeStore()
        bus = EventBus(store)
        received: list[str] = []

        async def handler(event: TranscriptGeneratedEvent) -> None:
            received.append(event.text)

        bus.subscribe(TranscriptGeneratedEvent, handler)

        event = TranscriptGeneratedEvent(
            correlation_id=uuid4(),
            source="stt",
            text="Hello ORION",
        )

        await bus.publish(event)

        assert received == ["Hello ORION"]
        assert store.events == [event]

    asyncio.run(scenario())
