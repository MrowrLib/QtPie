"""Screen utilities for Qt widgets."""

from qtpy.QtWidgets import QWidget


def center_on_screen(widget: QWidget) -> None:
    """Center a widget on its current screen."""
    screen = widget.screen()
    screen_geometry = screen.availableGeometry()
    window_geometry = widget.frameGeometry()
    x = screen_geometry.x() + (screen_geometry.width() - window_geometry.width()) // 2
    y = screen_geometry.y() + (screen_geometry.height() - window_geometry.height()) // 2
    widget.move(x, y)
