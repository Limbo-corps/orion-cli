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

    def header_text(self, width: int) -> Text:
        """Build the slim header (wordmark + rule). Pure; easy to test."""
        head = Text.assemble(
            (f"{theme.ORION_ICON} ", theme.ORION_ACCENT),
            ("ORION", f"bold {theme.ORION_ACCENT}"),
            ("   ·   ", theme.DIM),
            ("voice-native assistant", theme.MUTED),
        )

        rule = Text("─" * max(width, 24), style=theme.ORION_EDGE)

        return Text.assemble(head, "\n", rule)

    def render_header(self) -> None:
        self.update(self.header_text(self.size.width))
