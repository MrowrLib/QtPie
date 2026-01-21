from pathlib import Path
from typing import override

from qtpy.QtCore import Qt, Signal

from forc.app import ForcWindow
from forc.domain.models import Collection, Request, Workspace
from forc.services import EnvironmentsService, HttpClientService, WorkspaceService
from qtpie import App, Variable, app, new
from qtpie.setting import Setting


@app(
    app_name="Forc",
    org="MrowrPurr",
    title="Forc - Free Open-source Rest Client",
    on_reload_window="_on_reload_window",
    on_save="_on_save",
    on_load_workspace="_on_load_workspace",
    on_toggle_splitter_orientation="_on_toggle_splitter_orientation",
)
class ForcApp(App):
    ### Signals ###
    on_reload_window = Signal()
    on_save = Signal()  # saves current request if dirty
    on_load_workspace = Signal(str)
    on_toggle_splitter_orientation = Signal()

    ### Services ###
    environments_service: Variable[EnvironmentsService] = new()
    workspace_service: Variable[WorkspaceService] = new(environments=environments_service)
    http_client_service: Variable[HttpClientService] = new(workspace_service=workspace_service)

    ### Settings ###
    loaded_workspace_path: Setting[str | None] = new("fixtures/demo-api")

    ### Variables ###
    workspace: Variable[Workspace | None] = new(None)
    current_workspace_item: Variable[Collection | Request | None] = new(None)  # TODO rename!
    current_request: Variable[Request | None] = new(None)
    orientation: Variable[Qt.Orientation] = new(Qt.Orientation.Horizontal)  # TODO rename!

    ### Window ###
    main_window: ForcWindow

    ### Methods ###
    @override
    def on_run(self) -> None:
        self.main_window.show()

    def __setup__(self) -> None:
        last_workspace_path = self.loaded_workspace_path()
        if last_workspace_path is not None:
            self.workspace = self.workspace_service().load(Path(last_workspace_path))

    def _on_reload_window(self) -> None:
        """Support for reloading the main window (for light mode / dark mode changes or stylesheet hard refresh)."""
        self.setQuitOnLastWindowClosed(False)
        self.main_window.close()
        self.main_window = self.build(ForcWindow)
        self.main_window.show()
        self.setQuitOnLastWindowClosed(True)

    def _on_save(self) -> None:
        if self.current_request:
            if self.current_request.is_dirty:
                print("Signal: Save workspace.")
                request = self.current_request()
                print(f"Current request to save: {request}")
                workspace = self.workspace()
                if request is not None and workspace is not None:
                    print(f"Saving request '{request.name}' to workspace '{workspace.name}'.")
                    self.workspace_service().save_request(request)
                    print("Request saved.")
                    self.current_request.reset_dirty()

    def _on_load_workspace(self, workspace_path: str) -> None:
        print(f"Signal: Change workspace to path '{workspace_path}'.")
        workspace = self.workspace_service().load(Path(workspace_path))
        self.workspace = workspace
        self.loaded_workspace_path = workspace_path
        print(f"Workspace changed to '{workspace.name}'.")

    def _on_toggle_splitter_orientation(self) -> None:
        if self.orientation() == Qt.Orientation.Horizontal:
            self.orientation = Qt.Orientation.Vertical
        else:
            self.orientation = Qt.Orientation.Horizontal
