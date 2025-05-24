from dataclasses import dataclass, field
from typing import Callable, ParamSpec, TypeVar

from qtpy.QtCore import QObject
from qtpy.QtWidgets import QLabel, QWidget

T = TypeVar("T", covariant=True)
P = ParamSpec("P")


# note: could use field metadata to store options


@dataclass(frozen=True)
class WidgetFactoryOptions:
    object_name: str | None = None
    class_names: list[str] | None = None
    form_field_label: str | None = None
    grid_position: tuple[int, int] | None = None


def make(class_type: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    def factory_fn() -> T:
        return class_type(*args, **kwargs)

    return field(default_factory=factory_fn)


def form_row(label: str, class_type: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    """
    Concise version like `make()`: no widget_options required.
    Adds 'form_field_name' to any QWidget created.
    """

    def factory_fn() -> T:
        widget = class_type(*args, **kwargs)
        if isinstance(widget, QObject):
            widget.setProperty("_widget_factory_options", WidgetFactoryOptions(form_field_label=label))
        return widget

    return field(default_factory=factory_fn)


def grid_item(position: tuple[int, int], class_type: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    """
    Concise version like `make()`: no widget_options required.
    Adds 'form_field_name' to any QWidget created.
    """

    def factory_fn() -> T:
        widget = class_type(*args, **kwargs)
        if isinstance(widget, QObject):
            widget.setProperty("_widget_factory_options", WidgetFactoryOptions(grid_position=position))
        return widget

    return field(default_factory=factory_fn)


@dataclass
class SimpleDataclassWidget(QWidget):
    # Regular field() factory for widgets when using QBoxLayout (QVBoxLayout, QHBoxLayout)
    label1: QLabel = make(QLabel, "Hello, World!")
    label2: QLabel = make(QLabel, "This is a QLabel in a dataclass widget")

    # But the QFormLayout requires a different approach
    form_item1: QLabel = form_row("Form Label", QLabel, "This is a QLabel in a form row")
    form_item2: QLabel = form_row("Another Form Label", QLabel, "This is another QLabel in a form row")

    # For QGridLayout, we can use grid_item
    grid_item1: QLabel = grid_item((0, 0), QLabel, "This is a QLabel in a grid item")
    grid_item2: QLabel = grid_item((1, 0), QLabel, "This is another QLabel in a grid item")
