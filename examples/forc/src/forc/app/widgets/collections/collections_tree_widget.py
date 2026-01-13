from qtpy.QtWidgets import QLabel, QPushButton

from forc.domain.models import Workspace
from forc.services import WorkspaceService
from qtpie import Variable, Widget, new, widget


@widget
class CollectionsTreeWidget(Widget):
    """Tree view of collections and requests."""

    workspace_service: Variable[WorkspaceService]
    workspace: Variable[Workspace | None]

    _placeholder: QLabel = new(bind="Collections Tree Placeholder for {workspace.name}")

    btn_check_workspace_value: QPushButton = new("Check Workspace Value", clicked="on_check_workspace_value")

    def __setup__(self) -> None:
        if self.workspace.value is None:
            print("No workspace loaded; collections tree will be empty.")
        else:
            print(f"Loaded workspace: {self.workspace.value.name}")

    def on_check_workspace_value(self) -> None:
        if self.workspace.value is None:
            print("Workspace is currently None.")
        else:
            print(f"Workspace is loaded: {self.workspace.value.name}")
