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
    dockTabsClosable=True,
    dockTabsHideTitleBar=True,
    dockTabsMovable=True,
    dockTabsDragToUndock=True,
    size=(1920, 1080),
)
class ForcWindow(Window):
    ### Signals ###
    collection_item_clicked = Signal(Request)

    ### Menus ###
    _file_menu: FileMenu = new()
    _view_menu: ViewMenu = new()

    ### Docks / Widgets ###
    _sidebar: Dock[SidebarWidget] = new(dock="left", title="Explorer")
    _editors: Variable[list[Request], Dock[RequestEditorWidget]] = new(group="requests", dock="right", title="{name}")
    _response: Dock[ResponseViewerWidget] = new(dock="bottom", title="Response")

    ### Methods ###
    def on_collection_item_clicked(self, item: Request | Collection) -> None:
        if isinstance(item, Request):
            for editor in self._editors:
                if editor == item:
                    self._editors.remove(editor)
                    return
            self._editors.append(item)
