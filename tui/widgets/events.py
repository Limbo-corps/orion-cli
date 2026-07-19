# tui/widgets/events.py

from collections import deque
from datetime import datetime

from rich.text import Text

from textual.containers import ScrollableContainer
from textual.widgets import Static

from tui import theme


class EventContent(Static):
    pass


class EventStreamWidget(ScrollableContainer):
    DEFAULT_CSS = f"""
    EventStreamWidget {{
        border: round {theme.BORDER};
        border-title-color: {theme.MUTED};
        border-title-align: left;
        background: {theme.PANEL};

        overflow-y: auto;
        overflow-x: hidden;

        scrollbar-background: {theme.PANEL};
        scrollbar-color: {theme.DIM};
        scrollbar-size-vertical: 1;
    }}

    #event-content {{
        width: 100%;
        padding: 1 2;
    }}
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

    # Mono palette: greyscale by default, muted red for failures,
    # muted green for completions, soft slate for "start" markers.
    COLORS = {
        "PipelineStartEvent": theme.ORION_ACCENT,
        "PipelineCompleteEvent": theme.OK,
        "PipelineFailedEvent": theme.DANGER,
        "VoiceRecordingStartEvent": theme.ORION_ACCENT,
        "VoiceRecordingCompletedEvent": theme.MUTED,
        "VoiceRecordingFailedEvent": theme.DANGER,
        "TranscriptGeneratedEvent": theme.FG,
        "TranscriptGenerationFailedEvent": theme.DANGER,
        "AgentProcessingStartEvent": theme.ORION_ACCENT,
        "ResponseGeneratedEvent": theme.FG,
        "SpeechSynthesisStartEvent": theme.MUTED,
        "SpeechGeneratedEvent": theme.OK,
        "SpeechGenerationFailedEvent": theme.DANGER,
        "AudioPlaybackFailedEvent": theme.DANGER,
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
        self.border_title = " live events "

    def add_event(
        self,
        event_name: str,
        message: str,
    ) -> None:

        timestamp = datetime.now().strftime("%H:%M:%S")

        icon = self.ICONS.get(
            event_name,
            "·",
        )

        color = self.COLORS.get(
            event_name,
            theme.MUTED,
        )

        line = Text()

        line.append(
            timestamp,
            style=theme.DIM,
        )

        line.append(
            "  ",
        )

        line.append(
            icon,
            style=color,
        )

        line.append("  ")

        line.append(
            message,
            style=theme.MUTED,
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
