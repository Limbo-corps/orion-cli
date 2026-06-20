from PIL import Image, ImageOps

from rich.console import Console
from rich.panel import Panel


console = Console()


def image_to_terminal(
    image_path: str,
    width: int = 35,
    threshold: int = 128,
) -> str:
    """
    Convert logo image into terminal block art.
    Automatically crops empty borders.
    """

    img = Image.open(image_path).convert("L")

    # Crop black borders
    bbox = ImageOps.invert(img).getbbox()
    if bbox:
        img = img.crop(bbox)

    aspect_ratio = img.height / img.width
    height = max(1, int(width * aspect_ratio))

    img = img.resize(
        (width, height),
        Image.Resampling.LANCZOS,
    )

    pixels = img.load()

    output = []

    for y in range(0, img.height - 1, 2):
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

        output.append(row)

    return "\n".join(output)


def print_banner() -> None:
    logo_lines = image_to_terminal(
        "assets/ORION.png",
        width=35,
    ).splitlines()

    banner_lines = r"""
 ▄█████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗
██╔═══██╗██╔══██╗██║██╔═══██╗████╗  ██║
██║   ██║██████╔╝██║██║   ██║██╔██╗ ██║
██║   ██║██╔══██╗██║██║   ██║██║╚██╗██║
╚██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║
 ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝

      Voice-Native AI Assistant

     Event-Driven Voice Intelligence
""".splitlines()

    # Remove leading/trailing blank lines from raw string
    banner_lines = [
        line for line in banner_lines
    ]

    logo_height = len(logo_lines)
    banner_height = len(banner_lines)

    # Vertically center the banner relative to logo
    if logo_height > banner_height:
        pad_top = (logo_height - banner_height) // 2
        banner_lines = (
            [""] * pad_top
            + banner_lines
        )
    elif banner_height > logo_height:
        pad_top = (banner_height - logo_height) // 2
        logo_lines = (
            [""] * pad_top
            + logo_lines
        )

    max_lines = max(
        len(logo_lines),
        len(banner_lines),
    )

    logo_lines += [""] * (
        max_lines - len(logo_lines)
    )

    banner_lines += [""] * (
        max_lines - len(banner_lines)
    )

    logo_width = max(
        len(line)
        for line in logo_lines
    )

    rows = []

    for logo, banner in zip(
        logo_lines,
        banner_lines,
    ):
        rows.append(
            f"{logo:<{logo_width + 4}}{banner}"
        )

    content = "\n".join(rows)

    console.print(
        Panel(
            content,
            border_style="bright_blue",
            title="[bold magenta]ORION[/bold magenta]",
            padding=(1, 2),
        )
    )


if __name__ == "__main__":
    print_banner()