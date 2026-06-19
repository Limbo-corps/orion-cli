from typing import Type
from events.base import Event


class EventRegistry:
    """
    Registery to register all the events that are made
    """

    _registry: dict[str, Type[Event]] = {}

    @classmethod
    def register(cls, event_type: Type[Event]) -> None:
        cls._registry[event_type.__name__] = event_type

    @classmethod
    def get(cls, event_name: str) -> Type[Event]:
        try:
            return cls._registry[event_name]

        except KeyError:
            raise ValueError(f"Unknown event type: {event_name}")
