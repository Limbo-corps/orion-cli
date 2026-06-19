from events.base import Event
from events.registry import EventRegistry


class ResponseGenerated(Event):
    text: str


EventRegistry.register(ResponseGenerated)
