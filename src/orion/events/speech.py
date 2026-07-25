from orion.events.base import Event
from orion.events.registry import EventRegistry


class TranscriptGenerated(Event):
    text: str


EventRegistry.register(TranscriptGenerated)
