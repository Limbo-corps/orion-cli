from uuid import uuid4

import events  # noqa: F401 - import registers event types
from events import TranscriptGeneratedEvent, ResponseGeneratedEvent
from events.registry import EventRegistry


def test_event_registry_contains_core_event_types():
    assert EventRegistry.get("TranscriptGeneratedEvent") is TranscriptGeneratedEvent
    assert EventRegistry.get("ResponseGeneratedEvent") is ResponseGeneratedEvent


def test_registered_events_can_round_trip_through_pydantic_models():
    event = TranscriptGeneratedEvent(
        correlation_id=uuid4(),
        source="stt",
        text="Hello ORION",
    )

    payload = event.model_dump(mode="json")
    restored = EventRegistry.get(event.__class__.__name__).model_validate(payload)

    assert restored == event
