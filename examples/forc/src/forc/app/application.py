from pathlib import Path
from typing import override

from forc.app.windows import ForcWindow
from forc.domain.models import Workspace
from forc.services import WorkspaceService
from qtpie import App, Variable, app, new

from .qrc_resources import qt_resource_data

_qrc = qt_resource_data  # Prevent unused import from being removed


@app(title="Forc - Free Open-source Rest Client")
class ForcApp(App):
    workspace_service: Variable[WorkspaceService] = new()
    workspace: Variable[Workspace | None] = new(None)

    main_window: ForcWindow = new(on_reload_window="on_reload_window")

    @override
    def on_run(self) -> None:
        self.main_window.show()

    def on_reload_window(self) -> None:
        """Support for reloading the main window (for light mode / dark mode changes or stylesheet hard refresh)."""
        self.setQuitOnLastWindowClosed(False)
        self.main_window.close()
        self.main_window = self.build(ForcWindow, workspace_service=self.workspace_service, on_reload_window="on_reload_window")
        self.main_window.show()
        self.setQuitOnLastWindowClosed(True)

    def __setup__(self) -> None:
        self.workspace = self.workspace_service.value.load(Path("fixtures/demo-api"))
        print(self.workspace.value)
