import os
import re
from dataclasses import dataclass
from re import Match

from qtpie.files import write_file
from qtpy.QtCore import QFileSystemWatcher
from qtpy.QtWidgets import QApplication
from scss import Compiler


@dataclass
class StyleConfiguration:
    watch: bool = False
    scss_path: str | None = None
    qss_path: str | None = None
    qss_resource_path: str | None = None
    watch_folders: list[str] | None = None


@dataclass
class StylesheetWatcher:
    app: QApplication
    config: StyleConfiguration
    _qss_watcher: QFileSystemWatcher = QFileSystemWatcher()
    _main_scss_folder_path: str = ""

    def __post_init__(self):
        if not self.config.scss_path or not self.config.qss_path:
            raise ValueError(
                "Both main_scss_path and out_qss_path must be provided in the configuration."
            )
        abs_main_scss_path = os.path.abspath(self.config.scss_path)
        self._main_scss_folder_path = os.path.dirname(abs_main_scss_path)
        self._qss_watcher.fileChanged.connect(self._on_file_change)
        if self.config.watch_folders:
            self._qss_watcher.directoryChanged.connect(self._on_file_change)
            for folder in self.config.watch_folders:
                self._qss_watcher.addPath(folder)
        self._qss_watcher.addPath(abs_main_scss_path)
        self._on_file_change()

    def _on_file_change(self):
        if not self.config.scss_path or not self.config.qss_path:
            return

        print(f"Rebuilding {self.config.qss_path}")
        qss = self._rebuild_qss()
        write_file(self.config.qss_path, qss)
        self.app.setStyleSheet(qss)

    def _rebuild_qss(self) -> str:
        def attribute_name_replacer(match: Match[str]) -> str:
            content = match.group(1).replace("data-", "").replace("-", "_")
            return f"[{content}="

        compiler = Compiler(search_path=[self._main_scss_folder_path])
        qss_output: str = compiler.compile(self.config.scss_path)
        qss_output = re.sub(r"\[([^\]]+)=", attribute_name_replacer, qss_output)
        qss_output = f"/* Generated File - DO NOT EDIT */\n\n{qss_output}"

        return qss_output


stylesheet_watcher: StylesheetWatcher | None = None


def watch_qss(
    app: QApplication,
    config: StyleConfiguration,
) -> None:
    if config.watch:
        print("Watching SCSS files for changes...")
        print(f"Main SCSS Path: {config.scss_path}")
        print(f"Output QSS Path: {config.qss_path}")
        if config.watch_folders:
            print(f"Additional Watch Folders: {config.watch_folders}")

        global stylesheet_watcher
        stylesheet_watcher = StylesheetWatcher(app, config)
