from qtpy.QtWidgets import QComboBox, QLabel, QListView, QPushButton, QTableView, QTreeView

from forc2.domain.workspace import Workspace
from qtpie import Widget, new, widget


@widget
class SidebarWidget(Widget[Workspace | None]):
    the_record_label: QLabel = new(bind="The record is: {#record}")

    collections_headers: QLabel = new(bind="{name}")  # TODO: bind="name" should work
    collections_tree: QTreeView = new(
        bind="collection?.items",
        children="items",
        format="{name}",
        # selectedItem="selected_sidebar_item",
    )

    # Let's try it as a ListView...
    collections_list: QListView = new(
        bind="collection?.items",
        format="{name}",
    )

    # Let's try it as a TableView:
    collections_table: QTableView = new(
        bind="collection?.items",
    )

    collection_items_count_label: QLabel = new(bind="Items: {len(collection?.items) if collection is not None else 0}")

    environments_headers: QLabel = new("Environment")
    environments_chooser: QComboBox = new(
        bind="environments",
        format="{name}",
        # selectedItem="workspace?.active_environment",
        selectedText="active_environment_name",
    )

    btn_test: QPushButton = new("Test Button", clicked="{print(selected_sidebar_item)}")

    # The old one:
    #
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
