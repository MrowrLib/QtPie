import os

from qtpy.QtWidgets import QApplication

from qtpie.startup import run_app
from qtpie.styles.stylesheet import StyleConfiguration


class App(QApplication):
    def __init__(
        self,
        name: str = "Application",
        version: str = "1.0.0",
        light_mode: bool = False,
        dark_mode: bool = False,
        styles: StyleConfiguration | None = None,
        *args: list[str],
        **kwargs: dict[str, object],
    ) -> None:
        if light_mode is True:
            os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=0"
        elif dark_mode is True:
            os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"

        super().__init__(*args, *kwargs)

        self.setApplicationName(name)
        self.setApplicationVersion(version)

        self._styles = styles or StyleConfiguration()

    def set_styles(
        self,
        watch: bool = False,
        scss_path: str | None = None,
        qss_path: str | None = None,
        qss_resource: str | None = None,
        watch_folders: list[str] | None = None,
    ) -> None:
        self._styles = StyleConfiguration(
            watch=watch,
            scss_path=scss_path,
            qss_path=qss_path,
            qss_resource_path=qss_resource,
            watch_folders=watch_folders,
        )

    def run(self) -> None:
        run_app(self, styles=self._styles)
