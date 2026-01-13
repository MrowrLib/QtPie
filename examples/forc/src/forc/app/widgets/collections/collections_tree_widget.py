from PySide6.QtCore import Signal
from qtpy.QtWidgets import QLabel, QTreeView

from forc.domain.models.core import Request
from qtpie import Widget, new, widget


@widget(quick_test="on_quick_test")
class CollectionsTreeWidget(Widget):
    quick_test = Signal(Request)

    _header: QLabel = new(
        bind="{workspace?.name}",
        stylesheet="font-size: 14pt; font-weight: bold; margin-bottom: 10px;",
    )

    _treeview: QTreeView = new(
        bind="workspace.collections",
        children="items",
        format="{name}",
        selectedItem="collection_item",
        expand=True,
        headerHidden=True,
        # clicked="on_collection_item_clicked",
        clicked="{quick_test(collection_item)}",
    )

    # def on_collection_item_clicked(self) -> None:
    #     self.emit_signal("collection_item_clicked")

    def on_quick_test(self, request: Request) -> None:
        print("Collection item clicked in CollectionsTreeWidget:", request)
