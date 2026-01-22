from qtpy.QtCore import Signal
from qtpy.QtWidgets import QComboBox, QLabel, QListView, QTableView, QTreeView

from forc2.app.menus import FileMenu, ViewMenu
from qtpie import Window, new, window

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

    collections_headers: QLabel = new("Collections")
    collections_tree: QTreeView = new(
        bind="workspace?.collection?.items",
        children="items",
        format="{name}",
    )

    environments_headers: QLabel = new("Environments (ComboBox)")
    environments_chooser: QComboBox = new(
        bind="workspace?.environments",
        format="{name}",
        selectedText="workspace?.active_environment_name",
    )

    environments_headers2: QLabel = new("Environments (List)")
    environments_chooser2: QListView = new(
        bind="workspace?.environments",
        format="{name}",
        selectedText="workspace?.active_environment_name",
    )

    # Environment Variables table:
    environment_variables_headers: QLabel = new("Environment Variables")

    # When you change the active environment, this DOES NOT UPDATE:
    environment_variables_table: QTableView = new(
        bind="workspace?.active_environment?.variables",
        # key_column_name="Something Custom"
        # should just replace the hard-coded "Key" - for when it defaults to Key and Value
        # OR when it auto-detects but still uses 'Key'
        # value_column_name="Also custom",
        # should just replace the hard-coded "Value" - for when it defaults to Key and Value
    )

    #
    # columns={"#key": "Name", "value": "Value", "enabled": "Enabled", "secret": "Secret"},

    # When you change the active environment, this updates properly:
    env_vars_count_label: QLabel = new(
        bind="Number of variables: {len(workspace?.active_environment?.variables) "
        "if workspace?.active_environment?.variables else 0}"
    )

    # When you change the active environment, this updates properly:
    env_vars_label: QLabel = new(bind="workspace?.active_environment?.variables")

    # environment_as_table_label: QLabel = new("Environment as TableView:")
    # environment_as_table: QTableView = new(bind="workspace?.active_environment")

    # workspace_as_table_label: QLabel = new("Workspace as TableView:")
    # workspace_as_table: QTableView = new(bind="workspace")


#  treeview: QTreeView = new(
#         bind="workspace.collections",
#         children="items",
#         selectedItem="current_workspace_item",
#         expand=True,
#         headerHidden=True,
#         validator=filename_safe_validator,
#         clicked="{on_current_workspace_item_changed()}",
#         widget=CollectionsTreeWidgetRow,
#         onEnterKey="_on_enter_key",
#         onDeleteKey="_on_delete_key",
#         selectedWidget="current_tree_widget_row",
#     )


# TODO: Dock tabs should close on middle-click by default.
# TODO: Dock tabs should have a context menu with "Close other tabs", "Close tabs to the right", etc.
### Docks / Widgets ###
# sidebar: Dock[SidebarWidget] = new(dock="left", title="Explorer", hideTitleBar=True)(maximumWidth=400)
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
