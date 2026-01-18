from qtpy.QtWidgets import QLabel, QTreeView

from forc.domain.models import Collection, Request
from qtpie import Variable, Widget, new, widget


@widget
class CollectionsTreeWidget(Widget):
    collection_item: Variable[Collection | Request | None] = new(None)

    header: QLabel = new(
        bind="{workspace?.name}",
        stylesheet="font-size: 14pt; font-weight: bold; margin-bottom: 10px;",
    )

    treeview: QTreeView = new(
        bind="workspace.collections",
        children="items",
        format="{name}",
        selectedItem="collection_item",
        expand=True,
        headerHidden=True,
        clicked="{collection_item_clicked(collection_item)}",
    )
