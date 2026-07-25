from __future__ import annotations

from abc import ABC, abstractmethod


class Lifecycle(ABC):
    """
    Common lifecycle interface for long-lived runtime components.
    """

    @abstractmethod
    async def startup(self) -> None:
        """Initialize the component."""

    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanly stop the component."""
