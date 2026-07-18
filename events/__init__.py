from events.events import (
    PipelineStartEvent,
    PipelineCompleteEvent,
    VoiceRecordingStartEvent,
    VoiceRecordingCompletedEvent,
    SpeechDetectedEvent,
    SilenceDetectedEvent,
    TranscriptGeneratedEvent,
    AgentProcessingStartEvent,
    ResponseGeneratedEvent,
    SpeechSynthesisStartEvent,
    SpeechGeneratedEvent,
    PipelineFailedEvent,
)

from memory.events import (
    GraphFactAddedEvent,
    GraphFactRemovedEvent,
    MemoryRecallCompletedEvent,
    MemoryRecallFailedEvent,
    MemoryRecallStartedEvent,
    MemoryShutdownEvent,
    MemoryStartupEvent,
    MemoryStoreCompletedEvent,
    MemoryStoreFailedEvent,
    MemoryStoreStartedEvent,
    SummaryUpdatedEvent,
)

from events.registry import EventRegistry


EventRegistry.register(PipelineStartEvent)
EventRegistry.register(PipelineCompleteEvent)

EventRegistry.register(SpeechDetectedEvent)
EventRegistry.register(SilenceDetectedEvent)

EventRegistry.register(VoiceRecordingStartEvent)
EventRegistry.register(VoiceRecordingCompletedEvent)

EventRegistry.register(TranscriptGeneratedEvent)

EventRegistry.register(AgentProcessingStartEvent)
EventRegistry.register(ResponseGeneratedEvent)

EventRegistry.register(SpeechSynthesisStartEvent)
EventRegistry.register(SpeechGeneratedEvent)

EventRegistry.register(PipelineFailedEvent)

EventRegistry.register(GraphFactAddedEvent)
EventRegistry.register(GraphFactRemovedEvent)
EventRegistry.register(MemoryRecallCompletedEvent)
EventRegistry.register(MemoryStoreFailedEvent)
EventRegistry.register(MemoryRecallStartedEvent)

EventRegistry.register(MemoryRecallFailedEvent)
EventRegistry.register(MemoryShutdownEvent)
EventRegistry.register(MemoryStartupEvent)
EventRegistry.register(MemoryStoreCompletedEvent)
EventRegistry.register(MemoryStoreStartedEvent)
EventRegistry.register(SummaryUpdatedEvent)
