from events.base import Event, EventStatus


# ============================================================
# Pipeline Events
# ============================================================


class PipelineStartEvent(Event):
    status: EventStatus = EventStatus.INFO


class PipelineCompleteEvent(Event):
    status: EventStatus = EventStatus.INFO


class PipelineFailedEvent(Event):
    status: EventStatus = EventStatus.ERROR
    error: str


# ============================================================
# Voice Events
# ============================================================


class VoiceRecordingStartEvent(Event):
    status: EventStatus = EventStatus.INFO


class VoiceRecordingCompletedEvent(Event):
    status: EventStatus = EventStatus.INFO
    audio_path: str | None = None


class VoiceRecordingFailedEvent(Event):
    status: EventStatus = EventStatus.ERROR
    error: str


# ============================================================
# Speech-to-Text Events
# ============================================================


class TranscriptGeneratedEvent(Event):
    status: EventStatus = EventStatus.INFO
    text: str


class TranscriptGenerationFailedEvent(Event):
    status: EventStatus = EventStatus.ERROR
    error: str


# ============================================================
# Agent Events
# ============================================================


class AgentProcessingStartEvent(Event):
    status: EventStatus = EventStatus.INFO


class ResponseGeneratedEvent(Event):
    status: EventStatus = EventStatus.INFO
    text: str


# ============================================================
# Text-to-Speech Events
# ============================================================


class SpeechSynthesisStartEvent(Event):
    status: EventStatus = EventStatus.INFO
    text: str


class SpeechGeneratedEvent(Event):
    status: EventStatus = EventStatus.INFO
    audio_path: str | None = None
