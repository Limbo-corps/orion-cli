# cli/commands/voice.py

import asyncio

from dotenv import load_dotenv

from bus.event_bus import EventBus
from store.sqlite_store import SQLiteEventStore

from orchestrator.orchestrator import Orchestrator
from tui.app import OrionApp


async def pipeline_loop(
    orchestrator: Orchestrator,
) -> None:
    """
    Continuous ORION runtime.

    Waits until Textual has mounted before
    starting pipelines.
    """

    while OrionApp.instance is None:
        await asyncio.sleep(0.05)

    while True:
        try:
            await orchestrator.start_pipeline()

        except asyncio.CancelledError:
            raise

        except Exception as e:
            print(f"Pipeline failed: {e}")

        await asyncio.sleep(0.25)


async def run() -> None:

    store = SQLiteEventStore()
    await store.initialize()

    bus = EventBus(store)

    orchestrator = Orchestrator(bus)

    await orchestrator.startup()

    app = OrionApp()

    pipeline_task = asyncio.create_task(
        pipeline_loop(
            orchestrator,
        )
    )

    try:
        await app.run_async()

    finally:
        pipeline_task.cancel()

        try:
            await pipeline_task

        except asyncio.CancelledError:
            pass

        await orchestrator.shutdown()
        await store.close()


def voice() -> None:
    load_dotenv()
    asyncio.run(run())
