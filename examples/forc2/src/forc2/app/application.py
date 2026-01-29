from pathlib import Path
from typing import override

from qtpy.QtWidgets import QFileDialog

from forc2.app import MainWindow
from forc2.domain import Request, Workspace
from qtpie import App, Event, Setting, Var, app, new


@app(app_name="Forc", org="MrowrPurr", title="Forc :: Free Open-source Rest Client", icon=":/icon.png")
class Application(App):
    ### Events ###
    on_save: Event = new(on="_on_save")
    on_quit: Event = new(on="quit")
    on_reload_window: Event = new(on="_on_reload_window")
    on_choose_workspace: Event = new(on="_on_choose_workspace")
    on_load_workspace: Event[str] = new(on="_on_load_workspace")

    ### Settings ###
    loaded_workspace_path: Setting[str | None] = new("fixtures/demo-api")

    ### Variables ###
    workspace: Var[Workspace | None] = new(None)
    selected_request: Var[Request | None]

    ### Window ###
    main_window: MainWindow = new(bind="workspace")

    ### Methods ###
    @override
    def on_run(self) -> None:
        self.main_window.show()

    def __setup__(self) -> None:
        workspace_path = self.loaded_workspace_path()
        if workspace_path is not None:
            self._on_load_workspace(workspace_path)

    ### Methods ###
    def _on_save(self) -> None:
        if self.selected_request.value is not None:
            self.selected_request.value.save()

    def _on_reload_window(self) -> None:
        # Support for reloading the main window (for light mode / dark mode changes or stylesheet hard refresh).
        self.setQuitOnLastWindowClosed(False)
        self.main_window.close()
        self.main_window = self.build(MainWindow)
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
