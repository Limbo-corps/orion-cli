import asyncio

from bus.event_bus import EventBus

from store.sqlite_store import SQLiteEventStore

from orchestrator.orchestrator import Orchestrator


async def main():
    print("1")

    store = SQLiteEventStore()
    await store.initialize()

    print("2")

    bus = EventBus(store)

    print("3")

    orchestrator = Orchestrator(bus)

    print("4")

    await orchestrator.startup()

    print("5")

    await orchestrator.start_pipeline()

    print("6")

    import threading

    print("\nTHREADS:")

    for thread in threading.enumerate():
        print(
            f"name={thread.name}",
            f"daemon={thread.daemon}",
            f"alive={thread.is_alive()}",
        )

    await store.close()


if __name__ == "__main__":
    asyncio.run(main())