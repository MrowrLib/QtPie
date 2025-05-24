from dataclasses import dataclass
from typing import Callable, TypeVar, cast, dataclass_transform, overload

from qtpy.QtWidgets import QFormLayout, QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from qtpie.styles.classes import add_classes
from qtpie.types.widget_layout_type import WidgetLayoutType

T = TypeVar("T", bound=type)


def _widget_impl(
    cls: T,
    name: str | None = None,
    layout: WidgetLayoutType | None = None,
    classes: list[str] | None = None,
) -> T:
    """Core widget setup logic shared by both decorators."""
    if not issubclass(cls, QWidget):
        raise TypeError(f"Widget decorator can only be applied to QWidget subclasses, got {cls.__name__}")

    orig_init = cls.__init__

    def __init__(self: QWidget, *args: object, **kwargs: object) -> None:
        if orig_init is QWidget.__init__:
            orig_init(self, *args, **kwargs)
        else:
            QWidget.__init__(self)
            orig_init(self, *args, **kwargs)
        self.setObjectName(name or type(self).__name__)

        # Set layout if specified
        if layout == "horizontal":
            self.setLayout(QHBoxLayout())
        elif layout == "vertical":
            self.setLayout(QVBoxLayout())
        elif layout == "grid":
            self.setLayout(QGridLayout())
        elif layout == "form":
            self.setLayout(QFormLayout())

        # Add classes if provided
        if classes is not None:
            add_classes(self, classes)

    cls.__init__ = __init__
    return cls


@overload
def widget_class(
    cls: T,
    *,
    name: str | None = ...,
    layout: WidgetLayoutType | None = ...,
    classes: list[str] | None = ...,
) -> T: ...
@overload
def widget_class(
    *,
    name: str | None = ...,
    layout: WidgetLayoutType | None = ...,
    classes: list[str] | None = ...,
) -> Callable[[T], T]: ...
@overload
def widget_class() -> Callable[[T], T]: ...


def widget_class(
    cls: T | None = None,
    *,
    name: str | None = None,
    layout: WidgetLayoutType | None = "vertical",
    classes: list[str] | None = None,
) -> T | Callable[[T], T]:
    def decorator(cls: T) -> T:
        return _widget_impl(cls, name=name, layout=layout, classes=classes)

    return decorator if cls is None else decorator(cls)


@overload
def widget(
    cls: T,
    *,
    name: str | None = ...,
    layout: WidgetLayoutType | None = ...,
    classes: list[str] | None = ...,
) -> T: ...
@overload
def widget(
    *,
    name: str | None = ...,
    layout: WidgetLayoutType | None = ...,
    classes: list[str] | None = ...,
) -> Callable[[T], T]: ...
@overload
def widget() -> Callable[[T], T]: ...


@dataclass_transform()
def widget(
    cls: T | None = None,
    *,
    name: str | None = None,
    layout: WidgetLayoutType | None = "vertical",
    classes: list[str] | None = None,
) -> T | Callable[[T], T]:
    """Decorator that makes a class a dataclass with Qt widget capabilities."""

    def decorator(cls: T) -> T:
        if not issubclass(cls, QWidget):
            raise TypeError(f"@widget can only be applied to QWidget subclasses, got {cls.__name__}")

        dataclass_cls = cast(T, dataclass(cls))
        return _widget_impl(dataclass_cls, name=name, layout=layout, classes=classes)

    return decorator if cls is None else decorator(cls)
