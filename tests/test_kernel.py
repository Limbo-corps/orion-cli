from uuid import uuid4

from bus.event_bus import EventBus
from events.speech import TranscriptGenerated
from store.sqlite_store import SQLiteEventStore


async def transcript_handler(
    event: TranscriptGenerated,
) -> None:
    print(f"[HANDLER] {event.text}")


async def main() -> None:
    store = SQLiteEventStore("test.db")

    await store.initialize()

    bus = EventBus(store)

    bus.subscribe(
        TranscriptGenerated,
        transcript_handler,
    )

    event = TranscriptGenerated(
        correlation_id=uuid4(),
        source="stt",
        text="Hello ORION",
    )

    await bus.publish(event)

    events = await store.load_all()

    print(f"Stored Events: {len(events)}")

    await store.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
