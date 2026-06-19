import asyncio

from bus.event_bus import EventBus

from store.sqlite_store import SQLiteEventStore

from orchestrator.orchestrator import Orchestrator


async def main():
    store = SQLiteEventStore()
    await store.initialize()

    bus = EventBus(store)

    orchestrator = Orchestrator(bus)

    await orchestrator.startup()
    await orchestrator.start_pipeline()


if __name__ == "__main__":
    asyncio.run(main())