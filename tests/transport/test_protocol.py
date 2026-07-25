from __future__ import annotations

from uuid import uuid4

import pytest

from orion.transport.messages import (
    Envelope,
    MessageType,
    SubmitPromptPayload,
)
from orion.transport.protocol import decode, encode


def test_encode_message() -> None:
    payload = SubmitPromptPayload(
        text="Hello Orion",
    )

    message = Envelope(
        correlation_id=uuid4(),
        type=MessageType.SUBMIT_PROMPT,
        payload=payload.model_dump(),
    )

    encoded = encode(message)

    assert isinstance(encoded, bytes)
    assert encoded.endswith(b"\n")


def test_decode_message() -> None:
    payload = SubmitPromptPayload(
        text="Hello Orion",
    )

    message = Envelope(
        correlation_id=uuid4(),
        type=MessageType.SUBMIT_PROMPT,
        payload=payload.model_dump(),
    )

    encoded = encode(message)

    decoded = decode(encoded)

    assert decoded == message


def test_round_trip_encode_decode() -> None:
    payload = SubmitPromptPayload(
        text="Round trip",
    )

    original = Envelope(
        correlation_id=uuid4(),
        type=MessageType.SUBMIT_PROMPT,
        payload=payload.model_dump(),
    )

    restored = decode(encode(original))

    assert restored == original


def test_decode_invalid_json() -> None:
    with pytest.raises(ValueError, match="Invalid protocol message"):
        decode(b"{invalid json")


def test_decode_invalid_message() -> None:
    invalid = b'{"version":1,"payload":{},"correlation_id":"123"}'

    with pytest.raises(ValueError, match="Invalid protocol message"):
        decode(invalid)


def test_decode_unknown_message_type() -> None:
    invalid = b"""
    {
        "version": 1,
        "id": "11111111-1111-1111-1111-111111111111",
        "correlation_id": "22222222-2222-2222-2222-222222222222",
        "type": "not_a_message",
        "payload": {}
    }
    """

    with pytest.raises(ValueError, match="Invalid protocol message"):
        decode(invalid)


def test_encode_preserves_correlation_id() -> None:
    correlation_id = uuid4()

    message = Envelope(
        correlation_id=correlation_id,
        type=MessageType.PING,
        payload={},
    )

    decoded = decode(encode(message))

    assert decoded.correlation_id == correlation_id


def test_encode_preserves_message_id() -> None:
    message = Envelope(
        correlation_id=uuid4(),
        type=MessageType.PING,
        payload={},
    )

    decoded = decode(encode(message))

    assert decoded.id == message.id
