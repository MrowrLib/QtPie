from pathlib import Path
from typing import override

from qtpy.QtWidgets import QFileDialog

# from qtpy.QtCore import Signal
from forc2.app import ForcWindow
from forc2.domain.workspace import Workspace
from qtpie import App, Event, Setting, Var, app, new


@app(
    app_name="Forc",
    org="MrowrPurr",
    title="Forc :: Free Open-source Rest Client",
    icon=":/icon.png",
)
class ForcApp(App):
    ### Events ###
    on_quit: Event = new(on="quit")
    on_reload_window: Event = new(on="_on_reload_window")
    on_choose_workspace: Event = new(on="_on_choose_workspace")
    on_load_workspace: Event[str] = new(on="_on_load_workspace")

    ### Settings ###
    loaded_workspace_path: Setting[str | None] = new("fixtures/demo-api")

    ### Variables ###
    workspace: Var[Workspace | None] = new(None)

    ### Window ###
    main_window: ForcWindow = new(bind="workspace")

    ### Methods ###
    @override
    def on_run(self) -> None:
        self.main_window.show()

    def __setup__(self) -> None:
        workspace_path = self.loaded_workspace_path()
        if workspace_path is not None:
            self._on_load_workspace(workspace_path)

    ### Methods ###
    def _on_reload_window(self) -> None:
        # Support for reloading the main window (for light mode / dark mode changes or stylesheet hard refresh).
        self.setQuitOnLastWindowClosed(False)
        self.main_window.close()
        self.main_window = self.build(ForcWindow)
        self.main_window.show()
        self.setQuitOnLastWindowClosed(True)

    def _on_choose_workspace(self) -> None:
        workspace_path = self.loaded_workspace_path()
        folder = QFileDialog.getExistingDirectory(self.main_window, "Select Workspace Folder", str(workspace_path) or "")
        if folder:
            self.on_load_workspace.emit(folder)

    def _on_load_workspace(self, folder: str) -> None:
        self.workspace = Workspace.load(Path(folder))
        self.loaded_workspace_path = folder
