from qtpy.QtWidgets import QComboBox, QLabel, QPushButton, QTreeView

from qtpie import Widget, new, widget


@widget
class Sidebar(Widget):
    collections_headers: QLabel = new(bind="workspace?.name")
    collections_tree: QTreeView = new(
        bind="workspace?.collection?.items",
        children="items",
        format="{name}",
        selectedItem="selected_sidebar_item",
    )

    environments_headers: QLabel = new("Environment")
    environments_chooser: QComboBox = new(
        bind="workspace?.environments",
        format="{name}",
        selectedText="workspace?.active_environment_name",
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
