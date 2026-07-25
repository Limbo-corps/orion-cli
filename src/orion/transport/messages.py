from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class MessageType(StrEnum):
    """
    All message types supported by the Orion IPC protocol.

    These messages define the contract between a client (TUI, mobile,
    web, etc.) and the Orion runtime. Transport messages are intentionally
    independent of the runtime's internal domain events.
    """

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    #: Sent by a client to verify that the runtime is reachable.
    PING = "ping"

    #: Sent by the runtime in response to a ping request.
    PONG = "pong"

    # ------------------------------------------------------------------
    # Prompt Submission
    # ------------------------------------------------------------------

    #: Submit a text prompt for the assistant to process.
    SUBMIT_PROMPT = "submit_prompt"

    #: Cancel an in-progress assistant request.
    CANCEL_REQUEST = "cancel_request"

    # ------------------------------------------------------------------
    # Voice Streaming
    # ------------------------------------------------------------------

    #: Indicates the beginning of a voice recording session.
    VOICE_START = "voice_start"

    #: Contains one chunk of streamed audio.
    VOICE_CHUNK = "voice_chunk"

    #: Indicates that the client has finished sending audio.
    VOICE_END = "voice_end"

    # ------------------------------------------------------------------
    # Assistant Streaming
    # ------------------------------------------------------------------

    #: Indicates that the assistant has started generating a response.
    ASSISTANT_START = "assistant_start"

    #: Contains one streamed chunk of assistant text.
    ASSISTANT_CHUNK = "assistant_chunk"

    #: Indicates that the assistant response has completed.
    ASSISTANT_END = "assistant_end"

    # ------------------------------------------------------------------
    # Tool Execution
    # ------------------------------------------------------------------

    #: Indicates that the assistant has started executing a tool.
    TOOL_STARTED = "tool_started"

    #: Indicates that a tool execution has completed.
    TOOL_FINISHED = "tool_finished"

    # ------------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------------

    #: General runtime status update.
    STATUS = "status"

    #: Indicates an unrecoverable error.
    ERROR = "error"


class Envelope(BaseModel):
    """
    A transport message exchanged between the Orion runtime and a client.

    Every message transmitted over the IPC channel is wrapped inside an
    Envelope. The payload is interpreted according to the message type.
    """

    model_config = ConfigDict(use_enum_values=True)

    #: Protocol version used for compatibility checks.
    version: int = 1

    #: Unique identifier for this message.
    id: UUID = Field(default_factory=uuid4)

    #: ID of the request/workflow this message belongs to
    correlation_id: UUID = Field(default_factory=uuid4)

    #: Type of message being transmitted.
    type: MessageType

    #: Message-specific payload.
    payload: dict[str, Any]


# ======================================================================
# Client -> Runtime
# ======================================================================


class SubmitPromptPayload(BaseModel):
    """A user prompt submitted to the assistant."""

    #: User's prompt.
    text: str


class CancelRequestPayload(BaseModel):
    """Request cancellation of an active assistant task."""

    #: Identifier of the request to cancel.
    request_id: UUID


class VoiceStartPayload(BaseModel):
    """Metadata describing a new voice recording session."""

    #: Audio sampling frequency.
    sample_rate: int

    #: Number of audio channels.
    channels: int

    #: Audio encoding format.
    encoding: str = "pcm16"


class VoiceChunkPayload(BaseModel):
    """A single streamed audio frame."""

    #: Sequential chunk number.
    sequence: int

    #: Raw encoded audio bytes.
    data: bytes


class VoiceEndPayload(BaseModel):
    """Marks the end of a streamed voice recording."""


# ======================================================================
# Runtime -> Client
# ======================================================================


class AssistantStartPayload(BaseModel):
    """Signals the start of assistant response generation."""


class AssistantChunkPayload(BaseModel):
    """A streamed fragment of assistant output."""

    #: Partial assistant response.
    text: str


class AssistantEndPayload(BaseModel):
    """Signals completion of assistant response generation."""


class ToolStartedPayload(BaseModel):
    """Indicates that the assistant has started executing a tool."""

    #: Name of the tool.
    name: str


class ToolFinishedPayload(BaseModel):
    """Indicates that a tool execution has completed."""

    #: Name of the tool.
    name: str

    #: Whether execution completed successfully.
    success: bool


class StatusPayload(BaseModel):
    """General runtime status update."""

    #: Human-readable status message.
    message: str


class ErrorPayload(BaseModel):
    """Represents an error returned by the runtime."""

    #: Machine-readable error identifier.
    code: str

    #: Human-readable error description.
    message: str


class PingPayload(BaseModel):
    """Ping request payload."""


class PongPayload(BaseModel):
    """Ping response payload."""
