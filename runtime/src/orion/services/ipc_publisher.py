from __future__ import annotations

from orion.events.base import Event
from orion.services.base import BaseService
from orion.transport.bridge import IPCBridge
from orion.transport.messages import Envelope


class IPCPublisherService(BaseService):
    """
    Publishes runtime events to connected IPC clients.

    Events that do not define an IPC message type are considered
    internal runtime events and are not forwarded to clients.
    """

    service_name = "ipc"

    def __init__(self, bridge: IPCBridge) -> None:
        super().__init__()
        self._bridge = bridge

    async def handle(self, event: Event) -> None:
        """
        Publish a runtime event over IPC.
        """

        if event.type is None:
            return

        envelope = Envelope(
            correlation_id=event.correlation_id,
            type=event.type,
            payload=event.model_dump(
                exclude={
                    "event_id",
                    "correlation_id",
                    "session_id",
                    "timestamp",
                    "source",
                    "type",
                },
                exclude_none=True,
            ),
        )

        await self._bridge.send(
            session_id=event.session_id,
            envelope=envelope,
        )
