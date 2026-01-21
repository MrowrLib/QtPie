from qtpy.QtCore import Signal
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QFileDialog

from qtpie import Menu, menu, new


@menu(title="File")
class FileMenu(Menu):
    ### Signals ###
    on_quit = Signal()

    ### Actions ###
    load_workspace: QAction = new("&Load Workspace...", shortcut="Ctrl+O", triggered="_choose_workspace")
    save: QAction = new("&Save", shortcut="Ctrl+S", triggered="on_save")
    quit: QAction = new("&Quit", shortcut="Ctrl+Q", triggered="on_quit")

    ### Methods ###
    def _choose_workspace(self) -> None:
        workspace_path = self.setting("loaded_workspace_path", str, None)
        if workspace_path is not None:
            print(f"Existing workspace path: {workspace_path}")
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Workspace Folder",
            workspace_path or "",
        )
        if folder:
            self.emit_signal("on_load_workspace", folder)
