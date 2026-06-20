# tui/widgets/conversation.py

from textual.widgets import RichLog
from rich.text import Text


class ConversationWidget(RichLog):
    DEFAULT_CSS = """
    ConversationWidget {
        border: heavy #9ece6a;
        background: #1a1b26;
        color: #c0caf5;
    }
    """

    def on_mount(self) -> None:

        self.border_title = " Conversation "

        self.auto_scroll = True

    def add_user_message(
        self,
        text: str,
    ) -> None:

        self.write(
            Text.assemble(
                ("YOU   ", "bold cyan"),
                (text, "white"),
            )
        )

    def add_orion_message(
        self,
        text: str,
    ) -> None:

        self.write(
            Text.assemble(
                ("ORION ", "bold green"),
                (text, "white"),
            )
        )
