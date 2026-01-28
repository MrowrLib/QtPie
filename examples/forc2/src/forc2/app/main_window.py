from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLabel, QPushButton

from forc2.app.menus import FileMenu, ViewMenu
from forc2.app.widgets import RequestWidget, SidebarWidget
from forc2.domain import Request, TreeItem, Workspace
from forc2.domain.collection import Collection
from qtpie import Dock, Stretch, Var, Widget, Window, new, widget, window

# Can we let people define their own things like ... header: Heading1 = new("...") ? <---- this would be really nice to have, really really nice to have!
#
# @widget_alias
# class MyWidgetAlias(WidgetAlias):
#     content: QLabel = new("This is a widget alias example.")


# TODO add _
@widget
class CentralWidget(Widget[Workspace | None]):
    app_header_label: QLabel = new("Forc - Free Open-source Rest Client", classes=["h1"])
    load_workspace_message: QLabel = new("No workspace loaded. Please load a workspace to get started.", visible="{#record is None}")
    load_workspace_button: QPushButton = new("Load Workspace", clicked="on_choose_workspace", visible="{#record is None}")
    label_if_workspace_loaded: QLabel = new("Workspace loaded. Please select or create a request to get started.", visible="{#record is not None}", classes=["italic"])
    stretch: Stretch


# TODO add _
@window(
    size=(1920, 1080),
    center=True,
    dockTabsClosable=True,
    dockTabsHideTitleBar=True,
    dockTabsMovable=True,
    dockTabsDragToUndock=True,
    dockMaximizeFloatingOnDoubleClick=True,
)
class MainWindow(Window[Workspace | None]):
    ### Menus ###
    file_menu: FileMenu
    view_menu: ViewMenu = new(visible="{#record is not None}")

    ### Variables ###
    # TODO: make 'public' ones for DI not have _ and make the private ones start with _
    request_splitter_orientation: Var[Qt.Orientation] = new(Qt.Orientation.Vertical)
    # request_splitter_orientation: Var[Qt.Orientation] = new(Qt.Orientation.Horizontal)
    selected_sidebar_item: Var[TreeItem | None] = new(None, onChange="_on_selected_sidebar_item_changed")
    selected_collection: Var[Collection | None] = new(None)
    current_request: Var[Request | None]
    selected_request_index: Var[int]

    ### Docks ###
    sidebar_dock: Dock[SidebarWidget] = new(
        dock="left",
        title="Explorer",
        hideTitleBar=True,
        visible="{#record is not None}",
        width=0.25,
    )
    editor_docked_tabs: Var[list[Request], Dock[RequestWidget]] = new(
        group="requests",
        dock="right",
        title="{name} {'*' if #widget.is_dirty else ''}",
        groupSelectedIndex="selected_request_index",
        selectedItem="selected_request",
        visible="{workspace is not None}",
        width=0.75,
    )

    ### Widgets ###
    central_widget: CentralWidget = new(visible="{workspace is None or len(editor_docked_tabs) == 0}")

    ### Methods ###
    def _on_selected_sidebar_item_changed(self) -> None:
        item = self.selected_sidebar_item()
        print("Selected sidebar item changed:", item.name if item else None)

        if item is None:
            self.selected_collection = None  # <--- this causes recursion
        elif isinstance(item, Collection):
            self.selected_collection = item
        else:
            self.selected_collection = item.collection
            # If it's already added, then simply switch to that tab:
            for index, editor in enumerate(self.editor_docked_tabs()):
                if editor is item:
                    self.selected_request_index = index
                    return
            # Otherwise, add a new tab:
            self.editor_docked_tabs.append(item)
            self.selected_request_index = len(self.editor_docked_tabs) - 1

        # Debug the lost of editor tabs:
        print("Current editor tabs:")
        for index, editor in enumerate(self.editor_docked_tabs()):
            print(f" Tab {index}: {editor.name}")
