import logging

from qtpy.QtWidgets import QLabel

from forc2.app.menus import FileMenu, ViewMenu
from forc2.app.widgets.request import RequestWidget
from forc2.app.widgets.sidebar import SidebarWidget
from forc2.domain.collection import Collection
from forc2.domain.request import Request
from qtpie import Var, Window, new, window
from qtpie.dock import Dock
from qtpie.event import Event

logger = logging.getLogger(__name__)

# TODO: Dock tabs should have a context menu with "Close other tabs", "Close tabs to the right", etc.


@window(
    title="Forc :: Free Open-source Rest Client",
    icon=":/icon.png",
    dockTabsClosable=True,
    dockTabsHideTitleBar=True,
    dockTabsMovable=True,
    dockTabsDragToUndock=True,
    size=(1600, 900),
)
class ForcWindow(Window):
    ### Events ###
    on_current_workspace_item_changed: Event

    ### Variables ###
    selected_sidebar_item: Var[Collection | Request | None] = new(None, onChange="_on_selected_sidebar_item_changed")
    selected_request: Var[Request | None] = new(None, onChange="_on_selected_request_changed")
    selected_request_index: Var[int]

    ### Menus ###
    file_menu: FileMenu
    view_menu: ViewMenu  # = new(visible="{workspace is not None}")  # TODO visible= for menus!

    label_example: QLabel = new("Forc - Free Open-source Rest Client", visible="{workspace is None}")

    # workspace_value_label: QLabel = new(bind="Workspace: {workspace}")

    ### Docks / Widgets ###
    sidebar: Dock[SidebarWidget] = new(
        dock="left",
        title="Explorer",
        hideTitleBar=True,
        visible="{workspace is not None}",
    )(maximumWidth=400)

    editors: Var[list[Request], Dock[RequestWidget]] = new(
        group="requests",
        dock="right",
        title="{name} {'*' if #widget.is_dirty else ''}",
        groupSelectedIndex="selected_request_index",
        selectedItem="selected_request",
        visible="{workspace is not None}",
    )

    ### Methods ###
    def _on_selected_sidebar_item_changed(self) -> None:
        logger.warning("--> Selected collection item changed to: %s", self.selected_sidebar_item())
        #
        item = self.selected_sidebar_item()
        if isinstance(item, Request):
            # If it's already added, then simply switch to that tab:
            for index, editor in enumerate(self.editors.value):
                if editor is item:
                    self.selected_request_index.value = index  # TODO remove .value
                    return
            # Otherwise, add a new tab:
            self.editors.append(item)
            self.selected_request_index.value = len(self.editors) - 1

    def _on_selected_request_changed(self) -> None:
        logger.warning("-----> Selected REQUEST changed to: %s", self.selected_request())
