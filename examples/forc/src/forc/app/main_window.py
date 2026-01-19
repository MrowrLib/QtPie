from qtpy.QtCore import Signal

from forc.app.menus import FileMenu, ViewMenu
from forc.app.widgets import RequestWidget, SidebarWidget
from forc.domain.models import Collection, Request
from qtpie import Dock, Window, new, window
from qtpie.variable import Variable


@window(
    title="Forc :: Free Open-source Rest Client",
    icon=":/icon.png",
    on_current_workspace_item_changed="_on_current_workspace_item_changed",
    dockTabsClosable=True,
    dockTabsHideTitleBar=True,
    dockTabsMovable=True,
    dockTabsDragToUndock=True,
    size=(1600, 900),
)
class ForcWindow(Window):
    ### Signals ###
    on_current_workspace_item_changed = Signal()

    ### Variables ###
    # Ah, we should rename, current_workspace_item is just in the SIDEBAR selection, not e.g. the current tab! right?
    current_workspace_item: Variable[Collection | Request | None]  # TODO later: RENAME / move me
    selected_request_index: Variable[int]

    ### Menus ###
    file_menu: FileMenu
    view_menu: ViewMenu

    # TODO: Dock tabs should close on middle-click by default.
    # TODO: Dock tabs should have a context menu with "Close other tabs", "Close tabs to the right", etc.
    ### Docks / Widgets ###
    sidebar: Dock[SidebarWidget] = new(dock="left", title="Explorer", hideTitleBar=True)(maximumWidth=400)
    editors: Variable[list[Request], Dock[RequestWidget]] = new(
        group="requests",
        dock="right",
        title="{name} {'*' if #widget.is_dirty else ''}",
        groupSelectedIndex="selected_request_index",
        selectedItem="current_request",
    )

    def _on_current_workspace_item_changed(self) -> None:
        item = self.current_workspace_item()
        if isinstance(item, Request):
            # If it's already added, then simply switch to that tab:
            for index, editor in enumerate(self.editors.value):
                if editor is item:
                    self.selected_request_index.value = index  # TODO remove .value
                    return
            # Otherwise, add a new tab:
            self.editors.append(item)
            self.selected_request_index.value = len(self.editors) - 1
