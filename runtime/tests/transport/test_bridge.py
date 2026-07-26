from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from orion.events.base import Event
from orion.events.events import ChatPipelineStartEvent
from orion.transport.bridge import IPCBridge
from orion.transport.messages import (
    Envelope,
    MessageType,
    SubmitPromptPayload,
)


class FakeEventBus:
    """Simple EventBus implementation for bridge tests."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    async def publish(self, event: Event) -> None:
        self.events.append(event)


class FakeSession:
    """Fake client session used by bridge tests."""

    def __init__(self) -> None:
        self.id: UUID = uuid4()
        self.sent: list[Envelope] = []

    async def send(self, message: Envelope) -> None:
        self.sent.append(message)


@pytest.mark.asyncio
async def test_submit_prompt_publishes_chat_pipeline_event() -> None:
    bus = FakeEventBus()
    bridge = IPCBridge(bus)
    session = FakeSession()

    payload = SubmitPromptPayload(
        text="Hello Orion",
    )

    message = Envelope(
        correlation_id=uuid4(),
        type=MessageType.SUBMIT_PROMPT,
        payload=payload.model_dump(),
    )

    await bridge.handle(session, message)

    assert len(bus.events) == 1

    event = bus.events[0]

    assert isinstance(event, ChatPipelineStartEvent)
    assert event.text == "Hello Orion"
    assert event.session_id == session.id
    assert event.correlation_id == message.correlation_id
    assert event.source == "ipc"


@pytest.mark.asyncio
async def test_submit_prompt_preserves_correlation_id() -> None:
    bus = FakeEventBus()
    bridge = IPCBridge(bus)
    session = FakeSession()

    correlation_id = uuid4()

    message = Envelope(
        correlation_id=correlation_id,
        type=MessageType.SUBMIT_PROMPT,
        payload={
            "text": "Testing correlation id",
        },
    )

    await bridge.handle(session, message)

    event = bus.events[0]

    assert isinstance(event, ChatPipelineStartEvent)
    assert event.correlation_id == correlation_id


@pytest.mark.asyncio
async def test_submit_prompt_preserves_session_id() -> None:
    bus = FakeEventBus()
    bridge = IPCBridge(bus)
    session = FakeSession()

    message = Envelope(
        type=MessageType.SUBMIT_PROMPT,
        payload={
            "text": "Hello",
        },
    )

    await bridge.handle(session, message)

    event = bus.events[0]

    assert isinstance(event, ChatPipelineStartEvent)
    assert event.session_id == session.id


@pytest.mark.asyncio
async def test_invalid_submit_prompt_payload_raises_validation_error() -> None:
    bus = FakeEventBus()
    bridge = IPCBridge(bus)
    session = FakeSession()

    message = Envelope(
        type=MessageType.SUBMIT_PROMPT,
        payload={},
    )

    with pytest.raises(ValidationError):
        await bridge.handle(session, message)


@pytest.mark.asyncio
async def test_invalid_message_type_is_rejected_by_envelope() -> None:
    """
    Invalid message types are rejected by the Envelope model before they
    reach the bridge.
    """

    with pytest.raises(ValidationError):
        Envelope(
            type="invalid",  # type: ignore[arg-type]
            payload={},
        )


@pytest.mark.asyncio
async def test_ping_with_pong() -> None:
    bus = FakeEventBus()
    bridge = IPCBridge(bus)
    session = FakeSession()

    message = Envelope(
        type=MessageType.PING,
        payload={},
    )

    await bridge.handle(session, message)

    assert bus.events == []
    assert len(session.sent) == 1
    assert session.sent[0].type == MessageType.PONG


@pytest.mark.asyncio
async def test_voice_start_not_implemented() -> None:
    bus = FakeEventBus()
    bridge = IPCBridge(bus)
    session = FakeSession()

    message = Envelope(
        type=MessageType.VOICE_START,
        payload={},
    )

    await bridge.handle(session, message)

    assert bus.events == []


@pytest.mark.asyncio
async def test_voice_chunk_not_implemented() -> None:
    bus = FakeEventBus()
    bridge = IPCBridge(bus)
    session = FakeSession()

    message = Envelope(
        type=MessageType.VOICE_CHUNK,
        payload={},
    )

    await bridge.handle(session, message)

    assert bus.events == []


@pytest.mark.asyncio
async def test_voice_end_not_implemented() -> None:
    bus = FakeEventBus()
    bridge = IPCBridge(bus)
    session = FakeSession()

    message = Envelope(
        type=MessageType.VOICE_END,
        payload={},
    )

    await bridge.handle(session, message)

    assert bus.events == []


# ============================================================================
# Outgoing event tests
# ============================================================================
#
# ResponseStartedEvent   -> ASSISTANT_START
# ResponseChunkEvent     -> ASSISTANT_CHUNK
# ResponseCompletedEvent -> ASSISTANT_END
# PipelineFailedEvent    -> ERROR
#
