from __future__ import annotations

import json

import aiosqlite

from orion.events.base import Event
from orion.events.registry import EventRegistry
from orion.runtime.lifecycle import Lifecycle
from orion.store.base import EventStore


class SQLiteEventStore(EventStore):
    def __init__(self, db_path: str = "orion.db") -> None:
        self.db_path = db_path
        self.db: aiosqlite.Connection | None = None

    @property
    def is_running(self) -> bool:
        return self.db is not None

    async def startup(self) -> None:
        if self.db is not None:
            raise RuntimeError("SQLiteEventStore has already been started.")

        self.db = await aiosqlite.connect(self.db_path)

        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                correlation_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )

        await self.db.commit()

    async def append(self, event: Event) -> None:
        if self.db is None:
            raise RuntimeError("SQLiteEventStore has not been started.")

        await self.db.execute(
            """
            INSERT INTO events (
                event_id,
                correlation_id,
                event_type,
                timestamp,
                source,
                payload
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(event.event_id),
                str(event.correlation_id),
                event.__class__.__name__,
                event.timestamp.isoformat(),
                event.source,
                json.dumps(event.model_dump(mode="json")),
            ),
        )

        await self.db.commit()

    async def load_all(self) -> list[Event]:
        if self.db is None:
            raise RuntimeError("SQLiteEventStore has not been started.")

        cursor = await self.db.execute(
            """
            SELECT event_type, payload
            FROM events
            ORDER BY timestamp ASC
            """
        )

        try:
            rows = await cursor.fetchall()
        finally:
            await cursor.close()

        events: list[Event] = []

        for event_type, payload_json in rows:
            payload = json.loads(payload_json)

            event_cls = EventRegistry.get(event_type)
            events.append(event_cls.model_validate(payload))

        return events

    async def shutdown(self) -> None:
        if self.db is None:
            return

        try:
            await self.db.close()
        finally:
            self.db = None
