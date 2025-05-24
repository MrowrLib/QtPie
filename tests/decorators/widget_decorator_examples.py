from qtpy.QtWidgets import QWidget

from qtpie.decorators.widget import widget


@widget
class SimpleWidget(QWidget):
    value: int = 42


@widget
class MultiFieldWidget(QWidget):
    name: str = "default"
    count: int = 0


@widget
class LayoutWidget(QWidget):
    layout_mode: str = "vertical"


@widget
class NamedWidget(QWidget):
    name: str = "CustomWidgetName"
