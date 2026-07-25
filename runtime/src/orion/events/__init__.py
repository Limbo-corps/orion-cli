from orion.events.events import (
    # Pipeline
    PipelineStartEvent,
    VoicePipelineStartEvent,
    ChatPipelineStartEvent,
    PipelineCompleteEvent,
    PipelineFailedEvent,
    PipelineRestartEvent,
    # Voice
    SpeechDetectedEvent,
    SilenceDetectedEvent,
    VoiceRecordingStartEvent,
    VoiceRecordingCompletedEvent,
    # Speech-to-Text
    TranscriptGeneratedEvent,
    # Agent
    AgentProcessingStartEvent,
    ResponseStartedEvent,
    ResponseChunkEvent,
    ResponseCompletedEvent,
    ResponseGenerationFailedEvent,
    # Text-to-Speech
    SpeechSynthesisStartEvent,
    SpeechGeneratedEvent,
)

from orion.memory.events import (
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

from orion.events.registry import EventRegistry


# ============================================================
# Pipeline
# ============================================================

EventRegistry.register(PipelineStartEvent)
EventRegistry.register(VoicePipelineStartEvent)
EventRegistry.register(ChatPipelineStartEvent)
EventRegistry.register(PipelineCompleteEvent)
EventRegistry.register(PipelineFailedEvent)
EventRegistry.register(PipelineRestartEvent)


# ============================================================
# Voice
# ============================================================

EventRegistry.register(SpeechDetectedEvent)
EventRegistry.register(SilenceDetectedEvent)
EventRegistry.register(VoiceRecordingStartEvent)
EventRegistry.register(VoiceRecordingCompletedEvent)


# ============================================================
# Speech-to-Text
# ============================================================

EventRegistry.register(TranscriptGeneratedEvent)


# ============================================================
# Agent
# ============================================================

EventRegistry.register(AgentProcessingStartEvent)

EventRegistry.register(ResponseStartedEvent)
EventRegistry.register(ResponseChunkEvent)
EventRegistry.register(ResponseCompletedEvent)
EventRegistry.register(ResponseGenerationFailedEvent)


# ============================================================
# Text-to-Speech
# ============================================================

EventRegistry.register(SpeechSynthesisStartEvent)
EventRegistry.register(SpeechGeneratedEvent)


# ============================================================
# Memory
# ============================================================

EventRegistry.register(GraphFactAddedEvent)
EventRegistry.register(GraphFactRemovedEvent)

EventRegistry.register(MemoryStartupEvent)
EventRegistry.register(MemoryShutdownEvent)

EventRegistry.register(MemoryRecallStartedEvent)
EventRegistry.register(MemoryRecallCompletedEvent)
EventRegistry.register(MemoryRecallFailedEvent)

EventRegistry.register(MemoryStoreStartedEvent)
EventRegistry.register(MemoryStoreCompletedEvent)
EventRegistry.register(MemoryStoreFailedEvent)

EventRegistry.register(SummaryUpdatedEvent)
