import logging
from pathlib import Path
from typing import override

from qtpy.QtWidgets import QFileDialog

# from qtpy.QtCore import Signal
from forc2.app import ForcWindow
from forc2.domain.workspace import Workspace
from qtpie import App, Event, Setting, Var, app, new

logger = logging.getLogger(__name__)


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
    ### Events ###
    on_reload_window: Event

    ### Settings ###
    loaded_workspace_path: Setting[str | None] = new("fixtures/demo-api")

    ### Variables ###
    workspace: Var[Workspace | None] = new(None)

    ### Window ###
    main_window: ForcWindow  # TODO make this a Window[Workspace | None]

    ### Methods ###
    @override
    def on_run(self) -> None:
        self.main_window.show()

    def __setup__(self) -> None:
        # Call _load_the_workspace after  seconds with QTimer to reproduce some delay for fun
        pass

        # QTimer.singleShot(2000, self._load_the_workspace)

    def _load_the_workspace(self) -> None:
        workspace_path = self.loaded_workspace_path()
        if workspace_path is not None:
            print("Loading workspace from path:", workspace_path)
            self.workspace = Workspace.load(Path(workspace_path))
            print("  -> Loaded workspace")

    def _on_reload_window(self) -> None:
        """Support for reloading the main window (for light mode / dark mode changes or stylesheet hard refresh)."""
        self.setQuitOnLastWindowClosed(False)
        self.main_window.close()
        self.main_window = self.build(ForcWindow)
        self.main_window.show()
        self.setQuitOnLastWindowClosed(True)

    # def _on_selected_sidebar_item_changed(self) -> None:
    #     logger.warning("-----> Selected Collection ITEM changed to: %s", self.selected_sidebar_item())

    # def _on_selected_request_changed(self) -> None:
    #     logger.warning("-----> Selected REQUEST changed to: %s", self.selected_request())

    ### Methods ###
    def _choose_workspace(self) -> None:
        workspace_path = self.setting("loaded_workspace_path", str, None)
        folder = QFileDialog.getExistingDirectory(
            None,
            "Select Workspace Folder",
            workspace_path or "",
        )
        if folder:
            self.emit_event("on_load_workspace", folder)
