from qtpy.QtWidgets import QLabel, QPushButton

from forc2.app.menus import FileMenu, ViewMenu
from forc2.app.widgets.request import RequestWidget
from forc2.app.widgets.sidebar import SidebarWidget
from forc2.domain.collection import Collection
from forc2.domain.request import Request
from forc2.domain.workspace import Workspace
from qtpie import Dock, Event, Stretch, Var, Widget, Window, new, widget, window


@widget
class CentralWidget(Widget):
    app_header_label: QLabel = new("Forc - Free Open-source Rest Client")
    load_workspace_message: QLabel = new("No workspace loaded. Please load a workspace to get started.")
    load_workspace_button: QPushButton = new("Load Workspace", clicked="on_choose_workspace")
    stretch: Stretch


@window(dockTabsClosable=True, dockTabsHideTitleBar=True, dockTabsMovable=True, dockTabsDragToUndock=True, size=(1600, 900))
class ForcWindow(Window[Workspace | None]):
    ### Menus ###
    file_menu: FileMenu
    view_menu: ViewMenu = new(visible="{#record is not None}")

    ### Events ###
    on_collection_item_clicked: Event = new(on="_on_collection_item_clicked")

    ### Docks ###
    sidebar_dock: Dock[SidebarWidget] = new(dock="left", title="Explorer", hideTitleBar=True, visible="{#record is not None}")(maximumWidth=400)
    editor_docked_tabs: Var[list[Request], Dock[RequestWidget]] = new(
        group="requests",
        dock="right",
        title="{name} {'*' if #widget.is_dirty else ''}",
        groupSelectedIndex="selected_request_index",
        selectedItem="selected_request",
        visible="{workspace is not None}",
    )

    ### Widgets ###
    label: QLabel = new("Forc Main Window")
    workspace_name_label: QLabel = new(bind="Workspace is: {name}", visible="{#record is not None}")
    stretch: Stretch

    ### Methods ###
    def _on_collection_item_clicked(self) -> None:
        print("Collection item clicked!")


#####################
#####################
#####################
#####################
#####################


@window(
    dockTabsClosable=True,
    dockTabsHideTitleBar=True,
    dockTabsMovable=True,
    dockTabsDragToUndock=True,
    size=(1600, 900),
)
class ForcWindow_OneDraft(Window):
    ### Events ###
    on_current_workspace_item_changed: Event

    ### Variables ###
    selected_sidebar_item: Var[Collection | Request | None] = new(None, onChange="_on_selected_sidebar_item_changed")
    selected_request: Var[Request | None] = new(None, onChange="_on_selected_request_changed")
    selected_request_index: Var[int]

    ### Menus ###
    file_menu: FileMenu
    view_menu: ViewMenu  # = new(visible="{workspace is not None}")  # TODO visible= for menus!

    ### Central Window Widget ###
    central_widget: CentralWidget = new(visible="{workspace is None}")

    ### Docks / Widgets ###
    sidebar: Dock[SidebarWidget] = new(dock="left", title="Explorer", hideTitleBar=True)(maximumWidth=400)
    editors: Var[list[Request], Dock[RequestWidget]] = new(
        group="requests", dock="right", title="{name} {'*' if #widget.is_dirty else ''}", groupSelectedIndex="selected_request_index", selectedItem="selected_request"
    )

    ### Methods ###
    def _on_selected_sidebar_item_changed(self) -> None:
        # logger.warning("--> Selected collection item changed to: %s", self.selected_sidebar_item())
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

    # def _on_selected_request_changed(self) -> None:
    #     logger.warning("-----> Selected REQUEST changed to: %s", self.selected_request())
