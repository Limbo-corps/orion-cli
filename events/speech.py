from events.base import Event
from events.registry import EventRegistry


class TranscriptGenerated(Event):
    text: str


EventRegistry.register(TranscriptGenerated)
