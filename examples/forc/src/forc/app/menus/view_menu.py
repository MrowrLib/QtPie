from qtpy.QtCore import Signal
from qtpy.QtGui import QAction

from qtpie import ColorScheme, Menu, menu, new, set_color_scheme


@menu(title="View")
class ViewMenu(Menu):
    on_reload_window = Signal()

    light_mode: QAction = new("Switch to Light Mode", triggered="on_light_mode")
    dark_mode: QAction = new("Switch to Dark Mode", triggered="on_dark_mode")

    def on_light_mode(self):
        set_color_scheme(ColorScheme.Light)
        self.on_reload_window.emit()

    def on_dark_mode(self):
        set_color_scheme(ColorScheme.Dark)
        self.on_reload_window.emit()
