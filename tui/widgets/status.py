# tui/widgets/status.py

from textual.widgets import Static


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
    DEFAULT_CSS = """
    StatusWidget {
        height: 3;
        background: #1a1b26;
        border-top: heavy #565f89;
        color: #c0caf5;
        content-align: center middle;
        text-style: bold;
    }
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

        spinner = SPINNER[self._frame % len(SPINNER)]

        mic_color = "#f7768e" if self.mode == "RECORDING" else "#9ece6a"

        mode_color = {
            "IDLE": "#9ece6a",
            "RECORDING": "#f7768e",
            "TRANSCRIBING": "#7dcfff",
            "THINKING": "#bb9af7",
            "SYNTHESIZING": "#e0af68",
            "ERROR": "#f7768e",
        }.get(
            self.mode,
            "#c0caf5",
        )

        self.update(
            (
                f"[{mic_color}]󰍬 MIC[/]   │   "
                f"[#9ece6a]󰕾 SPK[/]   │   "
                f"[#7dcfff]󰚩 GROQ[/]   │   "
                f"[{mode_color}]{spinner} {self.mode}[/]   │   "
                f"[#bb9af7]{self.events} EVENTS[/]   │   "
                f"[#565f89]CTRL+Q EXIT[/]"
            )
        )
