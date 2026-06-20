# tui/widgets/events.py

from collections import deque
from datetime import datetime

from rich.text import Text

from textual.containers import ScrollableContainer
from textual.widgets import Static


class EventContent(Static):
    pass


class EventStreamWidget(ScrollableContainer):
    DEFAULT_CSS = """
    EventStreamWidget {
        border: round #e0af68;
        background: #1a1b26;

        overflow-y: auto;
        overflow-x: hidden;

        scrollbar-background: #16161e;
        scrollbar-color: #e0af68;
    }

    #event-content {
        width: 100%;
        padding: 0 1;
    }
    """

    ICONS = {
        "PipelineStartEvent": "▶",
        "PipelineCompleteEvent": "✓",
        "PipelineFailedEvent": "✕",
        "VoiceRecordingStartEvent": "●",
        "VoiceRecordingCompletedEvent": "■",
        "VoiceRecordingFailedEvent": "✕",
        "TranscriptGeneratedEvent": "◉",
        "TranscriptGenerationFailedEvent": "✕",
        "AgentProcessingStartEvent": "◆",
        "ResponseGeneratedEvent": "✦",
        "SpeechSynthesisStartEvent": "♪",
        "SpeechGeneratedEvent": "♫",
        "SpeechGenerationFailedEvent": "✕",
        "AudioPlaybackFailedEvent": "✕",
    }

    COLORS = {
        "PipelineStartEvent": "#7aa2f7",
        "PipelineCompleteEvent": "#9ece6a",
        "PipelineFailedEvent": "#f7768e",
        "VoiceRecordingStartEvent": "#e0af68",
        "VoiceRecordingCompletedEvent": "#9ece6a",
        "VoiceRecordingFailedEvent": "#f7768e",
        "TranscriptGeneratedEvent": "#7dcfff",
        "TranscriptGenerationFailedEvent": "#f7768e",
        "AgentProcessingStartEvent": "#bb9af7",
        "ResponseGeneratedEvent": "#9ece6a",
        "SpeechSynthesisStartEvent": "#e0af68",
        "SpeechGeneratedEvent": "#9ece6a",
        "SpeechGenerationFailedEvent": "#f7768e",
        "AudioPlaybackFailedEvent": "#f7768e",
    }

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:

        super().__init__(
            *args,
            **kwargs,
        )

        self._events: deque[Text] = deque(
            maxlen=250,
        )

        self.content = EventContent(
            id="event-content",
        )

    def compose(self):
        yield self.content

    def on_mount(self) -> None:
        self.border_title = " LIVE EVENTS "

    def add_event(
        self,
        event_name: str,
        message: str,
    ) -> None:

        timestamp = datetime.now().strftime("%H:%M:%S")

        icon = self.ICONS.get(
            event_name,
            "•",
        )

        color = self.COLORS.get(
            event_name,
            "#c0caf5",
        )

        line = Text()

        line.append(
            timestamp,
            style="#565f89",
        )

        line.append(
            " │ ",
            style="#414868",
        )

        line.append(
            icon,
            style=color,
        )

        line.append(" ")

        line.append(
            message,
            style="#c0caf5",
        )

        self._events.append(line)

        self.refresh_view()

    def add_success(
        self,
        message: str,
    ) -> None:

        self.add_event(
            "PipelineCompleteEvent",
            message,
        )

    def add_error(
        self,
        message: str,
    ) -> None:

        self.add_event(
            "PipelineFailedEvent",
            message,
        )

    def clear_stream(self) -> None:

        self._events.clear()

        self.refresh_view()

    def refresh_view(self) -> None:

        output = Text()

        for line in self._events:
            output.append_text(line)
            output.append("\n")

        self.content.update(output)

        self.call_after_refresh(
            lambda: self.scroll_end(
                animate=False,
            )
        )
