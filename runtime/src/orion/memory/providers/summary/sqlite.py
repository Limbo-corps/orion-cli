from __future__ import annotations

from datetime import datetime

import aiosqlite

from orion.memory.interfaces.summary import SummaryStore
from orion.memory.models import SummaryMemory


class SQLiteSummaryStore(SummaryStore):
    """
    SQLite implementation of the rolling summary store.

    Stores exactly one continuously evolving summary.
    """

    def __init__(
        self,
        database: str = "orion.db",
    ) -> None:
        self.database = database

    async def startup(self) -> None:
        async with aiosqlite.connect(self.database) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS summary (
                    id INTEGER PRIMARY KEY CHECK(id = 1),
                    version INTEGER NOT NULL,
                    summary TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            await db.commit()

    async def shutdown(self) -> None:
        pass

    async def load(self) -> SummaryMemory:
        async with aiosqlite.connect(self.database) as db:
            cursor = await db.execute(
                """
                SELECT
                    version,
                    summary,
                    updated_at
                FROM summary
                WHERE id = 1
                """
            )

            row = await cursor.fetchone()

            if row is None:
                return SummaryMemory()

            return SummaryMemory(
                version=row[0],
                summary=row[1],
                updated_at=datetime.fromisoformat(row[2]),
            )

    async def save(
        self,
        summary: SummaryMemory,
    ) -> None:
        async with aiosqlite.connect(self.database) as db:
            await db.execute(
                """
                INSERT INTO summary (
                    id,
                    version,
                    summary,
                    updated_at
                )
                VALUES (1, ?, ?, ?)
                ON CONFLICT(id)
                DO UPDATE SET
                    version = excluded.version,
                    summary = excluded.summary,
                    updated_at = excluded.updated_at
                """,
                (
                    summary.version,
                    summary.summary,
                    summary.updated_at.isoformat(),
                ),
            )

            await db.commit()

    async def clear(self) -> None:
        async with aiosqlite.connect(self.database) as db:
            await db.execute(
                """
                DELETE FROM summary
                """
            )
            await db.commit()
