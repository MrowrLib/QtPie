from PySide6.QtWidgets import QWidget


def center_on_screen(widget: QWidget):
    screen = widget.screen()
    screen_geometry = screen.geometry()
    window_geometry = widget.geometry()
    x = screen_geometry.x() + (screen_geometry.width() - window_geometry.width()) // 2
    y = screen_geometry.y() + (screen_geometry.height() - window_geometry.height()) // 2
    widget.setGeometry(x, y, window_geometry.width(), window_geometry.height())
