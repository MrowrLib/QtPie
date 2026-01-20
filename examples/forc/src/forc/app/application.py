from pathlib import Path
from typing import override

from qtpy.QtCore import Signal

from forc.app import ForcWindow
from forc.domain.models import Collection, Request, Workspace
from forc.services import HttpClientService, WorkspaceService
from qtpie import App, Variable, app, new


@app(
    title="Forc - Free Open-source Rest Client",
    on_reload_window="_on_reload_window",
    on_save="_on_save",
)
class ForcApp(App):
    ### Signals ###
    on_reload_window = Signal()
    on_save = Signal()

    ### Services ###
    workspace_service: Variable[WorkspaceService] = new()
    http_client_service: Variable[HttpClientService] = new(workspace_service=workspace_service)

    ### Variables ###
    # settings: QSettings = new("forc", "forc")
    workspace: Variable[Workspace | None] = new(None)
    current_workspace_item: Variable[Collection | Request | None] = new(None)  # TODO rename!
    current_request: Variable[Request | None] = new(None)

    ### Window ###
    main_window: ForcWindow

    ### Methods ###
    @override
    def on_run(self) -> None:
        self.main_window.show()

    def __setup__(self) -> None:
        self.workspace = self.workspace_service().load(Path("fixtures/demo-api"))

        # check if there was a value in settings for last opened workspace:
        # last_workspace_path = self.settings.value("last_workspace_path", type=str)

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
            else:
                print("Current request is not dirty; no need to save.")
                # weird. hmm... i DID make changes ... I even know because main_window shows the * ... hmm
