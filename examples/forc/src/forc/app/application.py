from forc.app.menus import FileMenu
from forc.app.widgets.layout import SidebarWidget
from forc.app.widgets.requests import RequestEditorWidget
from forc.app.widgets.response import ResponseViewerWidget
from qtpie import App, Dock, app, new

from .qrc_resources import qt_resource_data

_qrc = qt_resource_data  # Prevent unused import from being removed


@app(title="Forc - Free Open-source Rest Client", icon=":/icon.png")
class ForcApp(App):
    """Main Forc application with dock-based layout."""

    _sidebar: Dock[SidebarWidget] = new(dock="left", title="Explorer")
    _request: RequestEditorWidget = new()
    _response: Dock[ResponseViewerWidget] = new(dock="right", title="Response")

    _file_menu: FileMenu = new(on_quit="quit")
