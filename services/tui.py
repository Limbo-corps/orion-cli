from collections import deque

from events.base import Event
from events.events import (
    PipelineFailedEvent,
    VoiceRecordingStartEvent,
    VoiceRecordingCompletedEvent,
    AgentProcessingStartEvent,
    TranscriptGeneratedEvent,
    ResponseGeneratedEvent,
    SpeechSynthesisStartEvent,
    SpeechGeneratedEvent,
)

from services.base import BaseService

from tui.app import OrionApp


class TUIService(BaseService):

    service_name = "tui"

    def __init__(self) -> None:
        super().__init__()

        self.logs = deque(maxlen=250)
        self.conversation = deque(maxlen=50)

        self.mode = "IDLE"

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def handle(
        self,
        event: Event,
    ) -> None:

        self._update_mode(event)
        self._capture_log(event)
        self._capture_conversation(event)

    def _update_mode(
        self,
        event: Event,
    ) -> None:

        if isinstance(event, VoiceRecordingStartEvent):
            self.mode = "RECORDING"

        elif isinstance(event, VoiceRecordingCompletedEvent):
            self.mode = "TRANSCRIBING"

        elif isinstance(event, AgentProcessingStartEvent):
            self.mode = "THINKING"

        elif isinstance(event, SpeechSynthesisStartEvent):
            self.mode = "SYNTHESIZING"

        elif isinstance(event, SpeechGeneratedEvent):
            self.mode = "IDLE"

        elif isinstance(event, PipelineFailedEvent):
            self.mode = "ERROR"

    def _capture_log(
        self,
        event: Event,
    ) -> None:

        app = OrionApp.instance

        event_name = event.__class__.__name__

        self.logs.append(
            (
                event_name,
                event.message,
            )
        )

        if app:

            app.add_event(
                event_name,
                event.message,
            )

            app.update_status(
                self.mode,
                len(self.logs),
            )

    def _capture_conversation(
        self,
        event: Event,
    ) -> None:

        app = OrionApp.instance

        if isinstance(
            event,
            TranscriptGeneratedEvent,
        ):

            self.conversation.append(
                (
                    "user",
                    event.text,
                )
            )

            if app:
                app.add_user_message(
                    event.text,
                )

        elif isinstance(
            event,
            ResponseGeneratedEvent,
        ):

            self.conversation.append(
                (
                    "assistant",
                    event.text,
                )
            )

            if app:
                app.add_orion_message(
                    event.text,
                )