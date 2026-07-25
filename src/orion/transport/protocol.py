"""
Orion IPC protocol helpers.

This module provides utilities for serialising and deserialising IPC
messages exchanged between Orion clients and the runtime.

Messages are encoded as newline-delimited JSON (NDJSON), allowing both
ends of the connection to stream messages efficiently over a single
socket.
"""

from __future__ import annotations

import json

from pydantic import ValidationError

from .messages import Envelope


def encode(message: Envelope) -> bytes:
    """
    Encode a protocol message into newline-delimited JSON.

    Args:
        message:
            The protocol message to encode.

    Returns:
        UTF-8 encoded bytes terminated with a newline.
    """
    return (message.model_dump_json() + "\n").encode("utf-8")


def decode(data: bytes) -> Envelope:
    """
    Decode a protocol message from newline-delimited JSON.

    Args:
        data:
            Raw bytes received from the transport.

    Returns:
        The decoded protocol message.

    Raises:
        ValueError:
            If the message is not valid JSON or does not conform to the
            Orion protocol.
    """
    try:
        obj = json.loads(data.decode("utf-8").strip())

        return Envelope.model_validate(obj)

    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError("Invalid protocol message") from exc
