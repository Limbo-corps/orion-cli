"""
IPC bridge.

The bridge translates between the IPC transport protocol and Orion's
internal event system.

Incoming protocol messages are converted into domain events and published
to the EventBus.

Outgoing protocol messages are routed to the appropriate connected client.
"""

from __future__ import annotations

from uuid import UUID

from collections.abc import Awaitable, Callable

from orion.bus.event_bus import EventBus
from orion.events.events import ChatPipelineStartEvent
from orion.transport.messages import (
    Envelope,
    MessageType,
    PongPayload,
    SubmitPromptPayload,
    VoiceEndPayload,
)
from orion.services.transcript_generation import is_junk_transcript
from orion.transport.session import ClientSession
from orion.transport.transcription import transcribe_audio

#: Async callable turning a recorded audio path into transcript text.
Transcriber = Callable[[str], Awaitable[str]]


class IPCBridge:
    """
    Bridges IPC protocol messages and Orion domain events.
    """

    def __init__(
        self,
        event_bus: EventBus,
        transcriber: Transcriber = transcribe_audio,
    ) -> None:
        self._event_bus = event_bus
        self._transcriber = transcriber
        self._sessions: dict[UUID, ClientSession] = {}

    # ------------------------------------------------------------------
    # Session Management
    # ------------------------------------------------------------------

    def register_session(self, session: ClientSession) -> None:
        """Register a connected client."""
        self._sessions[session.id] = session

    def unregister_session(self, session: ClientSession) -> None:
        """Remove a disconnected client."""
        self._sessions.pop(session.id, None)

    async def send(
        self,
        session_id: UUID,
        envelope: Envelope,
    ) -> None:
        """
        Send an IPC message to a connected client.
        """
        session = self._sessions.get(session_id)

        if session is None:
            return

        await session.send(envelope)

    async def broadcast(
        self,
        envelope: Envelope,
    ) -> None:
        """
        Broadcast an IPC message to every connected client.
        """
        for session in self._sessions.values():
            await session.send(envelope)

    # ------------------------------------------------------------------
    # Incoming Messages
    # ------------------------------------------------------------------

    async def handle(
        self,
        session: ClientSession,
        envelope: Envelope,
    ) -> None:
        """
        Handle one incoming IPC message.
        """

        match envelope.type:
            case MessageType.PING:
                await self._handle_ping(session, envelope)

            case MessageType.SUBMIT_PROMPT:
                await self._handle_submit_prompt(session, envelope)

            case MessageType.VOICE_START:
                # Session metadata only; the path-based flow acts on VOICE_END.
                pass

            case MessageType.VOICE_CHUNK:
                # Streamed audio is a future enhancement.
                pass

            case MessageType.VOICE_END:
                await self._handle_voice_end(session, envelope)

            case _:
                raise ValueError(f"Unsupported IPC message: {envelope.type}")

    async def _handle_ping(
        self,
        session: ClientSession,
        envelope: Envelope,
    ) -> None:
        """
        Respond to a ping request.
        """

        await session.send(
            Envelope(
                correlation_id=envelope.correlation_id,
                type=MessageType.PONG,
                payload=PongPayload().model_dump(),
            )
        )

    async def _handle_submit_prompt(
        self,
        session: ClientSession,
        envelope: Envelope,
    ) -> None:
        """
        Translate a prompt submission into a domain event.
        """

        payload = SubmitPromptPayload.model_validate(envelope.payload)

        await self._event_bus.publish(
            ChatPipelineStartEvent(
                correlation_id=envelope.correlation_id,
                session_id=session.id,
                source="ipc",
                message="Prompt submitted via IPC.",
                text=payload.text,
            )
        )

    async def _handle_voice_end(
        self,
        session: ClientSession,
        envelope: Envelope,
    ) -> None:
        """
        Transcribe a recorded voice message and start the chat pipeline.

        The client sends the path to the audio it recorded; the runtime
        transcribes it and drives the same pipeline as a typed prompt.
        """

        payload = VoiceEndPayload.model_validate(envelope.payload)

        transcript = (await self._transcriber(payload.path)).strip()

        # Ignore empty or hallucinated transcriptions (silence / noise) so a
        # cough doesn't trigger a full agent turn.
        if not transcript or is_junk_transcript(transcript):
            return

        await self._event_bus.publish(
            ChatPipelineStartEvent(
                correlation_id=envelope.correlation_id,
                session_id=session.id,
                source="ipc",
                message="Voice prompt transcribed via IPC.",
                text=transcript,
            )
        )

    # ------------------------------------------------------------------
    # Session Lifecycle
    # ------------------------------------------------------------------

    async def serve(self, session: ClientSession) -> None:
        """
        Process messages from a connected client until it disconnects.
        """

        self.register_session(session)

        try:
            while True:
                envelope = await session.receive()
                await self.handle(session, envelope)

        finally:
            self.unregister_session(session)
