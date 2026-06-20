# tui/widgets/banner.py

from pathlib import Path

from PIL import Image
from PIL import ImageOps

from rich.align import Align
from rich.text import Text

from textual.widgets import Static


class BannerWidget(Static):
    DEFAULT_CSS = """
    BannerWidget {
        width: 100%;
        height: 100%;

        content-align: center middle;

        background: transparent;
    }
    """

    def image_to_terminal(
        self,
        image_path: str,
        width: int = 35,
        threshold: int = 128,
    ) -> str:

        path = Path(image_path)

        if not path.exists():
            return ""

        img = Image.open(path).convert("L")

        bbox = ImageOps.invert(img).getbbox()

        if bbox:
            img = img.crop(bbox)

        aspect_ratio = img.height / img.width

        height = max(
            1,
            int(width * aspect_ratio),
        )

        img = img.resize(
            (width, height),
            Image.Resampling.LANCZOS,
        )

        pixels = img.load()

        rows: list[str] = []

        for y in range(
            0,
            img.height - 1,
            2,
        ):
            row = ""

            for x in range(img.width):
                top = pixels[x, y]
                bottom = pixels[x, y + 1]

                top_on = top > threshold
                bottom_on = bottom > threshold

                if top_on and bottom_on:
                    row += "█"

                elif top_on:
                    row += "▀"

                elif bottom_on:
                    row += "▄"

                else:
                    row += " "

            rows.append(row)

        return "\n".join(rows)

    def build_banner(self) -> str:

        logo_lines = self.image_to_terminal(
            "assets/ORION.png",
            width=35,
        ).splitlines()

        title_lines = r"""
 ▄█████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗
██╔═══██╗██╔══██╗██║██╔═══██╗████╗  ██║
██║   ██║██████╔╝██║██║   ██║██╔██╗ ██║
██║   ██║██╔══██╗██║██║   ██║██║╚██╗██║
╚██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║
 ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
""".strip("\n").splitlines()

        subtitle_lines = [
            "",
            "Voice-Native AI Assistant",
            "",
            "Event-Driven Voice Intelligence",
        ]

        logo_height = len(logo_lines)
        title_height = len(title_lines)

        if logo_height > title_height:
            pad_top = (logo_height - title_height) // 2

            title_lines = [""] * pad_top + title_lines

        elif title_height > logo_height:
            pad_top = (title_height - logo_height) // 2

            logo_lines = [""] * pad_top + logo_lines

        max_lines = max(
            len(logo_lines),
            len(title_lines),
        )

        logo_lines += [""] * (max_lines - len(logo_lines))

        title_lines += [""] * (max_lines - len(title_lines))

        logo_width = max(len(line) for line in logo_lines)

        rows: list[str] = []

        for logo, title in zip(
            logo_lines,
            title_lines,
        ):
            rows.append(f"{logo:<{logo_width + 8}}{title}")

        subtitle_indent = logo_width + 8

        for line in subtitle_lines:
            rows.append(" " * subtitle_indent + line)

        return "\n".join(rows)

    def render_banner(self) -> None:

        banner_text = Text(
            self.build_banner(),
            style="#7aa2f7",
        )

        self.update(
            Align.center(
                banner_text,
                vertical="middle",
            )
        )

    def on_mount(self) -> None:
        self.render_banner()

    def on_resize(self) -> None:
        self.render_banner()
