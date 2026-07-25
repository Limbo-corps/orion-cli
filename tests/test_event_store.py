from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio

from orion.events.base import Event
from orion.events.registry import EventRegistry
from orion.store.sqlite_store import SQLiteEventStore


class DummyEvent(Event):
    value: int


EventRegistry.register(DummyEvent)


@pytest_asyncio.fixture
async def store(tmp_path):
    db_path = tmp_path / "test.db"

    store = SQLiteEventStore(str(db_path))
    await store.startup()

    try:
        yield store
    finally:
        await store.shutdown()


@pytest.mark.asyncio
async def test_startup_creates_database(tmp_path):
    db_path = tmp_path / "events.db"

    store = SQLiteEventStore(str(db_path))

    assert not store.is_running

    await store.startup()

    assert store.is_running
    assert db_path.exists()

    await store.shutdown()


@pytest.mark.asyncio
async def test_double_startup_raises(tmp_path):
    store = SQLiteEventStore(str(tmp_path / "events.db"))

    await store.startup()

    with pytest.raises(RuntimeError, match="already been started"):
        await store.startup()

    await store.shutdown()


@pytest.mark.asyncio
async def test_shutdown_is_idempotent(tmp_path):
    store = SQLiteEventStore(str(tmp_path / "events.db"))

    await store.startup()
    await store.shutdown()

    assert not store.is_running

    await store.shutdown()


@pytest.mark.asyncio
async def test_can_restart_after_shutdown(tmp_path):
    store = SQLiteEventStore(str(tmp_path / "events.db"))

    await store.startup()
    await store.shutdown()

    await store.startup()

    assert store.is_running

    await store.shutdown()


@pytest.mark.asyncio
async def test_append_and_load(store):
    event = DummyEvent(
        session_id=uuid4(),
        correlation_id=uuid4(),
        source="test",
        value=42,
    )

    await store.append(event)

    events = await store.load_all()

    assert len(events) == 1
    assert isinstance(events[0], DummyEvent)
    assert events[0] == event


@pytest.mark.asyncio
async def test_load_preserves_order(store):
    first = DummyEvent(
        session_id=uuid4(),
        correlation_id=uuid4(),
        source="test",
        value=1,
    )

    second = DummyEvent(
        session_id=uuid4(),
        correlation_id=uuid4(),
        source="test",
        value=2,
    )

    third = DummyEvent(
        session_id=uuid4(),
        correlation_id=uuid4(),
        source="test",
        value=3,
    )

    await store.append(first)
    await store.append(second)
    await store.append(third)

    events = await store.load_all()

    assert [e.value for e in events] == [1, 2, 3]


@pytest.mark.asyncio
async def test_append_before_startup_raises(tmp_path):
    store = SQLiteEventStore(str(tmp_path / "events.db"))

    event = DummyEvent(
        session_id=uuid4(),
        correlation_id=uuid4(),
        source="test",
        value=1,
    )

    with pytest.raises(RuntimeError, match="has not been started"):
        await store.append(event)


@pytest.mark.asyncio
async def test_load_before_startup_raises(tmp_path):
    store = SQLiteEventStore(str(tmp_path / "events.db"))

    with pytest.raises(RuntimeError, match="has not been started"):
        await store.load_all()


@pytest.mark.asyncio
async def test_database_persists_between_instances(tmp_path):
    db_path = tmp_path / "events.db"

    event = DummyEvent(
        session_id=uuid4(),
        correlation_id=uuid4(),
        source="test",
        value=99,
    )

    first = SQLiteEventStore(str(db_path))
    await first.startup()
    await first.append(event)
    await first.shutdown()

    second = SQLiteEventStore(str(db_path))
    await second.startup()

    events = await second.load_all()

    assert len(events) == 1
    assert events[0] == event

    await second.shutdown()
