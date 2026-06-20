import asyncio
from uuid import uuid4

from events.speech import TranscriptGenerated
from store.sqlite_store import SQLiteEventStore


async def main() -> None:
    store = SQLiteEventStore("test.db")

    await store.initialize()

    event = TranscriptGenerated(
        correlation_id=uuid4(),
        source="stt",
        text="Hello ORION",
    )

    await store.append(event)

    events = await store.load_all()

    for event in events:
        print(event)


if __name__ == "__main__":
    asyncio.run(main())
