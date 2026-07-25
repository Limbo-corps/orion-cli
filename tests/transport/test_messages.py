from __future__ import annotations

from uuid import uuid4


from orion.transport.messages import (
    AssistantChunkPayload,
    CancelRequestPayload,
    ErrorPayload,
    PingPayload,
    PongPayload,
    StatusPayload,
    SubmitPromptPayload,
    ToolFinishedPayload,
    ToolStartedPayload,
    VoiceChunkPayload,
    VoiceEndPayload,
    VoiceStartPayload,
)


def test_submit_prompt_payload() -> None:
    payload = SubmitPromptPayload(text="Hello")

    assert payload.text == "Hello"


def test_cancel_request_payload() -> None:
    request_id = uuid4()

    payload = CancelRequestPayload(
        request_id=request_id,
    )

    assert payload.request_id == request_id


def test_voice_start_payload() -> None:
    payload = VoiceStartPayload(
        sample_rate=16000,
        channels=1,
    )

    assert payload.sample_rate == 16000
    assert payload.channels == 1
    assert payload.encoding == "pcm16"


def test_voice_chunk_payload() -> None:
    payload = VoiceChunkPayload(
        sequence=5,
        data=b"audio",
    )

    assert payload.sequence == 5
    assert payload.data == b"audio"


def test_voice_end_payload() -> None:
    payload = VoiceEndPayload()

    assert payload.model_dump() == {}


def test_assistant_chunk_payload() -> None:
    payload = AssistantChunkPayload(text="Hello!")

    assert payload.text == "Hello!"


def test_tool_started_payload() -> None:
    payload = ToolStartedPayload(
        name="calculator",
    )

    assert payload.name == "calculator"


def test_tool_finished_payload() -> None:
    payload = ToolFinishedPayload(
        name="calculator",
        success=True,
    )

    assert payload.name == "calculator"
    assert payload.success is True


def test_status_payload() -> None:
    payload = StatusPayload(
        message="Running",
    )

    assert payload.message == "Running"


def test_error_payload() -> None:
    payload = ErrorPayload(
        code="internal_error",
        message="Something failed.",
    )

    assert payload.code == "internal_error"
    assert payload.message == "Something failed."


def test_ping_payload() -> None:
    payload = PingPayload()

    assert payload.model_dump() == {}


def test_pong_payload() -> None:
    payload = PongPayload()

    assert payload.model_dump() == {}

