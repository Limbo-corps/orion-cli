from __future__ import annotations

import asyncio
import json
from pathlib import Path
from uuid import uuid4

import pytest

from orion.bus.event_bus import EventBus
from orion.events.events import PipelineStartEvent
from orion.events.speech import TranscriptGenerated
from orion.services.logging import LoggingService
from orion.store.sqlite_store import SQLiteEventStore


@pytest.mark.asyncio
async def test_logging_service_persists_events(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_file = log_dir / "orion.log"
    db_file = tmp_path / "orion.db"

    store = SQLiteEventStore(str(db_file))
    await store.startup()

    bus = EventBus(store)

    logging_service = LoggingService(
        log_dir=log_dir,
        log_file=log_file,
    )

    bus.subscribe_all(logging_service.handle)

    await logging_service.startup()

    correlation_id = uuid4()

    try:
        await bus.publish(
            PipelineStartEvent(
                session_id=uuid4(),
                correlation_id=correlation_id,
                source="test_runner",
                message="Logging test pipeline start",
            )
        )

        await bus.publish(
            TranscriptGenerated(
                session_id=uuid4(),
                correlation_id=correlation_id,
                source="stt_test",
                text="Hello Orion, verifying disk logging system.",
            )
        )

        # Give the logger a moment to flush.
        await asyncio.sleep(0.5)

        assert log_file.exists()

        records = [
            json.loads(line)
            for line in log_file.read_text(encoding="utf-8").splitlines()
        ]

        # Ignore lifecycle messages emitted by LoggingService itself.
        events = [record for record in records if "event_type" in record]

        assert len(events) == 2

        pipeline, transcript = events

        # ------------------------------------------------------------------
        # PipelineStartEvent
        # ------------------------------------------------------------------

        assert pipeline["event_type"] == "PipelineStartEvent"
        assert pipeline["correlation_id"] == str(correlation_id)
        assert pipeline["source"] == "test_runner"
        assert pipeline["message"] == "Logging test pipeline start"

        assert "timestamp" in pipeline
        assert "event_id" in pipeline
        assert "status" in pipeline

        # All common metadata should be extracted from the payload.
        assert pipeline["payload"]["session_id"]
        assert "correlation_id" not in pipeline["payload"]
        assert "source" not in pipeline["payload"]
        assert "message" not in pipeline["payload"]
        assert "status" not in pipeline["payload"]
        assert "timestamp" not in pipeline["payload"]
        assert "event_id" not in pipeline["payload"]

        # ------------------------------------------------------------------
        # TranscriptGenerated
        # ------------------------------------------------------------------

        assert transcript["event_type"] == "TranscriptGenerated"
        assert transcript["correlation_id"] == str(correlation_id)
        assert transcript["source"] == "stt_test"

        assert "timestamp" in transcript
        assert "event_id" in transcript
        assert "status" in transcript

        assert transcript["payload"]["text"] == (
            "Hello Orion, verifying disk logging system."
        )
        assert transcript["payload"]["session_id"]
        assert "correlation_id" not in transcript["payload"]
        assert "source" not in transcript["payload"]
        assert "status" not in transcript["payload"]
        assert "timestamp" not in transcript["payload"]
        assert "event_id" not in transcript["payload"]

    finally:
        await logging_service.shutdown()
        await store.shutdown()