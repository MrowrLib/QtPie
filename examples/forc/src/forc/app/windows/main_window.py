from qtpy.QtCore import Signal

from forc.app.menus import FileMenu, ViewMenu
from forc.app.widgets.layout import SidebarWidget
from forc.app.widgets.requests import RequestEditorWidget
from forc.app.widgets.response import ResponseViewerWidget
from forc.domain.models.core import Workspace
from forc.services import WorkspaceService
from qtpie import Dock, Variable, Window, new, window


@window(title="Forc :: Free Open-source Rest Client", icon=":/icon.png")
class ForcWindow(Window):
    workspace_service: Variable[WorkspaceService]
    workspace: Variable[Workspace | None]

    on_reload_window = Signal()

    _request: RequestEditorWidget = new()

    _sidebar: Dock[SidebarWidget] = new(dock="left", title="Explorer")
    _response: Dock[ResponseViewerWidget] = new(dock="right", title="Response")

    _file_menu: FileMenu = new()
    _view_menu: ViewMenu = new(on_reload_window="on_reload_window")
