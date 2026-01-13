from qtpy.QtWidgets import QLabel, QTableView

from forc.domain.models import Workspace
from forc.services import WorkspaceService
from qtpie import Variable, Widget, new, widget


@widget
class CollectionsTreeWidget(Widget):
    """Tree view of collections and requests."""

    workspace_service: Variable[WorkspaceService]
    workspace: Variable[Workspace | None]

    _placeholder: QLabel = new(bind="Collections Tree Placeholder for {workspace?.name}")

    _show_collections: QTableView = new(bind="workspace.collections")
    _show_collections_labels: list[QLabel] = new(bind="workspace.collections", format="Collection: {name}")
