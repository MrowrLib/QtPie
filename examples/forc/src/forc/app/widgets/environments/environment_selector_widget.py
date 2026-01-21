from qtpy.QtWidgets import QComboBox, QLabel, QPushButton, QSizePolicy, QToolButton

from forc.domain.models.core import Workspace
from forc.services.workspace import WorkspaceService
from qtpie import Variable, Widget, new, widget


@widget(layout="horizontal")
class EnvironmentSelectorWidget(Widget):
    ### Services ###
    # environments_service: Variable[EnvironmentsService]
    workspace_service: Variable[WorkspaceService]
    workspace: Variable[Workspace | None]

    ### Widgets ###
    label: QLabel = new("Environment:")
    environments_chooser: QComboBox = new(
        bind="workspace.environments",
        format="{name}",
        selectedItem="workspace?.active_environment",
        sizePolicy=QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed),
    )
    test_button: QPushButton = new("Print the active environment", clicked="_on_print_active_environment")

    ### Methods ###
    def _on_print_active_environment(self) -> None:
        workspace = self.workspace()
        if workspace is None:
            print("No workspace loaded.")
            return
        active_env = workspace.active_environment
        if active_env:
            print(f"Active Environment: {active_env}")
        else:
            print("No active environment set.")

    #
    settings_button: QToolButton = new(icon=":/settings-dark.svg", clicked="_on_test_clicked")

    def _on_test_clicked(self) -> None:
        print("Test button clicked!")
