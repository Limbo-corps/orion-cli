"""
IPC bridge.

The bridge connects the transport layer to Orion's internal event system.

Incoming protocol messages are translated into domain events and
published to the EventBus.

Outgoing domain events are translated into protocol messages and sent
back to the appropriate client session.
"""

from __future__ import annotations
from uuid import UUID

from orion.bus.event_bus import EventBus
from orion.events.events import ChatPipelineStartEvent

from .messages import (
    Envelope,
    MessageType,
    SubmitPromptPayload,
)
from .session import ClientSession


class IPCBridge:
    """
    Bridges IPC protocol messages and Orion domain events.
    """

    def __init__(
        self,
        event_bus: EventBus,
    ) -> None:
        """
        Initialise the IPC bridge.

        Args:
            event_bus:
                Orion's event bus.
        """
        self._event_bus = event_bus
        self._session: dict[UUID, ClientSession] = {}

    def register_session(self, session: ClientSession) -> None:
        """
        Register a new client session.

        Args:
            session:
                Client session to register.
        """
        self._session[session.id] = session

    def unregister_session(self, session: ClientSession) -> None:
        """
        Deregister a client session.

        Args:
            session:
                Client session to deregister.
        """
        self._session.pop(session.id, None)

    async def handle(
        self,
        session: ClientSession,
        message: Envelope,
    ) -> None:
        """
        Handle one incoming protocol message.

        Args:
            session:
                Client that sent the message.

            message:
                Incoming protocol message.
        """
        match message.type:
            case MessageType.PING:
                await self._handle_ping(session)

            case MessageType.SUBMIT_PROMPT:
                await self._handle_prompt(session, message)

            case MessageType.VOICE_START:
                ...

            case MessageType.VOICE_CHUNK:
                ...

            case MessageType.VOICE_END:
                ...

            case _:
                raise ValueError(f"Unsupported message: {message.type}")

    async def _handle_ping(
        self,
        session: ClientSession,
    ) -> None:
        """
        Respond to a ping request.
        """
        ...

    async def _handle_prompt(
        self,
        session: ClientSession,
        message: Envelope,
    ) -> None:
        """
        Handle a prompt submission from a client.

        The incoming protocol message is translated into a
        ChatPipelineStartEvent and published to the EventBus.
        """
        payload = SubmitPromptPayload.model_validate(message.payload)

        event = ChatPipelineStartEvent(
            correlation_id=message.correlation_id,
            session_id=session.id,
            source="ipc",
            message="Prompt submitted via IPC.",
            text=payload.text,
        )

        await self._event_bus.publish(event)

        await session.send(
            Envelope(
                correlation_id=message.correlation_id,
                type=MessageType.STATUS,
                payload={
                    "message": "Prompt accepted.",
                },
            )
        )

    async def serve(self, session: ClientSession) -> None:
        print(f"[IPC] Client connected: {session.id}")

        self.register_session(session)

        try:
            while True:
                print("[IPC] Waiting for message...")
                message = await session.receive()
                print(f"[IPC] Received: {message.type}")

                await self.handle(session, message)

        finally:
            print(f"[IPC] Client disconnected: {session.id}")
            self.unregister_session(session)
