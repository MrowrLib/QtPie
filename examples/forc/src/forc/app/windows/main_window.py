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
    selected_request_index: Variable[int]

    ### Menus ###
    file_menu: FileMenu
    view_menu: ViewMenu

    ### Docks / Widgets ###
    sidebar: Dock[SidebarWidget] = new(dock="left", title="Explorer")(maximumWidth=400)
    editors: Variable[list[Request], Dock[RequestWidget]] = new(
        group="requests",
        dock="right",
        title="{name}",
        groupSelectedIndex="selected_request_index",
    )

    ### Methods ###
    def on_collection_item_clicked(self, item: Request | Collection) -> None:
        if isinstance(item, Request):
            # If it's already added, then simply switch to that tab:
            for index, editor in enumerate(self.editors.value):
                if editor is item:
                    self.selected_request_index.value = index
                    return
            # Otherwise, add a new tab:
            self.editors.append(item)
            self.selected_request_index.value = len(self.editors) - 1
