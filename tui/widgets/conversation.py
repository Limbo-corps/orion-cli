# tui/widgets/conversation.py

from rich.text import Text

from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Static

from tui import theme


class ChatBubble(Static):
    """A single rounded, colored-edge message bubble."""


class MessageRow(Horizontal):
    """A full-width row that left/right-aligns its bubble."""


class ConversationWidget(VerticalScroll):
    DEFAULT_CSS = f"""
    ConversationWidget {{
        background: {theme.PANEL};
        border: round {theme.BORDER};
        border-title-color: {theme.MUTED};
        border-title-align: left;
        padding: 1 2;
        scrollbar-background: {theme.PANEL};
        scrollbar-color: {theme.DIM};
        scrollbar-size-vertical: 1;
    }}

    MessageRow {{
        height: auto;
        width: 100%;
        margin-bottom: 1;
    }}

    MessageRow.orion {{
        align-horizontal: left;
    }}

    MessageRow.user {{
        align-horizontal: right;
    }}

    ChatBubble {{
        width: auto;
        max-width: 74%;
        height: auto;
        padding: 0 2;
    }}

    ChatBubble.orion {{
        border: round {theme.ORION_EDGE};
        background: {theme.ORION_BUBBLE};
        color: {theme.FG};
    }}

    ChatBubble.user {{
        border: round {theme.USER_EDGE};
        background: {theme.USER_BUBBLE};
        color: {theme.FG};
    }}
    """

    def on_mount(self) -> None:
        self.border_title = " conversation "

    def add_orion_message(
        self,
        text: str,
    ) -> None:
        content = Text()
        content.append(f"{theme.ORION_ICON} ", style=theme.ORION_ACCENT)
        content.append("ORION", style=f"bold {theme.ORION_ACCENT}")
        content.append("\n")
        content.append(text, style=theme.FG)

        self._add(content, side="orion")

    def add_user_message(
        self,
        text: str,
    ) -> None:
        content = Text(justify="right")
        content.append(theme.USER_NAME, style=f"bold {theme.USER_ACCENT}")
        content.append("\n")
        content.append(text, style=theme.FG)

        self._add(content, side="user")

    def _add(
        self,
        content: Text,
        side: str,
    ) -> None:
        bubble = ChatBubble(content, classes=side)
        row = MessageRow(bubble, classes=side)

        self.mount(row)

        self.call_after_refresh(
            lambda: self.scroll_end(animate=False),
        )
