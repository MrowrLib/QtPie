from pathlib import Path
from typing import override

from qtpy.QtCore import Signal

from forc.app.windows import ForcWindow
from forc.domain.models import Workspace
from forc.services import WorkspaceService
from qtpie import App, Variable, app, new

from .qrc_resources import qt_resource_data

_qrc = qt_resource_data  # Prevent unused import from being removed


@app(title="Forc - Free Open-source Rest Client", on_reload_window="_on_reload_window")
class ForcApp(App):
    on_reload_window = Signal()

    workspace_service: Variable[WorkspaceService] = new()
    workspace: Variable[Workspace | None] = new(None)

    main_window: ForcWindow = new()

    @override
    def on_run(self) -> None:
        self.main_window.show()

    def _on_reload_window(self) -> None:
        """Support for reloading the main window (for light mode / dark mode changes or stylesheet hard refresh)."""
        print("CALLED RELOAD WINDOW")
        self.setQuitOnLastWindowClosed(False)
        self.main_window.close()
        self.main_window = self.build(ForcWindow)
        self.main_window.show()
        self.setQuitOnLastWindowClosed(True)

    def __setup__(self) -> None:
        self.workspace = self.workspace_service.value.load(Path("fixtures/demo-api"))
        print(self.workspace.value)

        # Hook up the signal connection here, for now. then let's find a nice DSL way to do this in qtpie
        #
        # Ok, now it's time to do this!
        #
        # Let's do it via @app() .... so like @app(on_reload_window="_on_reload_window")
        # self.on_reload_window.connect(self._on_reload_window)
