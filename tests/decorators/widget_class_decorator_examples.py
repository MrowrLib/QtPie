from qtpy.QtWidgets import QWidget

from qtpie.decorators.widget import widget_class


@widget_class
class SimpleWidgetClass(QWidget):
    def __init__(self, value: int = 42) -> None:
        self.value = value


@widget_class
class MultiArgWidgetClass(QWidget):
    def __init__(self, name: str, count: int) -> None:
        self.name = name
        self.count = count


@widget_class
class NamedWidgetClass(QWidget):
    def __init__(self, name: str = "CustomWidgetName") -> None:
        self.name = name
