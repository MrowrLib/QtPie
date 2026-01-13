from typing import Any

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QLabel

from forc.app.menus import FileMenu, ViewMenu
from forc.app.widgets.layout import SidebarWidget
from forc.app.widgets.requests import RequestEditorWidget
from forc.app.widgets.response import ResponseViewerWidget
from forc.domain.models import Request
from qtpie import Dock, Window, new, window
from qtpie.variable import Variable


@window(title="Forc :: Free Open-source Rest Client", icon=":/icon.png")
class ForcWindow(Window):
    collection_item_clicked = Signal(Request)

    collection_item: Variable[Any | None] = new(None)  # <--- I wanna store this in the state of the Window

    _request: RequestEditorWidget = new()

    _sidebar: Dock[SidebarWidget] = new(dock="left", title="Explorer")
    _response: Dock[ResponseViewerWidget] = new(dock="right", title="Response")

    _file_menu: FileMenu = new()
    _view_menu: ViewMenu = new()

    # also try it here
    item_info: QLabel = new(bind="{collection_item?.name}")
