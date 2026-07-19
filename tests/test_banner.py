from tui.widgets.banner import BannerWidget


def test_banner_renders_orion_wordmark():
    widget = BannerWidget()

    header = widget.header_text(width=40)
    plain = header.plain

    assert "ORION" in plain
    assert "\n" in plain
