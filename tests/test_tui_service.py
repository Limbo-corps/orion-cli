import asyncio
from uuid import uuid4

from bus.event_bus import EventBus
from events.events import (
    AgentProcessingStartEvent,
    ResponseGeneratedEvent,
    SpeechGeneratedEvent,
    SpeechSynthesisStartEvent,
    TranscriptGeneratedEvent,
    VoiceRecordingStartEvent,
)
from services.tui import TUIService
from tui.app import OrionApp


class FakeApp:
    def __init__(self) -> None:
        self.events = []
        self.status_updates = []
        self.user_messages = []
        self.orion_messages = []

    def add_event(self, icon: str, message: str) -> None:
        self.events.append((icon, message))

    def update_status(self, mode: str, events: int) -> None:
        self.status_updates.append((mode, events))

    def add_user_message(self, text: str) -> None:
        self.user_messages.append(text)

    def add_orion_message(self, text: str) -> None:
        self.orion_messages.append(text)


class FakeStore:
    async def append(self, event) -> None:
        return None


def test_tui_service_updates_mode_and_conversation_stream():
    async def scenario():
        original_app = OrionApp.instance
        OrionApp.instance = FakeApp()

        try:
            EventBus(FakeStore())
            service = TUIService()

            await service.handle(
                VoiceRecordingStartEvent(
                    correlation_id=uuid4(),
                    source="voice",
                    message="Recording started",
                )
            )

            await service.handle(
                AgentProcessingStartEvent(
                    correlation_id=uuid4(),
                    source="agent",
                    message="Thinking",
                )
            )

            await service.handle(
                TranscriptGeneratedEvent(
                    correlation_id=uuid4(),
                    source="stt",
                    text="Hello ORION",
                )
            )

            await service.handle(
                SpeechSynthesisStartEvent(
                    correlation_id=uuid4(),
                    source="tts",
                    text="Hello human",
                    message="Synthesizing",
                )
            )

            await service.handle(
                ResponseGeneratedEvent(
                    correlation_id=uuid4(),
                    source="agent",
                    text="Hello human",
                )
            )

            await service.handle(
                SpeechGeneratedEvent(
                    correlation_id=uuid4(),
                    source="tts",
                    audio_path="/tmp/output.wav",
                    message="Speech generated",
                )
            )

            assert service.mode == "IDLE"
            assert OrionApp.instance.events[0][1] == "Recording started"
            assert OrionApp.instance.user_messages == ["Hello ORION"]
            assert OrionApp.instance.orion_messages == ["Hello human"]
            assert OrionApp.instance.status_updates[-1][0] == "IDLE"
        finally:
            OrionApp.instance = original_app

    asyncio.run(scenario())
