from qtpy.QtWidgets import QLabel, QTreeView

from qtpie import Widget, new, widget


@widget
class CollectionsTreeWidget(Widget):
    _header: QLabel = new(bind="{workspace?.name}")

    # TODO: expand=True and have it expandAll() whenever the workspace changes
    _treeview: QTreeView = new(bind="workspace.collections", children="items", format="{name}", selectedItem="selected_collection_item", headerHidden=True)
