from qtpy.QtGui import QAction

from qtpie import ColorScheme, Menu, Separator, Var, menu, new, set_color_scheme, set_theme, set_zoom


@menu(title="View")
class ViewMenu(Menu):
    ### Variables ###
    scale_factor: Var[float] = new(1.0, onChange="_on_scale_factor_changed")

    ### Actions ###
    _light_mode: QAction = new("Switch to Light Mode", triggered="_on_light_mode")
    _dark_mode: QAction = new("Switch to Dark Mode", triggered="_on_dark_mode")
    _________: Separator
    _zoom_in: QAction = new("Zoom In", shortcut="Ctrl+Shift+=", triggered="_on_zoom_in")
    _zoom_out: QAction = new("Zoom Out", shortcut="Ctrl+Shift+-", triggered="_on_zoom_out")

    def _on_light_mode(self):
        set_color_scheme(ColorScheme.Light)
        set_theme("light")
        self.emit_event("on_reload_window")

    def _on_dark_mode(self):
        set_color_scheme(ColorScheme.Dark)
        set_theme("dark")
        self.emit_event("on_reload_window")

    ### Methods ###
    def _on_zoom_in(self) -> None:
        self.scale_factor *= 1.1
        print(self.scale_factor)

    def _on_zoom_out(self) -> None:
        self.scale_factor /= 1.1
        print(self.scale_factor)

    def _on_scale_factor_changed(self, new_value: float) -> None:
        set_zoom(new_value)
