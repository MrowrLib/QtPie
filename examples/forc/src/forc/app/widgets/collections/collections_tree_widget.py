from qtpy.QtWidgets import QLabel, QTreeView

from forc.domain.models import Workspace
from forc.services import WorkspaceService
from qtpie import Variable, Widget, new, widget


@widget
class CollectionsTreeWidget(Widget):
    workspace_service: Variable[WorkspaceService]
    workspace: Variable[Workspace | None]

    header: QLabel = new(bind="{workspace?.name}")
    tree: QTreeView = new(bind="workspace.collections", children="items", format="{name}", selectedItem="selected_collection_item", headerHidden=True)
