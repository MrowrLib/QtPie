from pathlib import Path
from typing import override

from qtpy.QtCore import Signal

from forc.app.windows import ForcWindow
from forc.domain.models import Workspace
from forc.services import HttpClientService, WorkspaceService
from qtpie import App, Variable, app, new


@app(title="Forc - Free Open-source Rest Client", on_reload_window="_on_reload_window")
class ForcApp(App):
    ### Signals ###
    on_reload_window = Signal()

    ### Services / Variables ###
    workspace_service: Variable[WorkspaceService] = new()
    workspace: Variable[Workspace | None] = new(None)
    http_client_service: Variable[HttpClientService] = new(workspace_service=workspace_service)

    ### Window ###
    main_window: ForcWindow = new()

    ### Methods ###
    @override
    def on_run(self) -> None:
        self.main_window.show()

    def __setup__(self) -> None:
        self.workspace = self.workspace_service.value.load(Path("fixtures/demo-api"))

    def _on_reload_window(self) -> None:
        """Support for reloading the main window (for light mode / dark mode changes or stylesheet hard refresh)."""
        self.setQuitOnLastWindowClosed(False)
        self.main_window.close()
        self.main_window = self.build(ForcWindow)
        self.main_window.show()
        self.setQuitOnLastWindowClosed(True)
