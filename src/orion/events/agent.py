from orion.events.base import Event
from orion.events.registry import EventRegistry


class ResponseGenerated(Event):
    text: str


EventRegistry.register(ResponseGenerated)
