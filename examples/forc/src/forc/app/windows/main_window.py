from qtpy.QtCore import Signal

from forc.app.menus import FileMenu, ViewMenu
from forc.app.widgets.layout import SidebarWidget
from forc.app.widgets.requests import RequestEditorWidget
from forc.app.widgets.response import ResponseViewerWidget
from qtpie import Dock, Window, new, window


@window(title="Forc - Free Open-source Rest Client")  # , icon=":/icon.png")
class ForcWindow(Window):
    """Main Forc window with dock-based layout."""

    on_reload_window = Signal()

    _sidebar: Dock[SidebarWidget] = new(dock="left", title="Explorer")
    _request: RequestEditorWidget = new()
    _response: Dock[ResponseViewerWidget] = new(dock="right", title="Response")

    _file_menu: FileMenu = new()
    _view_menu: ViewMenu = new(on_reload_window="on_reload_window")
