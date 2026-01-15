from qtpy.QtCore import Signal

from forc.app.menus import FileMenu, ViewMenu
from forc.app.widgets.layout import SidebarWidget
from forc.app.widgets.requests import RequestWidget
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
    size=(1600, 900),
)
class ForcWindow(Window):
    ### Signals ###
    collection_item_clicked = Signal(Request)

    ### Variables ###
    _selected_request_index: Variable[int]

    ### Menus ###
    _file_menu: FileMenu = new()
    _view_menu: ViewMenu = new()

    ### Docks / Widgets ###
    _sidebar: Dock[SidebarWidget] = new(dock="left", title="Explorer")(maximumWidth=400)
    _editors: Variable[list[Request], Dock[RequestWidget]] = new(
        group="requests",
        dock="right",
        title="{name}",
        groupSelectedIndex="_selected_request_index",
    )

    ### Methods ###
    def on_collection_item_clicked(self, item: Request | Collection) -> None:
        if isinstance(item, Request):
            # If it's already added, then simply switch to that tab:
            for index, editor in enumerate(self._editors.value):
                if editor is item:
                    self._selected_request_index.value = index
                    return
            self._editors.append(item)
            self._selected_request_index.value = len(self._editors) - 1

    def _select_last_editor(self) -> None:
        ...
        # self._selected_request_index.value = len(self._editors) - 1
        # repeater = self._editors.widget
        # print(f"Repeater: {repeater}")
        # print(f"Items: {len(repeater._items) if repeater else 'N/A'}")
        # print(f"Obs: {repeater._selected_index_obs if repeater else 'N/A'}")
        # print(
        #     f"Callbacks: {
        #         len(repeater._selected_index_obs._callbacks) if repeater and repeater._selected_index_obs else 'N/A'
        #     }"
        # )
        # print(f"Setting to: {len(self._editors) - 1}")
        # self._selected_request_index.value = len(self._editors) - 1
        # print(f"Value after set: {self._selected_request_index.value}")
