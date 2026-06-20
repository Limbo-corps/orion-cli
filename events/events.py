from events.base import Event, EventStatus

# ============================================================
# Log Events
# ============================================================

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


class PipelineRestartEvent(Event):
    status: EventStatus = EventStatus.INFO


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

class SpeechDetectedEvent(Event):
    status: EventStatus = EventStatus.INFO
    # fired when the user STARTS talking (energy crosses the threshold)

class SilenceDetectedEvent(Event):
    status: EventStatus = EventStatus.INFO
    silence_duration: float = 0.0
    # fired when sustained silence is detected and recording stops


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


class SpeechGenerationFailedEvent(Event):
    status: EventStatus = EventStatus.ERROR
    error: str


# ============================================================
# Audio Playback Events
# ============================================================


class AudioPlaybackFailedEvent(Event):
    status: EventStatus = EventStatus.ERROR
    error: str
