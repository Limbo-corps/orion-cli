from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


# ======================================================================
# Message Types
# ======================================================================


class MessageType(StrEnum):
    """
    All message types supported by the Orion IPC protocol.

    Transport messages are intentionally independent of Orion's internal
    domain event classes. Internal events are translated into Envelopes
    before being sent to clients.
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
    # Pipeline
    # ------------------------------------------------------------------

    #: Indicates that a processing pipeline has started.
    PIPELINE_STARTED = "pipeline_started"

    #: Indicates that a processing pipeline completed successfully.
    PIPELINE_COMPLETED = "pipeline_completed"

    #: Indicates that a processing pipeline failed.
    PIPELINE_FAILED = "pipeline_failed"

    #: Indicates that a processing pipeline was restarted.
    PIPELINE_RESTARTED = "pipeline_restarted"

    # ------------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------------

    #: General runtime status update.
    STATUS = "status"

    #: Indicates an error.
    ERROR = "error"

    #: Runtime event
    RUNTIME_EVENT = "runtime_event"


# ======================================================================
# Envelope
# ======================================================================


class Envelope(BaseModel):
    """
    Transport envelope exchanged between the Orion runtime and clients.

    Every message transmitted over IPC is wrapped inside an Envelope.

    The payload is interpreted according to the message type.
    """

    model_config = ConfigDict(
        use_enum_values=True,
    )

    #: Protocol version used for compatibility checks.
    version: int = 1

    #: Unique identifier for this individual message.
    id: UUID = Field(
        default_factory=uuid4,
    )

    #: Identifier of the request/workflow this message belongs to.
    correlation_id: UUID | None = None

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
    """
    Marks the end of a voice recording.

    Carries the path to the file the runtime should process.
    """

    #: Filesystem path to the recorded audio.
    path: str


# ======================================================================
# Runtime -> Client
# ======================================================================


# ----------------------------------------------------------------------
# Assistant
# ----------------------------------------------------------------------


class AssistantStartPayload(BaseModel):
    """Signals the start of assistant response generation."""


class AssistantChunkPayload(BaseModel):
    """A streamed fragment of assistant output."""

    #: Partial assistant response.
    text: str


class AssistantEndPayload(BaseModel):
    """Signals completion of assistant response generation."""


# ----------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------


class PipelineStartedPayload(BaseModel):
    """Signals that a processing pipeline has started."""

    #: Name of the pipeline.
    pipeline: str


class PipelineCompletedPayload(BaseModel):
    """Signals that a processing pipeline completed successfully."""

    #: Name of the pipeline.
    pipeline: str


class PipelineFailedPayload(BaseModel):
    """
    Describes a failed processing pipeline.

    The traceback is optional so production clients do not have to
    expose implementation details while development clients can still
    display complete debugging information.
    """

    #: Name of the pipeline that failed.
    pipeline: str

    #: Machine-readable exception type.
    error_type: str

    #: Human-readable error message.
    message: str

    #: Full traceback when available.
    traceback: str | None = None


class PipelineRestartedPayload(BaseModel):
    """Signals that a processing pipeline has been restarted."""

    #: Name of the pipeline.
    pipeline: str


# ----------------------------------------------------------------------
# Tool Execution
# ----------------------------------------------------------------------


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


# ----------------------------------------------------------------------
# Runtime Status
# ----------------------------------------------------------------------


class StatusPayload(BaseModel):
    """General runtime status update."""

    #: Human-readable status message.
    message: str


class ErrorPayload(BaseModel):
    """
    Represents an error returned by the runtime.

    This is intended for errors that are not represented by a more
    specific pipeline failure message.
    """

    #: Machine-readable error identifier.
    code: str

    #: Human-readable error description.
    message: str

    #: Exception type when available.
    error_type: str | None = None

    #: Pipeline associated with the error when applicable.
    pipeline: str | None = None

    #: Full traceback when available.
    traceback: str | None = None


# ----------------------------------------------------------------------
# Voice / Speech
# ----------------------------------------------------------------------


class VoiceRecordingStartedPayload(BaseModel):
    """Signals that voice recording has started."""


class VoiceRecordingCompletedPayload(BaseModel):
    """Signals that voice recording has completed."""

    #: Path to the recorded audio.
    path: str | None = None


class TranscriptPayload(BaseModel):
    """Contains a generated speech transcript."""

    #: Transcribed text.
    text: str


class SpeechSynthesisPayload(BaseModel):
    """Contains information about generated speech."""

    #: Text that was synthesized.
    text: str

    #: Generated audio path, if available.
    audio_path: str | None = None


# ----------------------------------------------------------------------
# Audio Playback
# ----------------------------------------------------------------------


class AudioPlaybackStartedPayload(BaseModel):
    """Signals that audio playback has started."""


class AudioPlaybackCompletedPayload(BaseModel):
    """Signals that audio playback has completed."""


# ----------------------------------------------------------------------
# Connection
# ----------------------------------------------------------------------


class PingPayload(BaseModel):
    """Ping request payload."""


class PongPayload(BaseModel):
    """Ping response payload."""