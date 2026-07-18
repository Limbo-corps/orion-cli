# tui/widgets/banner.py

from rich.text import Text

from textual.widgets import Static

from tui import theme


class BannerWidget(Static):
    """
    Slim, mono header: a wordmark + tagline over a thin rule.
    """

    DEFAULT_CSS = f"""
    BannerWidget {{
        width: 100%;
        height: 2;
        content-align: left middle;
        background: transparent;
        color: {theme.FG};
    }}
    """

    def on_mount(self) -> None:
        self.render_header()

    def on_resize(self) -> None:
        self.render_header()

    def render_header(self) -> None:
        head = Text.assemble(
            (f"{theme.ORION_ICON} ", theme.ORION_ACCENT),
            ("ORION", f"bold {theme.ORION_ACCENT}"),
            ("   ·   ", theme.DIM),
            ("voice-native assistant", theme.MUTED),
        )

        width = max(self.size.width, 24)
        rule = Text("─" * width, style=theme.ORION_EDGE)

        self.update(Text.assemble(head, "\n", rule))
