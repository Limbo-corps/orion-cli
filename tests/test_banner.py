from tui.widgets.banner import BannerWidget


def test_banner_image_converts_to_terminal_art():
    widget = BannerWidget()

    art = widget.image_to_terminal("assets/ORION.png", width=20)

    assert art.strip() != ""
    assert "\n" in art
