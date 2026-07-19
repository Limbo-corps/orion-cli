# tui/app.py

from textual.app import App
from textual.containers import Horizontal

from tui import theme
from tui.widgets.banner import BannerWidget
from tui.widgets.conversation import ConversationWidget
from tui.widgets.events import EventStreamWidget
from tui.widgets.status import StatusWidget


class OrionApp(App):
    instance: "OrionApp | None" = None

    CSS = f"""
    Screen {{
        background: {theme.BG};
        color: {theme.FG};
        padding: 1 2;
    }}

    #banner {{
        height: 2;
        margin-bottom: 1;
    }}

    #content {{
        height: 1fr;
    }}

    #conversation {{
        width: 2fr;
        margin-right: 2;
    }}

    #events {{
        width: 1fr;
    }}

    #status {{
        height: 1;
        margin-top: 1;
    }}
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear", "Clear Events"),
    ]

    def compose(self):

        yield BannerWidget(id="banner")

        with Horizontal(id="content"):
            yield ConversationWidget(id="conversation")

            yield EventStreamWidget(id="events")

        yield StatusWidget(id="status")

    def on_mount(self) -> None:

        OrionApp.instance = self

    # --------------------------------------------------
    # Conversation
    # --------------------------------------------------

    def add_user_message(
        self,
        text: str,
    ) -> None:

        self.query_one(
            "#conversation",
            ConversationWidget,
        ).add_user_message(text)

    def add_orion_message(
        self,
        text: str,
    ) -> None:

        self.query_one(
            "#conversation",
            ConversationWidget,
        ).add_orion_message(text)

    # --------------------------------------------------
    # Events
    # --------------------------------------------------

    def add_event(
        self,
        icon: str,
        message: str,
    ) -> None:

        self.query_one(
            "#events",
            EventStreamWidget,
        ).add_event(
            icon,
            message,
        )

    def clear_events(self) -> None:

        self.query_one(
            "#events",
            EventStreamWidget,
        ).clear_stream()

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def update_status(
        self,
        mode: str,
        events: int,
    ) -> None:

        self.query_one(
            "#status",
            StatusWidget,
        ).update_status(
            mode=mode,
            events=events,
        )

    # --------------------------------------------------
    # Actions
    # --------------------------------------------------

    def action_clear(self) -> None:

        self.clear_events()


if __name__ == "__main__":
    OrionApp().run()
