from typing import override

from forc.app.windows import ForcWindow
from qtpie import App, app, new

from .qrc_resources import qt_resource_data

_qrc = qt_resource_data  # Prevent unused import from being removed


@app(title="Forc - Free Open-source Rest Client")
class ForcApp(App):
    main_window: ForcWindow = new(on_reload_window="on_reload_window")

    @override
    def on_run(self) -> None:
        self.main_window.show()

    def on_reload_window(self) -> None:
        """Support for reloading the main window (for light mode / dark mode changes or stylesheet hard refresh)."""
        self.setQuitOnLastWindowClosed(False)
        self.main_window.close()
        self.main_window = self.build(ForcWindow, on_reload_window="on_reload_window")
        self.main_window.show()
        self.setQuitOnLastWindowClosed(True)
