import os
import re
from dataclasses import dataclass
from re import Match
from typing import Any

import sass
from PySide6.QtCore import QFileSystemWatcher, QObject
from PySide6.QtWidgets import QApplication, QWidget

from qtpie.files import write_file


class QtStyleClass:
    @staticmethod
    def get_classes(obj: QObject) -> list[str]:
        classes = obj.property("class")
        if isinstance(classes, list):
            list_of_any: list[Any] = classes  # type: ignore
            class_names: list[str] = [str(class_name) for class_name in list_of_any]
            return class_names
        return []

    @staticmethod
    def set_classes(obj: QObject, classes: list[str]) -> None:
        obj.setProperty("class", classes)
        if isinstance(obj, QWidget):
            obj.style().unpolish(obj)
            obj.style().polish(obj)

    @staticmethod
    def add_class(obj: QObject, class_name: str) -> None:
        classes = QtStyleClass.get_classes(obj)
        if class_name not in classes:
            classes.append(class_name)
            QtStyleClass.set_classes(obj, classes)

    @staticmethod
    def add_classes(obj: QObject, class_names: list[str]) -> None:
        classes = QtStyleClass.get_classes(obj)
        for class_name in class_names:
            if class_name not in classes:
                classes.append(class_name)
        QtStyleClass.set_classes(obj, classes)

    @staticmethod
    def has_class(obj: QObject, class_name: str) -> bool:
        classes = QtStyleClass.get_classes(obj)
        return class_name in classes

    @staticmethod
    def has_any_class(obj: QObject, class_names: list[str]) -> bool:
        classes = QtStyleClass.get_classes(obj)
        for class_name in class_names:
            if class_name in classes:
                return True
        return False

    @staticmethod
    def remove_class(obj: QObject, class_name: str) -> None:
        classes = QtStyleClass.get_classes(obj)
        if class_name in classes:
            classes.remove(class_name)
            QtStyleClass.set_classes(obj, classes)

    @staticmethod
    def replace_class(obj: QObject, old_class_name: str, new_class_name: str) -> None:
        classes = QtStyleClass.get_classes(obj)
        if old_class_name in classes:
            index = classes.index(old_class_name)
            classes[index] = new_class_name
            QtStyleClass.set_classes(obj, classes)

    @staticmethod
    def toggle_class(obj: QObject, class_name: str) -> None:
        classes = QtStyleClass.get_classes(obj)
        if class_name in classes:
            classes.remove(class_name)
        else:
            classes.append(class_name)
        QtStyleClass.set_classes(obj, classes)


@dataclass
class StylesheetWatcher:
    app: QApplication
    main_scss_path: str
    out_qss_path: str
    _qss_watcher: QFileSystemWatcher = QFileSystemWatcher()
    _main_scss_folder_path: str = ""

    def __post_init__(self):
        self._main_scss_folder_path = os.path.dirname(self.main_scss_path)
        self._qss_watcher.fileChanged.connect(self._on_file_change)
        self._qss_watcher.directoryChanged.connect(self._on_file_change)
        self._update_watched_files()
        self._on_file_change()

    def _update_watched_files(self):
        print(f"Updating watched files in {self._main_scss_folder_path}")

        # Remove all paths; we'll re-add the current directory contents
        for path in self._qss_watcher.files() + self._qss_watcher.directories():
            self._qss_watcher.removePath(path)

        # Add the directory itself to watch for new files or directories
        self._qss_watcher.addPath(self._main_scss_folder_path)

        # Add all files in the directory to the watcher
        for filename in os.listdir(self._main_scss_folder_path):
            full_path = os.path.join(self._main_scss_folder_path, filename)
            if os.path.isfile(full_path):
                self._qss_watcher.addPath(full_path)

    def _on_file_change(self):
        print(f"Rebuilding {self.out_qss_path}")
        qss = self._rebuild_qss()
        write_file(self.out_qss_path, qss)
        self.app.setStyleSheet(qss)

    def _rebuild_qss(self) -> str:
        def attribute_name_replacer(match: Match[str]) -> str:
            content = match.group(1).replace("data-", "").replace("-", "_")
            return f"[{content}="

        qss_output: str = sass.compile(filename=self.main_scss_path, include_paths=[self._main_scss_folder_path])
        qss_output = re.sub(r"\[([^\]]+)=", attribute_name_replacer, qss_output)
        qss_output = f"/* Generated File - DO NOT EDIT */\n\n{qss_output}"

        return qss_output


stylesheet_watcher: StylesheetWatcher | None = None


def watch_qss(app: QApplication, main_scss: str, out_qss: str) -> None:
    print(f"Watching {main_scss} and writing to {out_qss}")

    if not os.path.exists(main_scss):
        raise FileNotFoundError(f"Could not find file {main_scss}. Current directory: {os.getcwd()}")

    global stylesheet_watcher
    stylesheet_watcher = StylesheetWatcher(app, main_scss, out_qss)
