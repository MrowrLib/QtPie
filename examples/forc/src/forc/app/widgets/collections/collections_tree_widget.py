from qtpy.QtWidgets import QLabel, QTreeView

from qtpie import Widget, new, widget


@widget
class CollectionsTreeWidget(Widget):
    _header: QLabel = new(bind="{workspace?.name}", stylesheet="font-size: 14pt; font-weight: bold; margin-bottom: 10px;")
    _treeview: QTreeView = new(bind="workspace.collections", children="items", format="{name}", selectedItem="selected_collection_item", expand=True, headerHidden=True)
