from typing import override

from qtpy.QtCore import Signal

from forc2.app import ForcWindow
from qtpie import App, app


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

    ### Services ###
    # ...

    ### Settings ###
    # loaded_workspace_path: Setting[str | None] = new("fixtures/demo-api")

    ### Variables ###
    # workspace: Variable[Workspace | None] = new(None)
    # current_workspace_item: Variable[Collection | Request | None] = new(None)  # TODO rename!
    # current_request: Variable[Request | None] = new(None)
    # orientation: Variable[Qt.Orientation] = new(Qt.Orientation.Horizontal)  # TODO rename!

    ### Window ###
    main_window: ForcWindow

    ### Methods ###
    @override
    def on_run(self) -> None:
        self.main_window.show()

    def _on_reload_window(self) -> None:
        """Support for reloading the main window (for light mode / dark mode changes or stylesheet hard refresh)."""
        self.setQuitOnLastWindowClosed(False)
        self.main_window.close()
        self.main_window = self.build(ForcWindow)
        self.main_window.show()
        self.setQuitOnLastWindowClosed(True)
