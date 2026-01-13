from typing import Any

from qtpy.QtCore import Signal

from forc.app.menus import FileMenu, ViewMenu
from forc.app.widgets.layout import SidebarWidget
from forc.app.widgets.requests import RequestEditorWidget
from forc.app.widgets.response import ResponseViewerWidget
from forc.domain.models import Collection, Request
from qtpie import Dock, Window, new, window
from qtpie.variable import Variable


@window(
    title="Forc :: Free Open-source Rest Client",
    icon=":/icon.png",
    collection_item_clicked="on_collection_item_clicked",
)
class ForcWindow(Window):
    collection_item_clicked = Signal(Request)

    collection_item: Variable[Any | None] = new(None)
    open_requests: Variable[list[Request]] = new([])

    _file_menu: FileMenu = new()
    _view_menu: ViewMenu = new()

    # finally, I want this as the final:
    # it makes 1 dock per request already
    # but does not group!
    editors: Variable[list[Request], Dock[RequestEditorWidget]] = new(group="requests", dock="right", title="{name}")

    _sidebar: Dock[SidebarWidget] = new(dock="left", title="Explorer")
    _response: Dock[ResponseViewerWidget] = new(dock="bottom", title="Response")

    def on_collection_item_clicked(self, item: Request | Collection) -> None:
        if isinstance(item, Request):
            self.editors.append(item)
