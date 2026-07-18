# tui/widgets/status.py

from textual.widgets import Static

from tui import theme


SPINNER = [
    "⠋",
    "⠙",
    "⠹",
    "⠸",
    "⠼",
    "⠴",
    "⠦",
    "⠧",
    "⠇",
    "⠏",
]


class StatusWidget(Static):
    DEFAULT_CSS = f"""
    StatusWidget {{
        height: 1;
        background: transparent;
        color: {theme.MUTED};
        content-align: left middle;
    }}
    """

    def __init__(
        self,
        mode: str = "IDLE",
        events: int = 0,
        *args,
        **kwargs,
    ) -> None:

        super().__init__(
            *args,
            **kwargs,
        )

        self.mode = mode
        self.events = events

        self._frame = 0
        self._timer = None

    def on_mount(self) -> None:

        self._timer = self.set_interval(
            0.1,
            self.animate,
        )

        self.refresh_status()

    def animate(self) -> None:

        self._frame += 1
        self.refresh_status()

    def update_status(
        self,
        mode: str,
        events: int,
    ) -> None:

        self.mode = mode
        self.events = events

        self.refresh_status()

    def refresh_status(self) -> None:

        state_color = theme.STATE_COLORS.get(self.mode, theme.FG)

        if self.mode == "IDLE":
            marker = "●"
        else:
            marker = SPINNER[self._frame % len(SPINNER)]

        sep = f"[{theme.DIM}]·[/]"

        self.update(
            (
                f"[{state_color}]{marker} {self.mode.lower()}[/]"
                f"   {sep}   "
                f"[{theme.MUTED}]groq[/]"
                f"   {sep}   "
                f"[{theme.MUTED}]{self.events} events[/]"
                f"   {sep}   "
                f"[{theme.DIM}]q quit[/]"
                f"   {sep}   "
                f"[{theme.DIM}]c clear[/]"
            )
        )
