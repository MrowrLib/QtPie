from typing import Any

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget


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
