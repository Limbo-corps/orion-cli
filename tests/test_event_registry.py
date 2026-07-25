from uuid import uuid4

import orion.events  # noqa: F401 - Registers event types.
from orion.events.events import (
    ChatPipelineStartEvent,
    ResponseChunkEvent,
    ResponseCompletedEvent,
    ResponseStartedEvent,
    TranscriptGeneratedEvent,
)
from orion.events.registry import EventRegistry


def test_event_registry_contains_core_event_types() -> None:
    assert (
        EventRegistry.get("TranscriptGeneratedEvent")
        is TranscriptGeneratedEvent
    )
    assert (
        EventRegistry.get("ChatPipelineStartEvent")
        is ChatPipelineStartEvent
    )
    assert (
        EventRegistry.get("ResponseStartedEvent")
        is ResponseStartedEvent
    )
    assert (
        EventRegistry.get("ResponseChunkEvent")
        is ResponseChunkEvent
    )
    assert (
        EventRegistry.get("ResponseCompletedEvent")
        is ResponseCompletedEvent
    )


def test_registered_events_can_round_trip_through_pydantic_models() -> None:
    event = TranscriptGeneratedEvent(
        session_id=uuid4(),
        correlation_id=uuid4(),
        source="stt",
        text="Hello ORION",
    )

    payload = event.model_dump(mode="json")

    restored = EventRegistry.get(
        event.__class__.__name__
    ).model_validate(payload)

    assert restored == event


def test_chat_pipeline_start_event_round_trip() -> None:
    event = ChatPipelineStartEvent(
        session_id=uuid4(),
        correlation_id=uuid4(),
        source="ipc",
        text="Hello Orion",
    )

    payload = event.model_dump(mode="json")

    restored = EventRegistry.get(
        event.__class__.__name__
    ).model_validate(payload)

    assert restored == event


def test_response_started_event_round_trip() -> None:
    event = ResponseStartedEvent(
        session_id=uuid4(),
        correlation_id=uuid4(),
        source="agent",
    )

    payload = event.model_dump(mode="json")

    restored = EventRegistry.get(
        event.__class__.__name__
    ).model_validate(payload)

    assert restored == event


def test_response_chunk_event_round_trip() -> None:
    event = ResponseChunkEvent(
        session_id=uuid4(),
        correlation_id=uuid4(),
        source="agent",
        text="Hello",
    )

    payload = event.model_dump(mode="json")

    restored = EventRegistry.get(
        event.__class__.__name__
    ).model_validate(payload)

    assert restored == event


def test_response_completed_event_round_trip() -> None:
    event = ResponseCompletedEvent(
        session_id=uuid4(),
        correlation_id=uuid4(),
        source="agent",
    )

    payload = event.model_dump(mode="json")

    restored = EventRegistry.get(
        event.__class__.__name__
    ).model_validate(payload)

    assert restored == event
