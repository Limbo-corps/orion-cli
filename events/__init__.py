from events.events import (
    PipelineStartEvent,
    PipelineCompleteEvent,
    VoiceRecordingStartEvent,
    VoiceRecordingCompletedEvent,
    TranscriptGeneratedEvent,
    AgentProcessingStartEvent,
    ResponseGeneratedEvent,
    SpeechSynthesisStartEvent,
    SpeechGeneratedEvent,
    PipelineFailedEvent,
)

from events.registry import EventRegistry


EventRegistry.register(PipelineStartEvent)
EventRegistry.register(PipelineCompleteEvent)

EventRegistry.register(VoiceRecordingStartEvent)
EventRegistry.register(VoiceRecordingCompletedEvent)

EventRegistry.register(TranscriptGeneratedEvent)

EventRegistry.register(AgentProcessingStartEvent)
EventRegistry.register(ResponseGeneratedEvent)

EventRegistry.register(SpeechSynthesisStartEvent)
EventRegistry.register(SpeechGeneratedEvent)

EventRegistry.register(PipelineFailedEvent)