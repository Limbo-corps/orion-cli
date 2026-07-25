from orion.events.base import Event, EventStatus
from orion.transport.messages import MessageType

# ============================================================
# Pipeline Events
# ============================================================


class PipelineStartEvent(Event):
    """Base event published when a processing pipeline is started."""


class VoicePipelineStartEvent(PipelineStartEvent):
    """Published when a voice processing pipeline is started."""


class ChatPipelineStartEvent(PipelineStartEvent):
    """Published when a chat processing pipeline is started."""

    type: MessageType = MessageType.SUBMIT_PROMPT
    text: str


class PipelineCompleteEvent(Event):
    """Published when a processing pipeline completes successfully."""

    status: EventStatus = EventStatus.SUCCESS


class PipelineFailedEvent(Event):
    """Published when a processing pipeline fails."""

    status: EventStatus = EventStatus.ERROR
    error: str


class PipelineRestartEvent(Event):
    """Published when a processing pipeline is restarted."""


# ============================================================
# Voice Events
# ============================================================


class VoiceRecordingStartEvent(Event):
    """Published when voice recording begins."""

    type: MessageType = MessageType.VOICE_START


class VoiceRecordingCompletedEvent(Event):
    """Published when voice recording has completed."""

    type: MessageType = MessageType.VOICE_END
    audio_path: str | None = None


class VoiceRecordingFailedEvent(Event):
    """Published when voice recording fails."""

    status: EventStatus = EventStatus.ERROR
    error: str


class SpeechDetectedEvent(Event):
    """Published when speech is detected in the audio stream."""


class SilenceDetectedEvent(Event):
    """Published when sustained silence is detected."""

    silence_duration: float = 0.0


# ============================================================
# Speech-to-Text Events
# ============================================================


class TranscriptGeneratedEvent(Event):
    """Published after speech has been successfully transcribed."""

    text: str


class TranscriptGenerationFailedEvent(Event):
    """Published when speech transcription fails."""

    status: EventStatus = EventStatus.ERROR
    error: str


# ============================================================
# Agent Events
# ============================================================


class AgentProcessingStartEvent(Event):
    """Published when the agent begins processing a request."""


class ResponseStartedEvent(Event):
    """Published when the assistant starts generating a response."""

    type: MessageType = MessageType.ASSISTANT_START


class ResponseChunkEvent(Event):
    """Published for each streamed response chunk."""

    type: MessageType = MessageType.ASSISTANT_CHUNK
    text: str


class ResponseCompletedEvent(Event):
    """Published when the assistant has finished generating a response."""

    type: MessageType = MessageType.ASSISTANT_END
    status: EventStatus = EventStatus.SUCCESS
    text: str


class ResponseGenerationFailedEvent(Event):
    """Published when response generation fails."""

    type: MessageType = MessageType.ERROR
    status: EventStatus = EventStatus.ERROR
    error: str


# ============================================================
# Text-to-Speech Events
# ============================================================


class SpeechSynthesisStartEvent(Event):
    """Published when speech synthesis begins."""

    text: str


class SpeechGeneratedEvent(Event):
    """Published when speech synthesis completes successfully."""

    status: EventStatus = EventStatus.SUCCESS
    audio_path: str | None = None
    text: str


class SpeechGenerationFailedEvent(Event):
    """Published when speech synthesis fails."""

    status: EventStatus = EventStatus.ERROR
    error: str


# ============================================================
# Audio Playback Events
# ============================================================


class AudioPlaybackStartedEvent(Event):
    """Published when audio playback begins."""


class AudioPlaybackCompletedEvent(Event):
    """Published when audio playback completes successfully."""

    status: EventStatus = EventStatus.SUCCESS


class AudioPlaybackFailedEvent(Event):
    """Published when audio playback fails."""

    status: EventStatus = EventStatus.ERROR
    error: str
