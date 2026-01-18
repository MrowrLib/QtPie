from qtpy.QtWidgets import QLabel, QTreeView

from qtpie import Widget, new, widget


@widget
class CollectionsTreeWidget(Widget):
    header: QLabel = new(
        bind="{workspace?.name}",
        stylesheet="font-size: 14pt; font-weight: bold; margin-bottom: 10px;",
    )

    treeview: QTreeView = new(
        bind="workspace.collections",
        children="items",
        format="{name}",
        selectedItem="current_workspace_item",
        expand=True,
        headerHidden=True,
        clicked="{on_current_workspace_item_changed()}",
    )
