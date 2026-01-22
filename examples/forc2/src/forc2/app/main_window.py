from qtpy.QtCore import Signal

from forc2.app.menus import FileMenu, ViewMenu
from forc2.app.widgets.sidebar import Sidebar
from qtpie import Window, new, window
from qtpie.dock import Dock

# @widget(layout="horizontal")
# class TestStatusBar(Widget):
#     label1: QLabel = new("Status: Ready")
#     stretch: Stretch
#     toggle_request_splitter_orientation_button: QPushButton = new(
#         "Toggle Splitter Orientation", clicked="on_toggle_splitter_orientation"
#     )
#     label2: QLabel = new("Line 1, Col 1")


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
    ### Signals ###
    on_current_workspace_item_changed = Signal()

    ### Variables ###
    # Ah, we should rename, current_workspace_item is just in the SIDEBAR selection, not e.g. the current tab! right?
    # current_workspace_item: Variable[Collection | Request | None]  # TODO later: RENAME / move me
    # selected_request_index: Variable[int]

    ### Status Bar ###
    # status_bar: TestStatusBar = new()

    ### Menus ###
    file_menu: FileMenu
    view_menu: ViewMenu

    # TODO: Dock tabs should have a context menu with "Close other tabs", "Close tabs to the right", etc.

    ### Docks / Widgets ###
    sidebar: Dock[Sidebar] = new(dock="left", title="Explorer", hideTitleBar=True)(maximumWidth=400)

    # editors: Variable[list[Request], Dock[RequestWidget]] = new(
    #     group="requests",
    #     dock="right",
    #     title="{name} {'*' if #widget.is_dirty else ''}",
    #     groupSelectedIndex="selected_request_index",
    #     selectedItem="current_request",
    # )


# def _on_current_workspace_item_changed(self) -> None:
#     item = self.current_workspace_item()
#     if isinstance(item, Request):
#         # If it's already added, then simply switch to that tab:
#         for index, editor in enumerate(self.editors.value):
#             if editor is item:
#                 self.selected_request_index.value = index  # TODO remove .value
#                 return
#         # Otherwise, add a new tab:
#         self.editors.append(item)
#         self.selected_request_index.value = len(self.editors) - 1
