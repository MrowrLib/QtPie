from qtpy.QtGui import QAction

from qtpie import ColorScheme, Menu, menu, new, set_color_scheme
from qtpie.styles.theme_runtime import set_theme


@menu(title="View")
class ViewMenu(Menu):
    light_mode: QAction = new("Switch to Light Mode", triggered="on_light_mode")
    dark_mode: QAction = new("Switch to Dark Mode", triggered="on_dark_mode")

    def on_light_mode(self):
        set_color_scheme(ColorScheme.Light)
        set_theme("light")
        self.emit_event("on_reload_window")

    def on_dark_mode(self):
        set_color_scheme(ColorScheme.Dark)
        set_theme("dark")
        self.emit_event("on_reload_window")
